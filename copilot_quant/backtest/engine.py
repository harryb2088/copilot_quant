"""
Core backtesting engine.

This module provides the main BacktestEngine class for running strategy backtests
against historical market data.
"""

import logging
import uuid
from collections import defaultdict
from datetime import datetime
from typing import Dict, List, Optional

import pandas as pd

from copilot_quant.backtest.orders import Fill, Order, Position
from copilot_quant.backtest.results import BacktestResult
from copilot_quant.backtest.strategy import Strategy
from copilot_quant.data.providers import DataProvider

logger = logging.getLogger(__name__)


class BacktestEngine:
    """
    Event-driven backtesting engine.
    
    The engine simulates trading by replaying historical data and executing
    strategy logic at each time step. It tracks positions, portfolio value,
    and applies transaction costs.
    
    Example:
        >>> from copilot_quant.data.providers import YFinanceProvider
        >>> 
        >>> engine = BacktestEngine(
        ...     initial_capital=100000,
        ...     data_provider=YFinanceProvider(),
        ...     commission=0.001,
        ...     slippage=0.0005
        ... )
        >>> engine.add_strategy(MyStrategy())
        >>> result = engine.run(
        ...     start_date=datetime(2020, 1, 1),
        ...     end_date=datetime(2023, 12, 31),
        ...     symbols=['SPY']
        ... )
    """
    
    def __init__(
        self,
        initial_capital: float,
        data_provider: DataProvider,
        commission: float = 0.001,
        slippage: float = 0.0005
    ):
        """
        Initialize backtesting engine.
        
        Args:
            initial_capital: Starting capital in dollars
            data_provider: Data provider instance for historical data
            commission: Commission as a percentage (e.g., 0.001 = 0.1%)
            slippage: Slippage as a percentage (e.g., 0.0005 = 0.05%)
        """
        self.initial_capital = initial_capital
        self.data_provider = data_provider
        self.commission_rate = commission
        self.slippage_rate = slippage
        
        # Engine state
        self.strategy: Optional[Strategy] = None
        self.cash: float = initial_capital
        self.positions: Dict[str, Position] = {}
        self.fills: List[Fill] = []
        self.portfolio_history: List[dict] = []
        
        logger.info(
            f"Initialized BacktestEngine with ${initial_capital:,.2f} capital, "
            f"commission={commission:.4f}, slippage={slippage:.4f}"
        )
    
    def add_strategy(self, strategy: Strategy) -> None:
        """
        Register a trading strategy.
        
        Args:
            strategy: Strategy instance to backtest
        """
        self.strategy = strategy
        logger.info(f"Added strategy: {strategy.name}")
    
    def run(
        self,
        start_date: datetime,
        end_date: datetime,
        symbols: List[str]
    ) -> BacktestResult:
        """
        Execute backtest over date range.
        
        Args:
            start_date: Start date for backtest
            end_date: End date for backtest
            symbols: List of symbols to trade
        
        Returns:
            BacktestResult with performance metrics and trade history
        
        Raises:
            ValueError: If no strategy is registered
        """
        if self.strategy is None:
            raise ValueError("No strategy registered. Call add_strategy() first.")
        
        logger.info(
            f"Starting backtest: {start_date.date()} to {end_date.date()}, "
            f"symbols={symbols}"
        )
        
        # Reset engine state
        self._reset_state()
        
        # Initialize strategy
        self.strategy.initialize()
        
        # Download historical data
        data = self._fetch_data(symbols, start_date, end_date)
        
        if data.empty:
            logger.warning("No data available for backtest")
            return self._create_empty_result(start_date, end_date)
        
        # Run backtest loop
        self._run_backtest_loop(data, symbols)
        
        # Finalize strategy
        self.strategy.finalize()
        
        # Calculate final portfolio value
        final_value = self.get_portfolio_value()
        total_return = (final_value - self.initial_capital) / self.initial_capital
        
        logger.info(
            f"Backtest complete: Final value=${final_value:,.2f}, "
            f"Return={total_return:.2%}, Trades={len(self.fills)}"
        )
        
        # Create result object
        result = BacktestResult(
            strategy_name=self.strategy.name,
            start_date=start_date,
            end_date=end_date,
            initial_capital=self.initial_capital,
            final_capital=final_value,
            total_return=total_return,
            trades=self.fills.copy(),
            portfolio_history=pd.DataFrame(self.portfolio_history),
        )
        
        return result
    
    def get_portfolio_value(self) -> float:
        """
        Get current total portfolio value (cash + positions).
        
        Returns:
            Total portfolio value in dollars
        """
        positions_value = sum(pos.market_value for pos in self.positions.values())
        return self.cash + positions_value
    
    def get_positions(self) -> Dict[str, Position]:
        """
        Get current positions.
        
        Returns:
            Dictionary mapping symbols to Position objects
        """
        return self.positions.copy()
    
    def _reset_state(self) -> None:
        """Reset engine state for new backtest."""
        self.cash = self.initial_capital
        self.positions = {}
        self.fills = []
        self.portfolio_history = []
    
    def _fetch_data(
        self,
        symbols: List[str],
        start_date: datetime,
        end_date: datetime
    ) -> pd.DataFrame:
        """Fetch historical data for symbols."""
        try:
            if len(symbols) == 1:
                # Single symbol - simpler data structure
                data = self.data_provider.get_historical_data(
                    symbols[0],
                    start_date=start_date,
                    end_date=end_date
                )
                # Add symbol column for consistency
                if not data.empty:
                    data['Symbol'] = symbols[0]
            else:
                # Multiple symbols
                data = self.data_provider.get_multiple_symbols(
                    symbols,
                    start_date=start_date,
                    end_date=end_date
                )
            
            return data
        except Exception as e:
            logger.error(f"Error fetching data: {e}")
            return pd.DataFrame()
    
    def _run_backtest_loop(self, data: pd.DataFrame, symbols: List[str]) -> None:
        """
        Main backtest loop - iterate through data chronologically.
        
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
            
            # Record portfolio value
            self._record_portfolio_state(timestamp)
            
            # Call strategy to get orders
            try:
                orders = self.strategy.on_data(timestamp, current_data)
                
                if orders is None:
                    orders = []
                
                # Execute orders
                for order in orders:
                    self._execute_order(order, timestamp, current_data)
                    
            except Exception as e:
                logger.error(f"Strategy error at {timestamp}: {e}")
                continue
    
    def _get_current_data(
        self,
        data: pd.DataFrame,
        timestamp: datetime,
        symbols: List[str]
    ) -> pd.DataFrame:
        """
        Get data available at current timestamp.
        
        Returns data up to and including current timestamp to avoid look-ahead bias.
        """
        # Return all data up to current timestamp
        available_data = data.loc[:timestamp]
        return available_data
    
    def _update_positions_pnl(self, current_data: pd.DataFrame) -> None:
        """Update unrealized PnL for all positions based on current prices."""
        if current_data.empty:
            return
        
        # Get latest prices for each symbol
        for symbol, position in self.positions.items():
            if position.quantity == 0:
                continue
            
            current_price = self._get_current_price(current_data, symbol)
            if current_price is not None:
                position.update_unrealized_pnl(current_price)
    
    def _get_current_price(self, data: pd.DataFrame, symbol: str) -> Optional[float]:
        """Get current close price for a symbol."""
        try:
            # Handle different data structures
            if 'Symbol' in data.columns:
                # Single symbol with Symbol column
                symbol_data = data[data['Symbol'] == symbol]
                if not symbol_data.empty:
                    return float(symbol_data.iloc[-1]['Close'])
            elif 'Close' in data.columns:
                # Single symbol without Symbol column
                if not data.empty:
                    return float(data.iloc[-1]['Close'])
            elif isinstance(data.columns, pd.MultiIndex):
                # Multi-symbol data with multi-level columns
                if ('Close', symbol) in data.columns:
                    prices = data[('Close', symbol)].dropna()
                    if not prices.empty:
                        return float(prices.iloc[-1])
            
            return None
        except (KeyError, IndexError, ValueError):
            return None
    
    def _execute_order(
        self,
        order: Order,
        timestamp: datetime,
        current_data: pd.DataFrame
    ) -> None:
        """
        Execute an order with simulated fills.
        
        Args:
            order: Order to execute
            timestamp: Current timestamp
            current_data: Current market data
        """
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
        
        # Notify strategy
        self.strategy.on_fill(fill)
        
        logger.debug(
            f"Executed: {order.side} {order.quantity} {order.symbol} @ ${fill_price:.2f}"
        )
    
    def _calculate_fill_price(self, order: Order, current_price: float) -> float:
        """
        Calculate fill price with slippage.
        
        Args:
            order: Order being filled
            current_price: Current market price
        
        Returns:
            Fill price including slippage
        """
        if order.order_type == 'market':
            # Apply slippage to market orders
            if order.side == 'buy':
                # Pay slippage on buys
                return current_price * (1 + self.slippage_rate)
            else:
                # Receive less on sells
                return current_price * (1 - self.slippage_rate)
        
        elif order.order_type == 'limit':
            # Limit orders fill at limit price if market price is favorable
            if order.side == 'buy':
                # Buy limit fills if market <= limit
                if current_price <= order.limit_price:
                    return order.limit_price
                else:
                    # Don't fill
                    return None
            else:
                # Sell limit fills if market >= limit
                if current_price >= order.limit_price:
                    return order.limit_price
                else:
                    # Don't fill
                    return None
        
        return current_price
    
    def _process_fill(self, fill: Fill, current_price: float) -> None:
        """
        Process a fill by updating cash and positions.
        
        Args:
            fill: Fill to process
            current_price: Current market price for PnL calculation
        """
        symbol = fill.order.symbol
        
        # Update cash
        self.cash += fill.net_proceeds
        
        # Update or create position
        if symbol not in self.positions:
            self.positions[symbol] = Position(symbol=symbol)
        
        self.positions[symbol].update_from_fill(fill, current_price)
        
        # Remove position if flat
        if self.positions[symbol].quantity == 0:
            del self.positions[symbol]
    
    def _record_portfolio_state(self, timestamp: datetime) -> None:
        """Record current portfolio state for history."""
        portfolio_value = self.get_portfolio_value()
        
        state = {
            'timestamp': timestamp,
            'portfolio_value': portfolio_value,
            'cash': self.cash,
            'positions_value': portfolio_value - self.cash,
            'num_positions': len(self.positions),
        }
        
        # Add individual position values
        for symbol, position in self.positions.items():
            state[f'position_{symbol}'] = position.quantity
            state[f'value_{symbol}'] = position.market_value
        
        self.portfolio_history.append(state)
    
    def _create_empty_result(
        self,
        start_date: datetime,
        end_date: datetime
    ) -> BacktestResult:
        """Create an empty result when no data is available."""
        return BacktestResult(
            strategy_name=self.strategy.name if self.strategy else "Unknown",
            start_date=start_date,
            end_date=end_date,
            initial_capital=self.initial_capital,
            final_capital=self.initial_capital,
            total_return=0.0,
            trades=[],
            portfolio_history=pd.DataFrame(),
        )
