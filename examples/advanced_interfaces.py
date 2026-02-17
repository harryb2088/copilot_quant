"""
Example implementations of advanced backtesting interfaces.

This module demonstrates how to implement custom versions of the
backtesting engine interfaces for specialized use cases.
"""

from datetime import datetime
from typing import Dict, List, Optional

import pandas as pd

from copilot_quant.backtest.interfaces import (
    IBroker,
    IDataFeed,
    IPerformanceAnalyzer,
    IPortfolioManager,
    IResultsTracker,
)
from copilot_quant.backtest.orders import Fill, Order, Position


# =============================================================================
# Example: Custom Broker with Volume-Based Slippage
# =============================================================================


class VolumeBasedBroker(IBroker):
    """
    Broker implementation with volume-based slippage model.
    
    Slippage increases with order size relative to daily volume:
    - Small orders (< 1% of volume): Minimal slippage
    - Large orders (> 10% of volume): Significant slippage
    """
    
    def __init__(
        self,
        commission_rate: float = 0.001,
        base_slippage: float = 0.0005,
        volume_impact_factor: float = 0.1
    ):
        self.commission_rate = commission_rate
        self.base_slippage = base_slippage
        self.volume_impact_factor = volume_impact_factor
        self.cash = 0.0
        self.positions: Dict[str, Position] = {}
    
    def execute_order(
        self,
        order: Order,
        current_price: float,
        timestamp: datetime,
        daily_volume: Optional[float] = None
    ) -> Optional[Fill]:
        """Execute order with volume-based slippage."""
        # Check buying power
        if not self.check_buying_power(order, current_price):
            return None
        
        # Calculate fill price with dynamic slippage
        fill_price = self.calculate_slippage(
            order, 
            current_price,
            daily_volume
        )
        
        if fill_price is None:
            # Limit order not filled
            return None
        
        # Calculate commission
        commission = self.calculate_commission(fill_price, order.quantity)
        
        # Create fill
        fill = Fill(
            order=order,
            fill_price=fill_price,
            fill_quantity=order.quantity,
            commission=commission,
            timestamp=timestamp
        )
        
        return fill
    
    def check_buying_power(self, order: Order, price: float) -> bool:
        """Check if sufficient capital available."""
        if order.side == 'buy':
            required = price * order.quantity * (1 + self.commission_rate)
            return self.cash >= required
        return True  # Selling doesn't require cash
    
    def calculate_commission(self, fill_price: float, quantity: float) -> float:
        """Calculate percentage-based commission."""
        return fill_price * quantity * self.commission_rate
    
    def calculate_slippage(
        self,
        order: Order,
        market_price: float,
        daily_volume: Optional[float] = None
    ) -> Optional[float]:
        """
        Calculate fill price with volume-based slippage.
        
        Args:
            order: Order to fill
            market_price: Current market price
            daily_volume: Average daily volume (None = use base slippage)
        
        Returns:
            Fill price or None if limit order can't fill
        """
        # Start with base slippage
        slippage = self.base_slippage
        
        # Add volume-based impact if data available
        if daily_volume and daily_volume > 0:
            volume_fraction = order.quantity / daily_volume
            volume_impact = volume_fraction * self.volume_impact_factor
            slippage += volume_impact
        
        # Apply slippage
        if order.order_type == 'market':
            if order.side == 'buy':
                return market_price * (1 + slippage)
            else:
                return market_price * (1 - slippage)
        
        elif order.order_type == 'limit':
            # Check if limit can fill
            if order.side == 'buy' and market_price <= order.limit_price:
                return order.limit_price
            elif order.side == 'sell' and market_price >= order.limit_price:
                return order.limit_price
            return None
        
        return market_price
    
    def get_positions(self) -> Dict[str, Position]:
        """Get current positions."""
        return self.positions.copy()
    
    def get_cash_balance(self) -> float:
        """Get cash balance."""
        return self.cash


# =============================================================================
# Example: CSV Data Feed
# =============================================================================


class CSVDataFeed(IDataFeed):
    """
    DataFeed implementation that reads from CSV files.
    
    Expected directory structure:
        data_dir/
            AAPL.csv
            SPY.csv
            ...
    
    CSV format:
        Date,Open,High,Low,Close,Volume
        2020-01-02,100.0,101.0,99.0,100.5,1000000
        ...
    """
    
    def __init__(self, data_dir: str):
        self.data_dir = data_dir
        self._cache: Dict = {}
    
    def get_historical_data(
        self,
        symbol: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        interval: str = '1d'
    ) -> pd.DataFrame:
        """Load historical data from CSV file."""
        # Check cache
        cache_key = (symbol, start_date, end_date)
        if cache_key in self._cache:
            return self._cache[cache_key].copy()
        
        # Load from CSV
        filepath = f"{self.data_dir}/{symbol}.csv"
        
        try:
            df = pd.read_csv(filepath, index_col='Date', parse_dates=True)
            
            # Filter by date range
            if start_date:
                df = df[df.index >= start_date]
            if end_date:
                df = df[df.index <= end_date]
            
            # Validate required columns
            required = ['Open', 'High', 'Low', 'Close', 'Volume']
            if not all(col in df.columns for col in required):
                raise ValueError(f"CSV missing required columns for {symbol}")
            
            # Cache result
            self._cache[cache_key] = df.copy()
            
            return df
        
        except FileNotFoundError:
            print(f"Warning: No data file found for {symbol}")
            return pd.DataFrame()
    
    def get_multiple_symbols(
        self,
        symbols: List[str],
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        interval: str = '1d'
    ) -> pd.DataFrame:
        """Load data for multiple symbols."""
        dfs = []
        
        for symbol in symbols:
            df = self.get_historical_data(symbol, start_date, end_date, interval)
            if not df.empty:
                df['Symbol'] = symbol
                dfs.append(df)
        
        if not dfs:
            return pd.DataFrame()
        
        # Combine all symbols
        combined = pd.concat(dfs)
        combined = combined.sort_index()
        
        return combined
    
    def get_ticker_info(self, symbol: str) -> Dict:
        """Get ticker metadata (limited for CSV)."""
        return {
            'symbol': symbol,
            'name': symbol,
            'source': 'CSV'
        }


# =============================================================================
# Example: Advanced Performance Analyzer
# =============================================================================


class AdvancedPerformanceAnalyzer(IPerformanceAnalyzer):
    """
    Performance analyzer with comprehensive metrics.
    
    Calculates:
    - Returns (total, annualized, rolling)
    - Risk metrics (Sharpe, Sortino, Calmar)
    - Drawdown analysis
    - Trade statistics
    """
    
    def __init__(self, risk_free_rate: float = 0.02):
        self.risk_free_rate = risk_free_rate
    
    def calculate_returns(self, equity_curve: pd.Series) -> pd.Series:
        """Calculate period returns."""
        return equity_curve.pct_change().fillna(0)
    
    def calculate_total_return(self, initial: float, final: float) -> float:
        """Calculate total return."""
        return (final - initial) / initial
    
    def calculate_sharpe_ratio(
        self,
        returns: pd.Series,
        risk_free_rate: float = None
    ) -> float:
        """
        Calculate Sharpe ratio.
        
        Sharpe = (Mean Return - Risk Free Rate) / Std Dev of Returns
        """
        if risk_free_rate is None:
            risk_free_rate = self.risk_free_rate
        
        if len(returns) == 0 or returns.std() == 0:
            return 0.0
        
        # Annualize (assuming daily returns)
        excess_return = returns.mean() - (risk_free_rate / 252)
        sharpe = excess_return / returns.std()
        sharpe_annualized = sharpe * (252 ** 0.5)
        
        return sharpe_annualized
    
    def calculate_sortino_ratio(
        self,
        returns: pd.Series,
        risk_free_rate: float = None
    ) -> float:
        """
        Calculate Sortino ratio (uses downside deviation).
        
        Sortino = (Mean Return - Risk Free Rate) / Downside Deviation
        """
        if risk_free_rate is None:
            risk_free_rate = self.risk_free_rate
        
        if len(returns) == 0:
            return 0.0
        
        # Calculate downside deviation
        downside_returns = returns[returns < 0]
        if len(downside_returns) == 0 or downside_returns.std() == 0:
            return 0.0
        
        excess_return = returns.mean() - (risk_free_rate / 252)
        sortino = excess_return / downside_returns.std()
        sortino_annualized = sortino * (252 ** 0.5)
        
        return sortino_annualized
    
    def calculate_max_drawdown(self, equity_curve: pd.Series) -> float:
        """
        Calculate maximum drawdown.
        
        Returns the largest peak-to-trough decline as a negative decimal.
        """
        if len(equity_curve) == 0:
            return 0.0
        
        # Calculate running maximum
        running_max = equity_curve.expanding().max()
        
        # Calculate drawdown at each point
        drawdown = (equity_curve - running_max) / running_max
        
        # Return maximum drawdown (most negative)
        return drawdown.min()
    
    def calculate_calmar_ratio(
        self,
        total_return: float,
        max_drawdown: float,
        years: float
    ) -> float:
        """
        Calculate Calmar ratio.
        
        Calmar = Annualized Return / Absolute Max Drawdown
        """
        if max_drawdown == 0:
            return 0.0
        
        annualized_return = (1 + total_return) ** (1 / years) - 1
        return annualized_return / abs(max_drawdown)
    
    def calculate_win_rate(self, trades: List[Fill]) -> float:
        """Calculate percentage of profitable trades."""
        if not trades:
            return 0.0
        
        # Group buys and sells to identify completed trades
        # For simplification, count each sell as closing a position
        wins = 0
        total = 0
        
        for fill in trades:
            if fill.order.side == 'sell':
                # Simplified: Check if sell price > average buy price
                # Real implementation would track actual P&L
                total += 1
                # Placeholder logic
                if fill.fill_price > 0:  # Would compare to entry
                    wins += 1
        
        return wins / total if total > 0 else 0.0
    
    def generate_report(
        self,
        equity_curve: pd.Series,
        trades: List[Fill],
        initial_capital: float
    ) -> Dict:
        """Generate comprehensive performance report."""
        if equity_curve.empty:
            return {}
        
        final_capital = equity_curve.iloc[-1]
        returns = self.calculate_returns(equity_curve)
        
        # Time metrics
        days = len(equity_curve)
        years = days / 252
        
        # Calculate all metrics
        total_return = self.calculate_total_return(initial_capital, final_capital)
        annualized_return = (1 + total_return) ** (1 / years) - 1 if years > 0 else 0
        
        max_dd = self.calculate_max_drawdown(equity_curve)
        sharpe = self.calculate_sharpe_ratio(returns)
        sortino = self.calculate_sortino_ratio(returns)
        calmar = self.calculate_calmar_ratio(total_return, max_dd, years)
        
        return {
            # Returns
            'total_return': total_return,
            'annualized_return': annualized_return,
            'cagr': annualized_return,
            
            # Risk
            'volatility': returns.std() * (252 ** 0.5),
            'max_drawdown': max_dd,
            'sharpe_ratio': sharpe,
            'sortino_ratio': sortino,
            'calmar_ratio': calmar,
            
            # Trading
            'total_trades': len(trades),
            'win_rate': self.calculate_win_rate(trades),
            
            # Time
            'trading_days': days,
            'trading_years': years,
        }


# =============================================================================
# Example: In-Memory Results Tracker
# =============================================================================


class InMemoryResultsTracker(IResultsTracker):
    """
    Results tracker that stores all data in memory.
    
    Fast but limited by available RAM.
    """
    
    def __init__(self):
        self.portfolio_snapshots: List[Dict] = []
        self.trade_history: List[Fill] = []
    
    def record_portfolio_state(
        self,
        timestamp: datetime,
        portfolio_snapshot: Dict
    ) -> None:
        """Record portfolio state."""
        snapshot = portfolio_snapshot.copy()
        snapshot['timestamp'] = timestamp
        self.portfolio_snapshots.append(snapshot)
    
    def record_trade(self, fill: Fill) -> None:
        """Record a trade."""
        self.trade_history.append(fill)
    
    def get_equity_curve(self) -> pd.Series:
        """Get portfolio value time series."""
        if not self.portfolio_snapshots:
            return pd.Series(dtype=float)
        
        df = pd.DataFrame(self.portfolio_snapshots)
        df = df.set_index('timestamp')
        
        if 'portfolio_value' in df.columns:
            return df['portfolio_value']
        
        return pd.Series(dtype=float)
    
    def get_trade_log(self) -> pd.DataFrame:
        """Get all trades as DataFrame."""
        if not self.trade_history:
            return pd.DataFrame()
        
        trades_data = []
        for fill in self.trade_history:
            trades_data.append({
                'timestamp': fill.timestamp,
                'symbol': fill.order.symbol,
                'side': fill.order.side,
                'quantity': fill.fill_quantity,
                'price': fill.fill_price,
                'commission': fill.commission,
                'total_cost': fill.total_cost
            })
        
        df = pd.DataFrame(trades_data)
        df = df.set_index('timestamp')
        return df
    
    def get_portfolio_history(self) -> pd.DataFrame:
        """Get complete portfolio history."""
        if not self.portfolio_snapshots:
            return pd.DataFrame()
        
        df = pd.DataFrame(self.portfolio_snapshots)
        df = df.set_index('timestamp')
        return df
    
    def clear(self) -> None:
        """Clear all recorded data."""
        self.portfolio_snapshots.clear()
        self.trade_history.clear()


# =============================================================================
# Usage Examples
# =============================================================================


def example_volume_based_broker():
    """Example of using volume-based broker."""
    broker = VolumeBasedBroker(
        commission_rate=0.001,
        base_slippage=0.0005,
        volume_impact_factor=0.1
    )
    
    broker.cash = 100000
    
    # Small order - minimal slippage
    small_order = Order('AAPL', 100, 'market', 'buy')
    fill = broker.execute_order(
        small_order,
        current_price=150.0,
        timestamp=datetime.now(),
        daily_volume=10000000  # 10M shares daily
    )
    print(f"Small order fill: ${fill.fill_price:.2f}")
    # Slippage: ~0.05% (base only)
    
    # Large order - significant slippage
    large_order = Order('AAPL', 100000, 'market', 'buy')
    fill = broker.execute_order(
        large_order,
        current_price=150.0,
        timestamp=datetime.now(),
        daily_volume=10000000
    )
    print(f"Large order fill: ${fill.fill_price:.2f}")
    # Slippage: ~1.05% (base + 1% volume impact)


def example_csv_datafeed():
    """Example of using CSV data feed."""
    datafeed = CSVDataFeed(data_dir='./data/csv')
    
    # Load single symbol
    aapl_data = datafeed.get_historical_data(
        'AAPL',
        start_date=datetime(2020, 1, 1),
        end_date=datetime(2020, 12, 31)
    )
    print(f"Loaded {len(aapl_data)} days of AAPL data")
    
    # Load multiple symbols
    portfolio_data = datafeed.get_multiple_symbols(
        ['AAPL', 'MSFT', 'GOOGL'],
        start_date=datetime(2020, 1, 1)
    )
    print(f"Loaded {len(portfolio_data)} total data points")


def example_performance_analyzer():
    """Example of using performance analyzer."""
    analyzer = AdvancedPerformanceAnalyzer(risk_free_rate=0.02)
    
    # Create sample equity curve
    dates = pd.date_range('2020-01-01', periods=252)
    equity = pd.Series(range(100000, 100000 + 252 * 100), index=dates)
    
    # Generate report
    report = analyzer.generate_report(
        equity_curve=equity,
        trades=[],
        initial_capital=100000
    )
    
    print("Performance Metrics:")
    print(f"Total Return: {report['total_return']:.2%}")
    print(f"Sharpe Ratio: {report['sharpe_ratio']:.2f}")
    print(f"Max Drawdown: {report['max_drawdown']:.2%}")
    print(f"Sortino Ratio: {report['sortino_ratio']:.2f}")


if __name__ == '__main__':
    print("=== Volume-Based Broker ===")
    example_volume_based_broker()
    
    print("\n=== CSV Data Feed ===")
    example_csv_datafeed()
    
    print("\n=== Performance Analyzer ===")
    example_performance_analyzer()
