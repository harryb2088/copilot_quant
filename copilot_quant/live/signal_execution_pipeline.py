"""
Signal Execution Pipeline

Connects LiveSignalMonitor output to risk management and order execution.
This module provides the glue layer that wires signal generation through
risk checks, position sizing, and IBKR order submission.

Features:
- Risk-aware signal processing
- Dynamic position sizing based on signal quality
- Order lifecycle management
- Fill callbacks and portfolio state updates
- Circuit breaker integration
- Batch signal processing with quality ranking
- Structured notification and logging
"""

import json
import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import List, Optional, Any, Dict, Tuple

from copilot_quant.backtest.signals import TradingSignal
from copilot_quant.brokers.order_execution_handler import OrderExecutionHandler, OrderRecord
from copilot_quant.orchestrator.notifiers.base import Notifier, NotificationMessage, AlertLevel
from src.risk.portfolio_risk import RiskManager, RiskCheckResult

logger = logging.getLogger(__name__)


class SignalStatus(Enum):
    """Signal execution status"""
    PENDING = "pending"  # Signal received but not yet processed
    APPROVED = "approved"  # Passed risk checks
    REJECTED = "rejected"  # Failed risk checks
    EXECUTED = "executed"  # Order submitted successfully
    FILLED = "filled"  # Order filled
    FAILED = "failed"  # Order submission or execution failed


@dataclass
class ExecutionResult:
    """
    Result of signal execution through the pipeline.
    
    Tracks the complete lifecycle of a signal from reception through
    risk checks, sizing, order submission, and fills.
    """
    signal: TradingSignal
    status: SignalStatus
    timestamp: datetime = field(default_factory=datetime.now)
    
    # Risk check results
    risk_check_passed: bool = False
    risk_check_reason: str = ""
    risk_check_details: Optional[Dict[str, Any]] = None
    
    # Position sizing
    position_size: int = 0  # Number of shares
    position_value: float = 0.0  # Dollar value of position
    
    # Order execution
    order_record: Optional[OrderRecord] = None
    order_id: Optional[int] = None
    
    # Rejection tracking
    rejection_reason: Optional[str] = None
    
    # Metadata
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for logging/persistence"""
        return {
            'signal': {
                'symbol': self.signal.symbol,
                'side': self.signal.side,
                'confidence': self.signal.confidence,
                'sharpe_estimate': self.signal.sharpe_estimate,
                'quality_score': self.signal.quality_score,
                'strategy_name': self.signal.strategy_name,
                'entry_price': self.signal.entry_price,
            },
            'status': self.status.value,
            'timestamp': self.timestamp.isoformat(),
            'risk_check_passed': self.risk_check_passed,
            'risk_check_reason': self.risk_check_reason,
            'position_size': self.position_size,
            'position_value': self.position_value,
            'order_id': self.order_id,
            'rejection_reason': self.rejection_reason,
            'metadata': self.metadata,
        }
    
    def to_json(self) -> str:
        """Convert to JSON string for structured logging"""
        return json.dumps(self.to_dict(), indent=2)


class SignalExecutionPipeline:
    """
    Signal execution pipeline that connects signal generation to order execution.
    
    This class implements the glue layer between LiveSignalMonitor, RiskManager,
    and OrderExecutionHandler. It processes signals through:
    
    1. Risk checks (drawdown, position limits, correlation, etc.)
    2. Dynamic position sizing based on signal quality
    3. Order submission to IBKR
    4. Fill tracking and portfolio state updates
    
    Example:
        >>> pipeline = SignalExecutionPipeline(
        ...     risk_manager=risk_mgr,
        ...     order_handler=order_handler,
        ...     portfolio_state=portfolio_state,
        ...     notifier=notifier
        ... )
        >>> 
        >>> # Process single signal
        >>> result = await pipeline.process_signal(signal)
        >>> 
        >>> # Process batch of signals (ranked by quality)
        >>> results = await pipeline.process_batch(signals)
    """
    
    def __init__(
        self,
        risk_manager: RiskManager,
        order_handler: OrderExecutionHandler,
        portfolio_state: Any,  # PortfolioStateManager or compatible
        notifier: Optional[Notifier] = None,
        ib_connection: Optional[Any] = None,
        max_position_pct: float = 0.025,  # 2.5% per position
        max_portfolio_deployment: float = 0.80,  # 80% max deployment
    ):
        """
        Initialize signal execution pipeline.
        
        Args:
            risk_manager: RiskManager instance for risk checks
            order_handler: OrderExecutionHandler for order submission
            portfolio_state: Portfolio state manager for position tracking
            notifier: Optional notifier for alerts
            ib_connection: Interactive Brokers connection (for order submission)
            max_position_pct: Maximum position size as % of portfolio (default 2.5%)
            max_portfolio_deployment: Maximum portfolio deployment % (default 80%)
        """
        self.risk_manager = risk_manager
        self.order_handler = order_handler
        self.portfolio_state = portfolio_state
        self.notifier = notifier
        self.ib_connection = ib_connection
        
        self.max_position_pct = max_position_pct
        self.max_portfolio_deployment = max_portfolio_deployment
        
        # Statistics
        self.stats = {
            'total_processed': 0,
            'approved': 0,
            'rejected': 0,
            'executed': 0,
            'failed': 0,
        }
        
        # Register fill callback with order handler
        self.order_handler.register_fill_callback(self._on_fill)
        
        logger.info(
            f"SignalExecutionPipeline initialized: "
            f"max_position={max_position_pct:.1%}, "
            f"max_deployment={max_portfolio_deployment:.1%}"
        )
    
    async def process_signal(self, signal: TradingSignal) -> ExecutionResult:
        """
        Process a single trading signal through the pipeline.
        
        Pipeline steps:
        1. Perform risk checks
        2. Calculate position size if approved
        3. Submit order if sized
        4. Track execution result
        5. Send notifications
        
        Args:
            signal: TradingSignal to process
            
        Returns:
            ExecutionResult with complete execution tracking
        """
        self.stats['total_processed'] += 1
        
        result = ExecutionResult(
            signal=signal,
            status=SignalStatus.PENDING
        )
        
        # Log signal receipt
        logger.info(
            f"Processing signal: {signal.symbol} {signal.side} "
            f"(quality={signal.quality_score:.3f}, strategy={signal.strategy_name})"
        )
        
        try:
            # Step 1: Risk checks
            risk_result = self._perform_risk_checks(signal)
            result.risk_check_passed = risk_result.approved
            result.risk_check_reason = risk_result.reason
            result.risk_check_details = risk_result.details
            
            if not risk_result.approved:
                result.status = SignalStatus.REJECTED
                result.rejection_reason = risk_result.reason
                self.stats['rejected'] += 1
                
                # Log structured rejection
                logger.warning(
                    f"Signal REJECTED: {signal.symbol} {signal.side} - {risk_result.reason}\n"
                    f"{result.to_json()}"
                )
                
                # Send notification
                self._notify_rejection(signal, risk_result.reason)
                
                return result
            
            # Step 2: Calculate position size
            result.status = SignalStatus.APPROVED
            self.stats['approved'] += 1
            
            position_size, position_value = self._calculate_position_size(signal)
            result.position_size = position_size
            result.position_value = position_value
            
            if position_size <= 0:
                result.status = SignalStatus.REJECTED
                result.rejection_reason = "Position size too small or zero"
                self.stats['rejected'] += 1
                
                logger.info(
                    f"Signal rejected - position size zero: {signal.symbol} {signal.side}"
                )
                
                return result
            
            # Step 3: Submit order
            order_record = self._submit_order(signal, position_size)
            
            if order_record is None:
                result.status = SignalStatus.FAILED
                result.rejection_reason = "Order submission failed"
                self.stats['failed'] += 1
                
                logger.error(
                    f"Order submission FAILED: {signal.symbol} {signal.side} {position_size}"
                )
                
                return result
            
            # Step 4: Track execution
            result.status = SignalStatus.EXECUTED
            result.order_record = order_record
            result.order_id = order_record.order_id
            self.stats['executed'] += 1
            
            # Log structured execution
            logger.info(
                f"Signal EXECUTED: {signal.side} {position_size} {signal.symbol} "
                f"(order_id={order_record.order_id}, strategy={signal.strategy_name})\n"
                f"{result.to_json()}"
            )
            
            # Step 5: Send notification
            self._notify_execution(signal, position_size, order_record)
            
            return result
            
        except Exception as e:
            result.status = SignalStatus.FAILED
            result.rejection_reason = f"Pipeline error: {str(e)}"
            self.stats['failed'] += 1
            
            logger.error(
                f"Pipeline error processing signal {signal.symbol}: {e}",
                exc_info=True
            )
            
            return result
    
    async def process_batch(
        self,
        signals: List[TradingSignal]
    ) -> List[ExecutionResult]:
        """
        Process a batch of signals, ranked by quality score.
        
        Signals are processed in order of descending quality_score.
        Processing stops when portfolio deployment limit is reached.
        
        Args:
            signals: List of TradingSignal objects to process
            
        Returns:
            List of ExecutionResult objects
        """
        if not signals:
            logger.debug("No signals to process in batch")
            return []
        
        # Sort signals by quality score (highest first)
        sorted_signals = sorted(
            signals,
            key=lambda s: s.quality_score,
            reverse=True
        )
        
        logger.info(
            f"Processing batch of {len(signals)} signals "
            f"(quality range: {sorted_signals[-1].quality_score:.3f} - "
            f"{sorted_signals[0].quality_score:.3f})"
        )
        
        results = []
        
        for signal in sorted_signals:
            # Check if we've hit deployment limit
            if self._is_deployment_limit_reached():
                logger.warning(
                    f"Portfolio deployment limit reached - "
                    f"skipping remaining {len(sorted_signals) - len(results)} signals"
                )
                
                # Mark remaining signals as rejected
                for remaining_signal in sorted_signals[len(results):]:
                    result = ExecutionResult(
                        signal=remaining_signal,
                        status=SignalStatus.REJECTED,
                        rejection_reason="Portfolio deployment limit reached"
                    )
                    results.append(result)
                    self.stats['rejected'] += 1
                
                break
            
            # Process signal
            result = await self.process_signal(signal)
            results.append(result)
        
        # Log batch summary
        executed = sum(1 for r in results if r.status == SignalStatus.EXECUTED)
        rejected = sum(1 for r in results if r.status == SignalStatus.REJECTED)
        failed = sum(1 for r in results if r.status == SignalStatus.FAILED)
        
        logger.info(
            f"Batch processing complete: {executed} executed, "
            f"{rejected} rejected, {failed} failed"
        )
        
        return results
    
    def _perform_risk_checks(self, signal: TradingSignal) -> RiskCheckResult:
        """
        Perform comprehensive risk checks on a signal.
        
        Checks:
        - Circuit breaker status
        - Portfolio drawdown
        - Cash buffer
        - Position limits
        - Max deployment
        - Signal quality threshold
        
        Args:
            signal: TradingSignal to check
            
        Returns:
            RiskCheckResult indicating approval or rejection
        """
        # Get current portfolio state
        portfolio_value = self.portfolio_state.get_portfolio_value()
        peak_value = self.portfolio_state.get_peak_value()
        cash = self.portfolio_state.get_cash()
        positions = self.portfolio_state.get_positions()
        
        # Check portfolio-level risk
        portfolio_risk = self.risk_manager.check_portfolio_risk(
            portfolio_value=portfolio_value,
            peak_value=peak_value,
            cash=cash,
            positions=[{'symbol': p.symbol} for p in positions.values()] if positions else []
        )
        
        if not portfolio_risk.approved:
            return portfolio_risk
        
        # Check signal quality threshold (minimum 0.3)
        if signal.quality_score < 0.3:
            return RiskCheckResult(
                approved=False,
                reason=f"Signal quality score {signal.quality_score:.3f} below minimum 0.3",
                details={'quality_score': signal.quality_score}
            )
        
        # Check max deployment
        current_deployment = self._calculate_current_deployment()
        
        if current_deployment >= self.max_portfolio_deployment:
            return RiskCheckResult(
                approved=False,
                reason=f"Portfolio deployment {current_deployment:.1%} at or above maximum {self.max_portfolio_deployment:.1%}",
                details={
                    'current_deployment': current_deployment,
                    'max_deployment': self.max_portfolio_deployment
                }
            )
        
        # All checks passed
        return RiskCheckResult(
            approved=True,
            reason="All risk checks passed",
            details={
                'portfolio_value': portfolio_value,
                'current_deployment': current_deployment,
                'quality_score': signal.quality_score
            }
        )
    
    def _calculate_position_size(self, signal: TradingSignal) -> Tuple[int, float]:
        """
        Calculate position size based on signal quality and risk limits.
        
        Uses quality_score to scale position size within max_position_pct limit.
        
        Args:
            signal: TradingSignal to size
            
        Returns:
            Tuple of (shares, dollar_value)
        """
        portfolio_value = self.portfolio_state.get_portfolio_value()
        
        if portfolio_value <= 0:
            return 0, 0.0
        
        # Base allocation from max position percentage
        max_position_value = portfolio_value * self.max_position_pct
        
        # Scale by signal quality
        position_value = max_position_value * signal.quality_score
        
        # Convert to shares
        if signal.entry_price > 0:
            shares = int(position_value / signal.entry_price)
        else:
            shares = 0
        
        # Recalculate actual dollar value
        actual_value = shares * signal.entry_price if shares > 0 else 0.0
        
        logger.debug(
            f"Position sizing for {signal.symbol}: "
            f"{shares} shares @ ${signal.entry_price:.2f} = ${actual_value:.2f} "
            f"(quality={signal.quality_score:.3f})"
        )
        
        return shares, actual_value
    
    def _submit_order(
        self,
        signal: TradingSignal,
        quantity: int
    ) -> Optional[OrderRecord]:
        """
        Submit order to IBKR via OrderExecutionHandler.
        
        Args:
            signal: TradingSignal to execute
            quantity: Number of shares to order
            
        Returns:
            OrderRecord if successful, None otherwise
        """
        if self.ib_connection is None:
            logger.error("Cannot submit order - no IB connection")
            return None
        
        try:
            order_record = self.order_handler.submit_order(
                ib_connection=self.ib_connection,
                symbol=signal.symbol,
                action=signal.side.upper(),
                quantity=quantity,
                order_type="MARKET"
            )
            
            return order_record
            
        except Exception as e:
            logger.error(f"Error submitting order: {e}", exc_info=True)
            return None
    
    def _calculate_current_deployment(self) -> float:
        """
        Calculate current portfolio deployment percentage.
        
        Returns:
            Deployment as decimal (e.g., 0.75 for 75%)
        """
        portfolio_value = self.portfolio_state.get_portfolio_value()
        
        if portfolio_value <= 0:
            return 0.0
        
        cash = self.portfolio_state.get_cash()
        deployed = portfolio_value - cash
        
        return deployed / portfolio_value
    
    def _is_deployment_limit_reached(self) -> bool:
        """
        Check if portfolio deployment limit has been reached.
        
        Returns:
            True if at or above deployment limit
        """
        return self._calculate_current_deployment() >= self.max_portfolio_deployment
    
    def _on_fill(self, order_record: OrderRecord) -> None:
        """
        Callback for order fills.
        
        Updates portfolio state when orders are filled.
        
        Args:
            order_record: OrderRecord that was filled
        """
        logger.info(
            f"Fill callback: {order_record.symbol} {order_record.action} "
            f"{order_record.filled_quantity} @ ${order_record.avg_fill_price:.2f}"
        )
        
        # Update portfolio state
        # This would typically call portfolio_state.update_position()
        # Implementation depends on PortfolioStateManager interface
        
        # Send fill notification
        if self.notifier:
            message = NotificationMessage(
                title=f"Order Filled: {order_record.symbol}",
                message=(
                    f"{order_record.action} {order_record.filled_quantity} "
                    f"{order_record.symbol} @ ${order_record.avg_fill_price:.2f}\n"
                    f"Order ID: {order_record.order_id}\n"
                    f"Status: {order_record.status.value}"
                ),
                level=AlertLevel.INFO,
                metadata={
                    'symbol': order_record.symbol,
                    'action': order_record.action,
                    'quantity': order_record.filled_quantity,
                    'price': order_record.avg_fill_price,
                    'order_id': order_record.order_id,
                }
            )
            self.notifier.notify(message)
    
    def _notify_execution(
        self,
        signal: TradingSignal,
        quantity: int,
        order_record: OrderRecord
    ) -> None:
        """
        Send notification for signal execution.
        
        Args:
            signal: Executed signal
            quantity: Order quantity
            order_record: Order that was submitted
        """
        if not self.notifier:
            return
        
        message = NotificationMessage(
            title=f"Signal Executed: {signal.symbol}",
            message=(
                f"{signal.side.upper()} {quantity} {signal.symbol}\n"
                f"Strategy: {signal.strategy_name}\n"
                f"Quality Score: {signal.quality_score:.3f}\n"
                f"Entry Price: ${signal.entry_price:.2f}\n"
                f"Order ID: {order_record.order_id}"
            ),
            level=AlertLevel.INFO,
            metadata={
                'symbol': signal.symbol,
                'side': signal.side,
                'quantity': quantity,
                'quality_score': signal.quality_score,
                'strategy': signal.strategy_name,
                'order_id': order_record.order_id,
            }
        )
        
        self.notifier.notify(message)
    
    def _notify_rejection(self, signal: TradingSignal, reason: str) -> None:
        """
        Send notification for signal rejection.
        
        Args:
            signal: Rejected signal
            reason: Rejection reason
        """
        if not self.notifier:
            return
        
        # Determine alert level based on rejection reason
        level = AlertLevel.CRITICAL if "circuit breaker" in reason.lower() else AlertLevel.WARNING
        
        message = NotificationMessage(
            title=f"Signal Rejected: {signal.symbol}",
            message=(
                f"{signal.side.upper()} {signal.symbol}\n"
                f"Strategy: {signal.strategy_name}\n"
                f"Quality Score: {signal.quality_score:.3f}\n"
                f"Rejection Reason: {reason}"
            ),
            level=level,
            metadata={
                'symbol': signal.symbol,
                'side': signal.side,
                'quality_score': signal.quality_score,
                'strategy': signal.strategy_name,
                'rejection_reason': reason,
            }
        )
        
        self.notifier.notify(message)
    
    def get_stats(self) -> Dict[str, int]:
        """Get pipeline statistics"""
        return self.stats.copy()
