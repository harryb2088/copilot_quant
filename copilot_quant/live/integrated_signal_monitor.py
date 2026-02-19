"""
Example integration of SignalExecutionPipeline with LiveSignalMonitor

This module demonstrates how to connect the LiveSignalMonitor output to the
SignalExecutionPipeline for comprehensive risk management and order execution.

This shows the recommended approach for production deployments.
"""

import asyncio
import logging
from typing import List, Optional
from datetime import datetime

from copilot_quant.backtest.signals import SignalBasedStrategy, TradingSignal
from copilot_quant.live import LiveSignalMonitor, SignalExecutionPipeline
from copilot_quant.live.portfolio_state_manager import PortfolioStateManager
from copilot_quant.brokers.order_execution_handler import OrderExecutionHandler
from copilot_quant.orchestrator.notifiers.base import Notifier
from src.risk import RiskManager, RiskSettings

logger = logging.getLogger(__name__)


class EnhancedLiveSignalMonitor(LiveSignalMonitor):
    """
    Enhanced LiveSignalMonitor with integrated SignalExecutionPipeline.
    
    This class extends LiveSignalMonitor to use the SignalExecutionPipeline
    for comprehensive risk management, position sizing, and order execution.
    
    Features over base LiveSignalMonitor:
    - Full RiskManager integration (drawdown caps, position limits, correlation)
    - OrderExecutionHandler for professional order management
    - PortfolioStateManager for persistent state tracking
    - Notification integration for all events
    - Structured logging for audit trails
    
    Example:
        >>> # Initialize components
        >>> risk_manager = RiskManager(RiskSettings.get_conservative_profile())
        >>> order_handler = OrderExecutionHandler()
        >>> portfolio_state = PortfolioStateManager(database_url="...")
        >>> 
        >>> # Create enhanced monitor
        >>> monitor = EnhancedLiveSignalMonitor(
        ...     risk_manager=risk_manager,
        ...     order_handler=order_handler,
        ...     portfolio_state=portfolio_state,
        ...     paper_trading=True
        ... )
        >>> 
        >>> # Use like regular LiveSignalMonitor
        >>> monitor.add_strategy(MyStrategy())
        >>> monitor.connect()
        >>> monitor.start(['AAPL', 'MSFT'])
    """
    
    def __init__(
        self,
        risk_manager: RiskManager,
        order_handler: OrderExecutionHandler,
        portfolio_state: PortfolioStateManager,
        notifier: Optional[Notifier] = None,
        max_position_pct: float = 0.025,
        max_portfolio_deployment: float = 0.80,
        **kwargs
    ):
        """
        Initialize enhanced live signal monitor with execution pipeline.
        
        Args:
            risk_manager: RiskManager for comprehensive risk checks
            order_handler: OrderExecutionHandler for order management
            portfolio_state: PortfolioStateManager for state tracking
            notifier: Optional notifier for alerts
            max_position_pct: Maximum position size as % of portfolio
            max_portfolio_deployment: Maximum portfolio deployment %
            **kwargs: Additional arguments passed to LiveSignalMonitor
        """
        # Initialize base monitor
        super().__init__(**kwargs)
        
        # Create execution pipeline
        self.pipeline = SignalExecutionPipeline(
            risk_manager=risk_manager,
            order_handler=order_handler,
            portfolio_state=portfolio_state,
            notifier=notifier,
            ib_connection=None,  # Will be set when connected
            max_position_pct=max_position_pct,
            max_portfolio_deployment=max_portfolio_deployment
        )
        
        logger.info(
            "EnhancedLiveSignalMonitor initialized with SignalExecutionPipeline"
        )
    
    def connect(self, timeout: int = 30, retry_count: int = 3) -> bool:
        """
        Establish connections and wire IB connection to pipeline.
        
        Args:
            timeout: Connection timeout in seconds
            retry_count: Number of retry attempts
            
        Returns:
            True if connections successful
        """
        # Connect base monitor
        if not super().connect(timeout, retry_count):
            return False
        
        # Wire IB connection to pipeline
        # Note: LiveBrokerAdapter has an internal ib_connection
        # We need to access it for the pipeline
        if hasattr(self.broker, 'ib') and self.broker.ib is not None:
            self.pipeline.ib_connection = self.broker.ib
            logger.info("IB connection wired to execution pipeline")
        else:
            logger.warning(
                "Could not wire IB connection to pipeline - "
                "order execution may not work properly"
            )
        
        return True
    
    def _process_signal(self, signal: TradingSignal, timestamp: datetime) -> None:
        """
        Process signal through SignalExecutionPipeline instead of basic logic.
        
        This overrides the base class method to use comprehensive
        risk management and execution pipeline.
        
        Args:
            signal: TradingSignal to process
            timestamp: Current timestamp
        """
        # Persist signal to database (even if not executed)
        self._persist_signal(signal, timestamp)
        
        # Add to history for dashboard
        self._add_to_history(signal, timestamp)
        
        # Process through pipeline (async)
        try:
            # Run async method in sync context
            result = asyncio.run(self.pipeline.process_signal(signal))
            
            # Update stats based on result
            if result.status.value == 'executed':
                self.stats['signals_executed'] += 1
                self.active_signals[signal.symbol] = signal
            elif result.status.value == 'rejected':
                self.stats['signals_rejected'] += 1
            elif result.status.value == 'failed':
                self.stats['errors'] += 1
            
        except Exception as e:
            logger.error(f"Error processing signal through pipeline: {e}", exc_info=True)
            self.stats['errors'] += 1
    
    def get_dashboard_summary(self) -> dict:
        """
        Get enhanced dashboard summary including pipeline stats.
        
        Returns:
            Dictionary with dashboard data
        """
        # Get base summary
        summary = super().get_dashboard_summary()
        
        # Add pipeline stats
        summary['pipeline_stats'] = self.pipeline.get_stats()
        
        return summary


# Example usage function
def create_production_signal_monitor(
    database_url: str = "sqlite:///live_trading.db",
    risk_profile: str = "conservative",
    paper_trading: bool = True,
    notifier: Optional[Notifier] = None
) -> EnhancedLiveSignalMonitor:
    """
    Create a production-ready signal monitor with full pipeline integration.
    
    This is a convenience function that sets up all required components
    with sensible defaults.
    
    Args:
        database_url: Database URL for persistence
        risk_profile: Risk profile ("conservative", "balanced", "aggressive")
        paper_trading: Whether to use paper trading
        notifier: Optional notifier for alerts
        
    Returns:
        Configured EnhancedLiveSignalMonitor ready to use
        
    Example:
        >>> monitor = create_production_signal_monitor(
        ...     risk_profile="balanced",
        ...     paper_trading=True
        ... )
        >>> monitor.add_strategy(MyStrategy())
        >>> monitor.connect()
        >>> monitor.start(['AAPL', 'MSFT'])
    """
    # Select risk settings based on profile
    if risk_profile == "conservative":
        risk_settings = RiskSettings.get_conservative_profile()
    elif risk_profile == "balanced":
        risk_settings = RiskSettings.get_balanced_profile()
    elif risk_profile == "aggressive":
        risk_settings = RiskSettings.get_aggressive_profile()
    else:
        raise ValueError(f"Unknown risk profile: {risk_profile}")
    
    # Create components
    risk_manager = RiskManager(risk_settings)
    order_handler = OrderExecutionHandler()
    portfolio_state = PortfolioStateManager(
        database_url=database_url,
        broker=None  # Will be set during connection
    )
    
    # Create enhanced monitor
    monitor = EnhancedLiveSignalMonitor(
        risk_manager=risk_manager,
        order_handler=order_handler,
        portfolio_state=portfolio_state,
        notifier=notifier,
        database_url=database_url,
        paper_trading=paper_trading,
        enable_risk_checks=False,  # Disable basic checks, use pipeline
        max_position_pct=risk_settings.max_position_size,
        max_portfolio_deployment=0.80
    )
    
    logger.info(
        f"Production signal monitor created with {risk_profile} risk profile"
    )
    
    return monitor
