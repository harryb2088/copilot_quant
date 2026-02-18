"""
Multi-strategy backtesting engine with signal-based allocation.

This module provides the MultiStrategyEngine for running multiple strategies
simultaneously with dynamic capital allocation based on signal quality.
"""

import logging
import uuid
from datetime import datetime
from typing import Dict, List

import pandas as pd

from copilot_quant.backtest.engine import BacktestEngine
from copilot_quant.backtest.orders import Fill, Order
from copilot_quant.backtest.results import BacktestResult
from copilot_quant.backtest.signals import SignalBasedStrategy, TradingSignal
from copilot_quant.data.providers import DataProvider

logger = logging.getLogger(__name__)


class StrategyAttribution:
    """
    Tracks performance attribution for a single strategy.
    
    Attributes:
        strategy_name: Name of the strategy
        total_deployed: Total capital deployed by this strategy
        realized_pnl: Realized profit/loss
        unrealized_pnl: Unrealized profit/loss
        num_trades: Number of trades executed
        num_wins: Number of winning trades
        num_losses: Number of losing trades
    """
    
    def __init__(self, strategy_name: str):
        """Initialize attribution tracker."""
        self.strategy_name = strategy_name
        self.total_deployed = 0.0
        self.realized_pnl = 0.0
        self.unrealized_pnl = 0.0
        self.num_trades = 0
        self.num_wins = 0
        self.num_losses = 0
        self.fills: List[Fill] = []
    
    def record_fill(self, fill: Fill) -> None:
        """Record a fill for this strategy."""
        self.fills.append(fill)
        self.num_trades += 1
        
        # Track deployed capital (for buys)
        if fill.order.side == 'buy':
            self.total_deployed += fill.fill_price * fill.fill_quantity
    
    def record_trade_close(self, pnl: float) -> None:
        """Record a closed trade's P&L."""
        self.realized_pnl += pnl
        
        if pnl > 0:
            self.num_wins += 1
        elif pnl < 0:
            self.num_losses += 1
    
    def update_unrealized_pnl(self, pnl: float) -> None:
        """Update unrealized P&L."""
        self.unrealized_pnl = pnl
    
    @property
    def total_pnl(self) -> float:
        """Total profit/loss (realized + unrealized)."""
        return self.realized_pnl + self.unrealized_pnl
    
    @property
    def win_rate(self) -> float:
        """Win rate as a percentage."""
        total_closed = self.num_wins + self.num_losses
        if total_closed == 0:
            return 0.0
        return self.num_wins / total_closed
    
    @property
    def deployed_capital_return(self) -> float:
        """Return on deployed capital."""
        if self.total_deployed == 0:
            return 0.0
        return self.total_pnl / self.total_deployed
    
    def to_dict(self) -> dict:
        """Convert attribution to dictionary."""
        return {
            'strategy_name': self.strategy_name,
            'total_deployed': self.total_deployed,
            'realized_pnl': self.realized_pnl,
            'unrealized_pnl': self.unrealized_pnl,
            'total_pnl': self.total_pnl,
            'num_trades': self.num_trades,
            'num_wins': self.num_wins,
            'num_losses': self.num_losses,
            'win_rate': self.win_rate,
            'deployed_capital_return': self.deployed_capital_return,
        }


class MultiStrategyEngine(BacktestEngine):
    """
    Event-driven backtesting engine supporting multiple signal-based strategies.
    
    Unlike traditional pod-based allocation, this engine allows all strategies
    to compete for capital based on signal quality. Capital flows dynamically
    to the best signals while respecting global risk limits.
    
    Key features:
    - No pre-allocated capital pods
    - Dynamic position sizing based on signal quality
    - Global risk limits (max position size, max deployment)
    - Per-strategy performance attribution
    
    Example:
        >>> from copilot_quant.data.providers import YFinanceProvider
        >>> 
        >>> engine = MultiStrategyEngine(
        ...     initial_capital=100000,
        ...     data_provider=YFinanceProvider(),
        ...     max_position_pct=0.025,  # 2.5% max per position
        ...     max_deployed_pct=0.80     # 80% max deployed
        ... )
        >>> engine.add_strategy(MeanReversionStrategy())
        >>> engine.add_strategy(PairsTradingStrategy())
        >>> result = engine.run(
        ...     start_date=datetime(2020, 1, 1),
        ...     end_date=datetime(2023, 12, 31),
        ...     symbols=['SPY', 'AAPL', 'MSFT']
        ... )
    """
    
    def __init__(
        self,
        initial_capital: float,
        data_provider: DataProvider,
        commission: float = 0.001,
        slippage: float = 0.0005,
        max_position_pct: float = 0.025,  # 2.5% max per position
        max_deployed_pct: float = 0.80,   # 80% max deployed
    ):
        """
        Initialize multi-strategy backtesting engine.
        
        Args:
            initial_capital: Starting capital in dollars
            data_provider: Data provider instance for historical data
            commission: Commission as a percentage (e.g., 0.001 = 0.1%)
            slippage: Slippage as a percentage (e.g., 0.0005 = 0.05%)
            max_position_pct: Maximum position size as percentage of cash (e.g., 0.025 = 2.5%)
            max_deployed_pct: Maximum deployed capital as percentage of total (e.g., 0.80 = 80%)
        """
        super().__init__(initial_capital, data_provider, commission, slippage)
        
        # Override strategy to support multiple strategies
        self.strategies: List[SignalBasedStrategy] = []
        self.strategy = None  # Not used in multi-strategy mode
        
        # Risk limits
        self.max_position_pct = max_position_pct
        self.max_deployed_pct = max_deployed_pct
        
        # Strategy attribution tracking
        self.attributions: Dict[str, StrategyAttribution] = {}
        
        # Track which strategy owns which position
        self.position_owners: Dict[str, str] = {}  # symbol -> strategy_name
        
        logger.info(
            f"Initialized MultiStrategyEngine with ${initial_capital:,.2f} capital, "
            f"max_position={max_position_pct:.1%}, max_deployed={max_deployed_pct:.1%}"
        )
    
    def add_strategy(self, strategy: SignalBasedStrategy) -> None:
        """
        Register a signal-based trading strategy.
        
        Args:
            strategy: SignalBasedStrategy instance to add
        
        Raises:
            TypeError: If strategy is not a SignalBasedStrategy
        """
        if not isinstance(strategy, SignalBasedStrategy):
            raise TypeError(
                f"MultiStrategyEngine requires SignalBasedStrategy, got {type(strategy)}"
            )
        
        self.strategies.append(strategy)
        self.attributions[strategy.name] = StrategyAttribution(strategy.name)
        logger.info(f"Added strategy: {strategy.name}")
    
    def run(
        self,
        start_date: datetime,
        end_date: datetime,
        symbols: List[str]
    ) -> BacktestResult:
        """
        Execute backtest over date range with multiple strategies.
        
        Args:
            start_date: Start date for backtest
            end_date: End date for backtest
            symbols: List of symbols to trade
        
        Returns:
            BacktestResult with performance metrics and trade history
        
        Raises:
            ValueError: If no strategies are registered
        """
        if not self.strategies:
            raise ValueError("No strategies registered. Call add_strategy() first.")
        
        logger.info(
            f"Starting multi-strategy backtest: {start_date.date()} to {end_date.date()}, "
            f"symbols={symbols}, strategies={len(self.strategies)}"
        )
        
        # Reset engine state
        self._reset_state()
        
        # Initialize all strategies
        for strategy in self.strategies:
            strategy.initialize()
        
        # Download historical data
        data = self._fetch_data(symbols, start_date, end_date)
        
        if data.empty:
            logger.warning("No data available for backtest")
            return self._create_empty_result(start_date, end_date)
        
        # Run backtest loop
        self._run_multi_strategy_loop(data, symbols)
        
        # Finalize all strategies
        for strategy in self.strategies:
            strategy.finalize()
        
        # Calculate final portfolio value
        final_value = self.get_portfolio_value()
        total_return = (final_value - self.initial_capital) / self.initial_capital
        
        logger.info(
            f"Backtest complete: Final value=${final_value:,.2f}, "
            f"Return={total_return:.2%}, Total trades={len(self.fills)}"
        )
        
        # Log strategy attributions
        for attribution in self.attributions.values():
            logger.info(
                f"  {attribution.strategy_name}: {attribution.num_trades} trades, "
                f"P&L=${attribution.total_pnl:,.2f}, Win rate={attribution.win_rate:.1%}"
            )
        
        # Create result object
        result = BacktestResult(
            strategy_name="MultiStrategy",
            start_date=start_date,
            end_date=end_date,
            initial_capital=self.initial_capital,
            final_capital=final_value,
            total_return=total_return,
            trades=self.fills.copy(),
            portfolio_history=pd.DataFrame(self.portfolio_history),
        )
        
        # Add attribution data to result
        result.strategy_attributions = {
            name: attr.to_dict() for name, attr in self.attributions.items()
        }
        
        return result
    
    def _reset_state(self) -> None:
        """Reset engine state for new backtest."""
        super()._reset_state()
        self.attributions = {s.name: StrategyAttribution(s.name) for s in self.strategies}
        self.position_owners = {}
    
    def _run_multi_strategy_loop(self, data: pd.DataFrame, symbols: List[str]) -> None:
        """
        Main backtest loop for multiple strategies.
        
        At each time step:
        1. Collect signals from all strategies
        2. Rank signals by quality
        3. Execute signals until risk limits are hit
        
        Args:
            data: Historical market data
            symbols: List of symbols being traded
        """
        # Get sorted timestamps
        timestamps = sorted(data.index.unique())
        
        for timestamp in timestamps:
            # Get data for current timestamp
            current_data = self._get_current_data(data, timestamp, symbols)
            
            # Update unrealized PnL for all positions
            self._update_positions_pnl(current_data)
            
            # Update strategy attribution unrealized P&L
            self._update_attribution_unrealized_pnl()
            
            # Record portfolio value
            self._record_portfolio_state(timestamp)
            
            # Collect signals from all strategies
            all_signals = self._collect_signals(timestamp, current_data)
            
            # Rank signals by quality and execute
            self._execute_ranked_signals(all_signals, timestamp, current_data)
    
    def _collect_signals(
        self,
        timestamp: datetime,
        data: pd.DataFrame
    ) -> List[TradingSignal]:
        """
        Collect signals from all strategies.
        
        Args:
            timestamp: Current timestamp
            data: Market data available at this timestamp
        
        Returns:
            List of all signals generated by all strategies
        """
        all_signals = []
        
        for strategy in self.strategies:
            try:
                signals = strategy.generate_signals(timestamp, data)
                
                if signals is None:
                    signals = []
                
                # Ensure all signals have strategy name set
                for signal in signals:
                    if not signal.strategy_name:
                        signal.strategy_name = strategy.name
                
                all_signals.extend(signals)
                
            except Exception as e:
                logger.error(f"Error in strategy {strategy.name} at {timestamp}: {e}")
                continue
        
        return all_signals
    
    def _execute_ranked_signals(
        self,
        signals: List[TradingSignal],
        timestamp: datetime,
        current_data: pd.DataFrame
    ) -> None:
        """
        Rank signals by quality and execute until risk limits are hit.
        
        Args:
            signals: List of signals to execute
            timestamp: Current timestamp
            current_data: Current market data
        """
        if not signals:
            return
        
        # Sort signals by quality score (highest first)
        ranked_signals = sorted(signals, key=lambda s: s.quality_score, reverse=True)
        
        # Execute signals in order until risk limits prevent further execution
        for signal in ranked_signals:
            # Check if we can execute this signal
            if not self._can_execute_signal(signal):
                continue
            
            # Calculate position size based on signal quality
            position_size = self._calculate_signal_position_size(signal)
            
            if position_size <= 0:
                continue
            
            # Create order from signal
            order = self._signal_to_order(signal, position_size)
            
            # Execute order
            self._execute_order(order, timestamp, current_data)
    
    def _can_execute_signal(self, signal: TradingSignal) -> bool:
        """
        Check if signal can be executed given current risk limits.
        
        Args:
            signal: Signal to check
        
        Returns:
            True if signal can be executed, False otherwise
        """
        portfolio_value = self.get_portfolio_value()
        
        # Check max deployed capital limit
        deployed_value = sum(pos.market_value for pos in self.positions.values())
        deployed_pct = deployed_value / portfolio_value if portfolio_value > 0 else 0
        
        if signal.side == 'buy' and deployed_pct >= self.max_deployed_pct:
            logger.debug(
                f"Cannot execute signal: deployed capital ({deployed_pct:.1%}) "
                f"at maximum ({self.max_deployed_pct:.1%})"
            )
            return False
        
        return True
    
    def _calculate_signal_position_size(self, signal: TradingSignal) -> float:
        """
        Calculate position size for a signal based on quality and risk limits.
        
        Args:
            signal: Signal to size
        
        Returns:
            Position size in dollars
        """
        # Base position size from signal quality and max position limit
        # Use cash instead of portfolio value for position sizing
        max_position_value = self.cash * self.max_position_pct
        
        # Scale by signal quality
        position_value = max_position_value * signal.quality_score
        
        # Ensure we have enough cash
        position_value = min(position_value, self.cash * 0.99)  # Leave some buffer
        
        return position_value
    
    def _signal_to_order(self, signal: TradingSignal, position_value: float) -> Order:
        """
        Convert a signal to an order with calculated position size.
        
        Args:
            signal: Signal to convert
            position_value: Position value in dollars
        
        Returns:
            Order object
        """
        # Calculate quantity based on position value and entry price
        quantity = position_value / signal.entry_price
        
        # Create order
        order = Order(
            symbol=signal.symbol,
            quantity=quantity,
            order_type='market',
            side=signal.side,
        )
        
        # Track which strategy owns this position
        if signal.side == 'buy':
            self.position_owners[signal.symbol] = signal.strategy_name
        
        return order
    
    def _execute_order(
        self,
        order: Order,
        timestamp: datetime,
        current_data: pd.DataFrame
    ) -> None:
        """
        Execute an order and update strategy attribution.
        
        Args:
            order: Order to execute
            timestamp: Current timestamp
            current_data: Current market data
        """
        # Get the strategy that owns this order
        strategy_name = self.position_owners.get(order.symbol, "Unknown")
        
        # Execute the order using parent logic but without calling strategy.on_fill
        # Get current price for the symbol
        current_price = self._get_current_price(current_data, order.symbol)
        
        if current_price is None:
            logger.warning(f"Cannot execute order - no price data for {order.symbol}")
            return
        
        # Determine fill price based on order type
        fill_price = self._calculate_fill_price(order, current_price)
        
        # Check if limit order can be filled
        if fill_price is None:
            # Limit order not filled
            return
        
        # Check if we have sufficient capital for buy orders
        if order.side == 'buy':
            cost = fill_price * order.quantity
            commission = cost * self.commission_rate
            total_cost = cost + commission
            
            if total_cost > self.cash:
                logger.warning(
                    f"Insufficient capital for order: need ${total_cost:,.2f}, "
                    f"have ${self.cash:,.2f}"
                )
                return
        
        # Calculate commission
        commission = fill_price * order.quantity * self.commission_rate
        
        # Create fill
        fill = Fill(
            order=order,
            fill_price=fill_price,
            fill_quantity=order.quantity,
            commission=commission,
            timestamp=timestamp,
            fill_id=str(uuid.uuid4())
        )
        
        # Update cash and positions
        self._process_fill(fill, current_price)
        
        # Record fill
        self.fills.append(fill)
        
        # Record fill in attribution
        if strategy_name in self.attributions:
            self.attributions[strategy_name].record_fill(fill)
            
            # Notify the strategy
            for strategy in self.strategies:
                if strategy.name == strategy_name:
                    strategy.on_fill(fill)
                    break
        
        logger.debug(
            f"Executed: {order.side} {order.quantity} {order.symbol} @ ${fill_price:.2f}"
        )
    
    def _update_attribution_unrealized_pnl(self) -> None:
        """
        Update unrealized P&L for each strategy's attribution.
        
        Note: Currently simplified - unrealized P&L tracking per strategy
        would require maintaining a mapping of which positions belong to which
        strategy and tracking partial position updates. This is a potential
        future enhancement.
        """
        # For now, unrealized P&L is tracked at the portfolio level
        # Strategy attribution focuses on realized P&L from closed trades
        pass
    
    def _create_empty_result(
        self,
        start_date: datetime,
        end_date: datetime
    ) -> BacktestResult:
        """Create an empty result when no data is available."""
        result = BacktestResult(
            strategy_name="MultiStrategy",
            start_date=start_date,
            end_date=end_date,
            initial_capital=self.initial_capital,
            final_capital=self.initial_capital,
            total_return=0.0,
            trades=[],
            portfolio_history=pd.DataFrame(),
        )
        
        result.strategy_attributions = {
            name: attr.to_dict() for name, attr in self.attributions.items()
        }
        
        return result
