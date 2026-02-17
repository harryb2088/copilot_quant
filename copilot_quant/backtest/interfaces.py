"""
Core interface definitions for the backtesting engine.

This module provides abstract base classes and interfaces that define
the contracts for backtesting components. These interfaces promote
extensibility and allow for custom implementations.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, List, Optional, Protocol

import pandas as pd

from copilot_quant.backtest.orders import Fill, Order, Position


# =============================================================================
# Data Feed Interfaces
# =============================================================================


class IDataFeed(ABC):
    """
    Abstract interface for market data feeds.
    
    Implementations provide historical or real-time market data to the
    backtesting engine. This abstraction allows backtests to work with
    different data sources without modification.
    
    Examples:
        - YFinanceDataFeed: Yahoo Finance historical data
        - CSVDataFeed: Local CSV files
        - DatabaseDataFeed: SQL database
        - MockDataFeed: Synthetic data for testing
    """
    
    @abstractmethod
    def get_historical_data(
        self,
        symbol: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        interval: str = '1d'
    ) -> pd.DataFrame:
        """
        Retrieve historical OHLCV data for a single symbol.
        
        Args:
            symbol: Ticker symbol (e.g., 'AAPL', 'SPY')
            start_date: Start date for data (None = all available)
            end_date: End date for data (None = latest)
            interval: Data frequency ('1d', '1h', '1m', etc.)
        
        Returns:
            DataFrame with DatetimeIndex and columns:
                - Open: Opening price
                - High: High price
                - Low: Low price
                - Close: Closing price
                - Volume: Trading volume
                - (Optional) Dividends, Stock Splits
        
        Raises:
            ValueError: If symbol is invalid
            DataUnavailableError: If data cannot be retrieved
        """
        pass
    
    @abstractmethod
    def get_multiple_symbols(
        self,
        symbols: List[str],
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        interval: str = '1d'
    ) -> pd.DataFrame:
        """
        Retrieve historical data for multiple symbols efficiently.
        
        Args:
            symbols: List of ticker symbols
            start_date: Start date for data
            end_date: End date for data
            interval: Data frequency
        
        Returns:
            Multi-index DataFrame with (Date, Symbol) index or
            DataFrame with multi-level columns (Metric, Symbol)
        
        Note:
            Implementations should batch requests for efficiency.
        """
        pass
    
    @abstractmethod
    def get_ticker_info(self, symbol: str) -> Dict:
        """
        Get metadata about a security.
        
        Args:
            symbol: Ticker symbol
        
        Returns:
            Dictionary with metadata (name, sector, industry, etc.)
        """
        pass


# =============================================================================
# Broker/Execution Interfaces
# =============================================================================


class IBroker(ABC):
    """
    Abstract interface for order execution and brokerage operations.
    
    The broker simulates a real brokerage by:
    - Executing orders with realistic pricing
    - Applying transaction costs
    - Checking buying power
    - Managing positions
    
    This abstraction allows different execution models:
    - Simple broker: Market orders with fixed slippage
    - Realistic broker: Volume-based slippage, partial fills
    - Paper trading broker: Live market data
    """
    
    @abstractmethod
    def execute_order(
        self,
        order: Order,
        current_price: float,
        timestamp: datetime
    ) -> Optional[Fill]:
        """
        Execute an order if conditions are met.
        
        Args:
            order: Order to execute
            current_price: Current market price
            timestamp: Execution timestamp
        
        Returns:
            Fill object if order executed, None if rejected/unfilled
        
        Note:
            Should check buying power, apply slippage/commission,
            and update portfolio state.
        """
        pass
    
    @abstractmethod
    def check_buying_power(self, order: Order, price: float) -> bool:
        """
        Check if sufficient capital is available for order.
        
        Args:
            order: Order to check
            price: Estimated execution price
        
        Returns:
            True if order can be executed, False otherwise
        """
        pass
    
    @abstractmethod
    def calculate_commission(self, fill_price: float, quantity: float) -> float:
        """
        Calculate commission for a trade.
        
        Args:
            fill_price: Price at which order filled
            quantity: Quantity traded
        
        Returns:
            Commission amount in dollars
        """
        pass
    
    @abstractmethod
    def calculate_slippage(
        self,
        order: Order,
        market_price: float
    ) -> float:
        """
        Calculate realistic fill price with slippage.
        
        Args:
            order: Order being filled
            market_price: Current market price
        
        Returns:
            Expected fill price including slippage
        
        Note:
            Slippage models can be:
            - Fixed percentage
            - Volume-based
            - Bid-ask spread based
        """
        pass
    
    @abstractmethod
    def get_positions(self) -> Dict[str, Position]:
        """
        Get all current positions.
        
        Returns:
            Dictionary mapping symbol to Position object
        """
        pass
    
    @abstractmethod
    def get_cash_balance(self) -> float:
        """
        Get current cash balance.
        
        Returns:
            Available cash in dollars
        """
        pass


# =============================================================================
# Portfolio Management Interfaces
# =============================================================================


class IPortfolioManager(ABC):
    """
    Abstract interface for portfolio management.
    
    The portfolio manager tracks:
    - All positions (long and short)
    - Cash balance
    - Portfolio value over time
    - Performance metrics
    
    This abstraction allows different portfolio models:
    - Simple portfolio: Cash + positions
    - Margin portfolio: Leverage, margin calls
    - Multi-account portfolio: Multiple strategies/accounts
    """
    
    @abstractmethod
    def update_position(
        self,
        symbol: str,
        fill: Fill,
        current_price: float
    ) -> None:
        """
        Update position based on a fill.
        
        Args:
            symbol: Symbol being traded
            fill: Fill details
            current_price: Current market price for P&L calculation
        """
        pass
    
    @abstractmethod
    def get_position(self, symbol: str) -> Optional[Position]:
        """
        Get current position for a symbol.
        
        Args:
            symbol: Symbol to query
        
        Returns:
            Position object or None if no position
        """
        pass
    
    @abstractmethod
    def get_all_positions(self) -> Dict[str, Position]:
        """
        Get all current positions.
        
        Returns:
            Dictionary mapping symbol to Position
        """
        pass
    
    @abstractmethod
    def get_portfolio_value(self, current_prices: Dict[str, float]) -> float:
        """
        Calculate total portfolio value.
        
        Args:
            current_prices: Current market prices for all holdings
        
        Returns:
            Total value (cash + positions) in dollars
        """
        pass
    
    @abstractmethod
    def get_cash_balance(self) -> float:
        """
        Get current cash balance.
        
        Returns:
            Available cash in dollars
        """
        pass
    
    @abstractmethod
    def update_cash(self, amount: float) -> None:
        """
        Update cash balance.
        
        Args:
            amount: Amount to add (positive) or remove (negative)
        """
        pass
    
    @abstractmethod
    def mark_to_market(self, current_prices: Dict[str, float]) -> None:
        """
        Update unrealized P&L for all positions.
        
        Args:
            current_prices: Current market prices
        """
        pass
    
    @abstractmethod
    def get_total_pnl(self) -> float:
        """
        Get total profit/loss (realized + unrealized).
        
        Returns:
            Total P&L in dollars
        """
        pass
    
    @abstractmethod
    def get_portfolio_snapshot(self) -> Dict:
        """
        Get current portfolio state as a dictionary.
        
        Returns:
            Dictionary with portfolio metrics:
                - timestamp
                - cash
                - positions_value
                - portfolio_value
                - unrealized_pnl
                - realized_pnl
                - positions: {symbol: quantity}
        """
        pass


# =============================================================================
# Results and Analytics Interfaces
# =============================================================================


class IPerformanceAnalyzer(ABC):
    """
    Abstract interface for performance analysis.
    
    Calculates and reports on backtest performance metrics:
    - Returns (total, annualized, rolling)
    - Risk metrics (volatility, Sharpe, Sortino)
    - Drawdown analysis
    - Trade statistics
    
    This abstraction allows different analytics:
    - Basic analyzer: Simple returns and metrics
    - Advanced analyzer: Comprehensive risk analysis
    - Comparative analyzer: Benchmark comparison
    """
    
    @abstractmethod
    def calculate_returns(self, equity_curve: pd.Series) -> pd.Series:
        """
        Calculate returns from equity curve.
        
        Args:
            equity_curve: Portfolio values over time
        
        Returns:
            Series of period returns
        """
        pass
    
    @abstractmethod
    def calculate_total_return(self, initial: float, final: float) -> float:
        """
        Calculate total return.
        
        Args:
            initial: Starting capital
            final: Ending capital
        
        Returns:
            Total return as decimal (e.g., 0.15 = 15%)
        """
        pass
    
    @abstractmethod
    def calculate_sharpe_ratio(
        self,
        returns: pd.Series,
        risk_free_rate: float = 0.0
    ) -> float:
        """
        Calculate Sharpe ratio.
        
        Args:
            returns: Period returns
            risk_free_rate: Risk-free rate (annualized)
        
        Returns:
            Sharpe ratio
        """
        pass
    
    @abstractmethod
    def calculate_max_drawdown(self, equity_curve: pd.Series) -> float:
        """
        Calculate maximum drawdown.
        
        Args:
            equity_curve: Portfolio values over time
        
        Returns:
            Maximum drawdown as decimal (e.g., 0.20 = 20% drawdown)
        """
        pass
    
    @abstractmethod
    def calculate_win_rate(self, trades: List[Fill]) -> float:
        """
        Calculate win rate from trades.
        
        Args:
            trades: List of trade fills
        
        Returns:
            Win rate as decimal (e.g., 0.60 = 60% wins)
        """
        pass
    
    @abstractmethod
    def generate_report(
        self,
        equity_curve: pd.Series,
        trades: List[Fill],
        initial_capital: float
    ) -> Dict:
        """
        Generate comprehensive performance report.
        
        Args:
            equity_curve: Portfolio values over time
            trades: All trade fills
            initial_capital: Starting capital
        
        Returns:
            Dictionary with all performance metrics
        """
        pass


class IResultsTracker(ABC):
    """
    Abstract interface for tracking backtest results.
    
    Captures and stores:
    - Portfolio history (equity curve)
    - Trade history (all fills)
    - Position history
    - Performance metrics
    
    This abstraction allows different storage:
    - In-memory tracker: Fast, limited size
    - Database tracker: Persistent, scalable
    - Streaming tracker: Real-time updates
    """
    
    @abstractmethod
    def record_portfolio_state(
        self,
        timestamp: datetime,
        portfolio_snapshot: Dict
    ) -> None:
        """
        Record portfolio state at a point in time.
        
        Args:
            timestamp: Current time
            portfolio_snapshot: Portfolio metrics dictionary
        """
        pass
    
    @abstractmethod
    def record_trade(self, fill: Fill) -> None:
        """
        Record a trade execution.
        
        Args:
            fill: Fill details
        """
        pass
    
    @abstractmethod
    def get_equity_curve(self) -> pd.Series:
        """
        Get portfolio value over time.
        
        Returns:
            Series with DatetimeIndex and portfolio values
        """
        pass
    
    @abstractmethod
    def get_trade_log(self) -> pd.DataFrame:
        """
        Get all trades as a DataFrame.
        
        Returns:
            DataFrame with trade details (time, symbol, side, etc.)
        """
        pass
    
    @abstractmethod
    def get_portfolio_history(self) -> pd.DataFrame:
        """
        Get complete portfolio history.
        
        Returns:
            DataFrame with portfolio metrics over time
        """
        pass
    
    @abstractmethod
    def clear(self) -> None:
        """Clear all recorded data."""
        pass


# =============================================================================
# Strategy Protocol (Alternative to ABC)
# =============================================================================


class IStrategy(Protocol):
    """
    Protocol definition for strategies (duck typing alternative).
    
    This is an alternative to ABC inheritance that uses structural
    subtyping. Strategies don't need to inherit from a base class,
    they just need to implement the required methods.
    
    Note:
        The actual Strategy class uses ABC for stronger typing.
        This Protocol is provided for documentation and potential
        future use with type checkers.
    """
    
    name: str
    
    def initialize(self) -> None:
        """Called before backtest starts."""
        ...
    
    def on_data(self, timestamp: datetime, data: pd.DataFrame) -> List[Order]:
        """Process market data and generate orders."""
        ...
    
    def on_fill(self, fill: Fill) -> None:
        """Handle order execution notification."""
        ...
    
    def finalize(self) -> None:
        """Called after backtest ends."""
        ...


# =============================================================================
# Configuration Interfaces
# =============================================================================


@dataclass
class BacktestConfig:
    """
    Configuration for a backtest run.
    
    Attributes:
        initial_capital: Starting capital in dollars
        start_date: Backtest start date
        end_date: Backtest end date
        symbols: List of symbols to trade
        commission_rate: Commission as decimal (e.g., 0.001 = 0.1%)
        slippage_rate: Slippage as decimal (e.g., 0.0005 = 0.05%)
        data_frequency: Data interval ('1d', '1h', etc.)
        benchmark: Optional benchmark symbol for comparison
        risk_free_rate: Risk-free rate for metrics (annualized)
    """
    
    initial_capital: float
    start_date: datetime
    end_date: datetime
    symbols: List[str]
    commission_rate: float = 0.001
    slippage_rate: float = 0.0005
    data_frequency: str = '1d'
    benchmark: Optional[str] = None
    risk_free_rate: float = 0.0


@dataclass
class BrokerConfig:
    """
    Configuration for broker/execution.
    
    Attributes:
        commission_rate: Commission as decimal
        slippage_rate: Slippage as decimal
        allow_shorting: Whether short selling is allowed
        margin_rate: Margin interest rate (if using margin)
        max_leverage: Maximum portfolio leverage
        min_order_size: Minimum order quantity
        max_order_size: Maximum order quantity
    """
    
    commission_rate: float = 0.001
    slippage_rate: float = 0.0005
    allow_shorting: bool = True
    margin_rate: float = 0.0
    max_leverage: float = 1.0
    min_order_size: float = 1.0
    max_order_size: Optional[float] = None


# =============================================================================
# Event System (Future Enhancement)
# =============================================================================


class IEventBus(ABC):
    """
    Abstract interface for event-driven communication.
    
    An event bus allows components to communicate through events
    without tight coupling. This is a future enhancement for more
    sophisticated backtesting.
    
    Events could include:
    - MarketDataEvent: New market data available
    - OrderEvent: Order placed
    - FillEvent: Order executed
    - PositionEvent: Position changed
    - PortfolioEvent: Portfolio updated
    """
    
    @abstractmethod
    def publish(self, event_type: str, event_data: Dict) -> None:
        """
        Publish an event.
        
        Args:
            event_type: Type of event (e.g., 'market_data', 'fill')
            event_data: Event payload
        """
        pass
    
    @abstractmethod
    def subscribe(self, event_type: str, handler: callable) -> None:
        """
        Subscribe to an event type.
        
        Args:
            event_type: Type of event to listen for
            handler: Callback function to handle event
        """
        pass
    
    @abstractmethod
    def unsubscribe(self, event_type: str, handler: callable) -> None:
        """
        Unsubscribe from an event type.
        
        Args:
            event_type: Event type
            handler: Handler to remove
        """
        pass


# =============================================================================
# Risk Management (Future Enhancement)
# =============================================================================


class IRiskManager(ABC):
    """
    Abstract interface for risk management.
    
    Risk managers enforce position limits and risk controls:
    - Position size limits
    - Portfolio concentration limits
    - Stop-loss enforcement
    - Maximum drawdown protection
    - Correlation limits
    
    This is a future enhancement for production systems.
    """
    
    @abstractmethod
    def check_order(self, order: Order, portfolio_state: Dict) -> bool:
        """
        Check if order violates risk limits.
        
        Args:
            order: Order to check
            portfolio_state: Current portfolio metrics
        
        Returns:
            True if order is acceptable, False if rejected
        """
        pass
    
    @abstractmethod
    def calculate_position_size(
        self,
        symbol: str,
        signal_strength: float,
        portfolio_value: float,
        risk_params: Dict
    ) -> float:
        """
        Calculate appropriate position size.
        
        Args:
            symbol: Symbol to trade
            signal_strength: Strategy signal (-1 to 1)
            portfolio_value: Current portfolio value
            risk_params: Risk parameters (max_position_pct, etc.)
        
        Returns:
            Recommended position size
        """
        pass
    
    @abstractmethod
    def get_risk_metrics(self, portfolio_state: Dict) -> Dict:
        """
        Calculate current risk metrics.
        
        Args:
            portfolio_state: Current portfolio state
        
        Returns:
            Dictionary with risk metrics (VaR, exposure, etc.)
        """
        pass
