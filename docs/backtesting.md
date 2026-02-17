# Backtesting Engine Documentation

## Overview

The Copilot Quant backtesting engine allows you to test trading strategies against historical market data. It provides a realistic simulation environment with transaction costs, position tracking, and comprehensive performance analytics.

## Key Features

- **Event-driven architecture**: Simulates real-time trading by replaying historical data chronologically
- **Realistic order execution**: Supports market and limit orders with configurable slippage
- **Transaction costs**: Applies commission and slippage to simulate real trading costs
- **Position tracking**: Maintains accurate position sizes, entry prices, and P&L
- **Strategy callbacks**: Hooks for initialization, data processing, order fills, and finalization
- **Comprehensive results**: Detailed trade logs, portfolio history, and performance metrics

## Architecture

### Core Components

1. **BacktestEngine** (`copilot_quant.backtest.engine`)
   - Main orchestrator that runs the backtest
   - Manages data replay, order execution, and result collection

2. **Strategy** (`copilot_quant.backtest.strategy`)
   - Abstract base class for trading strategies
   - Implement `on_data()` to define trading logic

3. **Orders** (`copilot_quant.backtest.orders`)
   - `Order`: Represents a trading order
   - `Fill`: Represents an executed order
   - `Position`: Tracks current holdings in a security

4. **Results** (`copilot_quant.backtest.results`)
   - `BacktestResult`: Stores performance metrics and trade history

## Quick Start

### 1. Create a Strategy

```python
from copilot_quant.backtest import Strategy, Order

class BuyAndHold(Strategy):
    def __init__(self, symbol='SPY', quantity=100):
        super().__init__()
        self.symbol = symbol
        self.quantity = quantity
        self.invested = False
    
    def on_data(self, timestamp, data):
        """Buy once and hold."""
        if not self.invested:
            self.invested = True
            return [Order(
                symbol=self.symbol,
                quantity=self.quantity,
                order_type='market',
                side='buy'
            )]
        return []
```

### 2. Run the Backtest

```python
from datetime import datetime
from copilot_quant.backtest import BacktestEngine
from copilot_quant.data.providers import YFinanceProvider

# Initialize engine
engine = BacktestEngine(
    initial_capital=100000,
    data_provider=YFinanceProvider(),
    commission=0.001,   # 0.1%
    slippage=0.0005     # 0.05%
)

# Add strategy
engine.add_strategy(BuyAndHold(symbol='SPY', quantity=100))

# Run backtest
result = engine.run(
    start_date=datetime(2020, 1, 1),
    end_date=datetime(2023, 12, 31),
    symbols=['SPY']
)

# View results
print(f"Total Return: {result.total_return:.2%}")
print(f"Final Capital: ${result.final_capital:,.2f}")
```

## Strategy Development

### Strategy Lifecycle

1. **initialize()** - Called once before backtest starts
   - Set up indicators, state variables
   - Load any configuration

2. **on_data(timestamp, data)** - Called for each data point
   - Main strategy logic
   - Return list of orders to execute
   - Must avoid look-ahead bias

3. **on_fill(fill)** - Called when an order is filled (optional)
   - Track fills for analysis
   - Update internal state

4. **finalize()** - Called once after backtest ends (optional)
   - Cleanup or final calculations

### Example: Moving Average Crossover

```python
from copilot_quant.backtest import Strategy, Order

class MovingAverageCrossover(Strategy):
    def __init__(self, symbol='SPY', short_window=50, long_window=200):
        super().__init__()
        self.symbol = symbol
        self.short_window = short_window
        self.long_window = long_window
        self.position = 0
    
    def on_data(self, timestamp, data):
        # Need enough data for long MA
        if len(data) < self.long_window:
            return []
        
        # Calculate moving averages
        closes = data['Close']
        short_ma = closes.tail(self.short_window).mean()
        long_ma = closes.tail(self.long_window).mean()
        
        orders = []
        
        # Golden cross - buy signal
        if short_ma > long_ma and self.position <= 0:
            orders.append(Order(
                symbol=self.symbol,
                quantity=100,
                order_type='market',
                side='buy'
            ))
            self.position = 1
        
        # Death cross - sell signal
        elif short_ma < long_ma and self.position > 0:
            orders.append(Order(
                symbol=self.symbol,
                quantity=100,
                order_type='market',
                side='sell'
            ))
            self.position = 0
        
        return orders
```

## Order Types

### Market Orders

Execute immediately at the next available price plus slippage.

```python
Order(
    symbol='AAPL',
    quantity=100,
    order_type='market',
    side='buy'
)
```

### Limit Orders

Execute only if price reaches the limit price.

```python
Order(
    symbol='AAPL',
    quantity=100,
    order_type='limit',
    side='buy',
    limit_price=150.0  # Will only fill if price <= $150
)
```

## Transaction Costs

### Commission

Applied as a percentage of trade value:
```python
commission = fill_price * quantity * commission_rate
```

### Slippage

Applied to market orders to simulate market impact:
- **Buy orders**: Fill at `price * (1 + slippage_rate)`
- **Sell orders**: Fill at `price * (1 - slippage_rate)`

Example:
```python
engine = BacktestEngine(
    initial_capital=100000,
    data_provider=provider,
    commission=0.001,   # 0.1% commission
    slippage=0.0005     # 0.05% slippage
)
```

## Position Tracking

The engine automatically tracks:
- **Quantity**: Current position size (positive = long, negative = short)
- **Average entry price**: Cost basis
- **Unrealized P&L**: Current profit/loss on open positions
- **Realized P&L**: Cumulative profit/loss from closed trades

### Long Positions

```python
# Open long position
buy_order = Order(symbol='AAPL', quantity=100, order_type='market', side='buy')

# Increase long position
buy_more = Order(symbol='AAPL', quantity=50, order_type='market', side='buy')

# Close long position
sell_order = Order(symbol='AAPL', quantity=150, order_type='market', side='sell')
```

### Short Positions

```python
# Open short position
short_order = Order(symbol='AAPL', quantity=100, order_type='market', side='sell')

# Close short position
cover_order = Order(symbol='AAPL', quantity=100, order_type='market', side='buy')
```

## Analyzing Results

### BacktestResult Object

```python
result = engine.run(...)

# Basic performance metrics
print(f"Total Return: {result.total_return:.2%}")
print(f"Final Capital: ${result.final_capital:,.2f}")

# Trade log
trade_log = result.get_trade_log()
print(trade_log)

# Equity curve
equity_curve = result.get_equity_curve()
equity_curve.plot(title='Portfolio Value Over Time')

# Comprehensive performance metrics
metrics = result.get_performance_metrics(risk_free_rate=0.02)
print(f"Sharpe Ratio: {metrics['sharpe_ratio']:.2f}")
print(f"Max Drawdown: {metrics['max_drawdown']:.2%}")
print(f"Win Rate: {metrics['win_rate']:.2%}")
print(f"Sortino Ratio: {metrics['sortino_ratio']:.2f}")
print(f"Calmar Ratio: {metrics['calmar_ratio']:.2f}")
print(f"Profit Factor: {metrics['profit_factor']:.2f}")
```

### Performance Metrics

The `get_performance_metrics()` method returns comprehensive statistics:

**Return Metrics:**
- `total_return`: Total return as decimal (e.g., 0.15 = 15%)
- `total_return_pct`: Total return as percentage
- `annualized_return`: Compound annual growth rate (CAGR)
- `cagr`: Same as annualized_return

**Risk Metrics:**
- `volatility`: Annualized volatility (standard deviation of returns)
- `max_drawdown`: Largest peak-to-trough decline (e.g., -0.20 = -20%)
- `sharpe_ratio`: Risk-adjusted return (higher is better, typically 1-3 is good)
- `sortino_ratio`: Similar to Sharpe but only penalizes downside volatility
- `calmar_ratio`: Return divided by max drawdown (higher is better)

**Trade Statistics:**
- `total_trades`: Number of completed round-trip trades
- `win_rate`: Percentage of profitable trades
- `profit_factor`: Gross profit / Gross loss (>1 means profitable)
- `avg_win`: Average profit from winning trades
- `avg_loss`: Average loss from losing trades
- `avg_trade`: Average profit/loss per trade

**Time Metrics:**
- `trading_days`: Number of trading days in backtest
- `trading_years`: Trading period in years

Example:
```python
# Get comprehensive metrics
metrics = result.get_performance_metrics(risk_free_rate=0.02)

# Display key metrics
print(f"\n{'='*50}")
print(f"Strategy: {metrics['strategy_name']}")
print(f"Period: {metrics['start_date']} to {metrics['end_date']}")
print(f"{'='*50}")
print(f"\nReturns:")
print(f"  Total Return: {metrics['total_return']:.2%}")
print(f"  Annualized Return: {metrics['annualized_return']:.2%}")
print(f"\nRisk Metrics:")
print(f"  Sharpe Ratio: {metrics['sharpe_ratio']:.2f}")
print(f"  Sortino Ratio: {metrics['sortino_ratio']:.2f}")
print(f"  Max Drawdown: {metrics['max_drawdown']:.2%}")
print(f"  Volatility: {metrics['volatility']:.2%}")
print(f"\nTrade Statistics:")
print(f"  Total Trades: {metrics['total_trades']}")
print(f"  Win Rate: {metrics['win_rate']:.2%}")
print(f"  Profit Factor: {metrics['profit_factor']:.2f}")
print(f"  Avg Win: ${metrics['avg_win']:.2f}")
print(f"  Avg Loss: ${metrics['avg_loss']:.2f}")
```

### Using the PerformanceAnalyzer Directly

For advanced use cases, you can use the PerformanceAnalyzer class directly:

```python
from copilot_quant.backtest import PerformanceAnalyzer

# Create analyzer with custom risk-free rate
analyzer = PerformanceAnalyzer(risk_free_rate=0.03)

# Get equity curve from backtest result
equity_curve = result.get_equity_curve()

# Calculate specific metrics
sharpe = analyzer.calculate_sharpe_ratio(
    analyzer.calculate_returns(equity_curve)
)
max_dd = analyzer.calculate_max_drawdown(equity_curve)
win_rate = analyzer.calculate_win_rate(result.trades)

print(f"Sharpe Ratio: {sharpe:.2f}")
print(f"Max Drawdown: {max_dd:.2%}")
print(f"Win Rate: {win_rate:.2%}")
```

### Portfolio History

The `portfolio_history` DataFrame contains:
- `timestamp`: Date/time
- `portfolio_value`: Total value (cash + positions)
- `cash`: Available cash
- `positions_value`: Total value of all positions
- `position_{symbol}`: Quantity for each symbol
- `value_{symbol}`: Market value for each symbol

## Best Practices

### Avoid Look-Ahead Bias

❌ **Wrong** - Using future data:
```python
def on_data(self, timestamp, data):
    # DON'T do this - uses all data including future
    max_price = data['Close'].max()
```

✅ **Correct** - Only use past data:
```python
def on_data(self, timestamp, data):
    # Only use data up to current timestamp
    max_price = data.loc[:timestamp, 'Close'].max()
```

### Handle Edge Cases

```python
def on_data(self, timestamp, data):
    # Check for sufficient data
    if len(data) < self.lookback_period:
        return []
    
    # Handle missing data
    if data['Close'].iloc[-1] is None:
        return []
    
    # Your trading logic here
    ...
```

### Transaction Cost Awareness

```python
# Consider round-trip costs before trading
min_profit_threshold = 2 * (commission_rate + slippage_rate)

if expected_return > min_profit_threshold:
    # Trade only if expected profit exceeds costs
    return [order]
```

## Testing Your Strategy

### Unit Testing

```python
import pytest
from copilot_quant.backtest import Strategy

def test_strategy_initialization():
    strategy = MyStrategy(param1=10)
    assert strategy.param1 == 10

def test_strategy_generates_orders():
    strategy = MyStrategy()
    data = create_test_data()
    orders = strategy.on_data(timestamp, data)
    assert len(orders) > 0
```

### Mock Data Provider

```python
from copilot_quant.data.providers import DataProvider
import pandas as pd

class MockDataProvider(DataProvider):
    def get_historical_data(self, symbol, start_date=None, end_date=None, interval='1d'):
        # Return controlled test data
        dates = pd.date_range('2020-01-01', periods=100)
        return pd.DataFrame({
            'Close': [100 + i for i in range(100)],
            'Open': [100 + i for i in range(100)],
            'High': [105 + i for i in range(100)],
            'Low': [95 + i for i in range(100)],
            'Volume': [1000000] * 100
        }, index=dates)
```

## Performance Considerations

### Data Frequency

- **Daily data**: Fast, suitable for most strategies
- **Intraday data**: Slower, use for high-frequency strategies
- Consider downsampling if not needed

### Large Backtests

For multi-year backtests:
1. Use date ranges to limit data
2. Consider chunking very long periods
3. Monitor memory usage for multiple symbols

### Multiple Symbols

```python
# Efficient multi-symbol backtest
result = engine.run(
    start_date=start_date,
    end_date=end_date,
    symbols=['SPY', 'QQQ', 'IWM']  # Multiple symbols
)
```

## Limitations

Current limitations (planned for future releases):

1. **No partial fills**: Orders fill completely or not at all
2. **No advanced order types**: Stop-loss, trailing stops not yet supported
3. **Simplified market impact**: Fixed slippage model
4. **Daily mark-to-market**: Intraday P&L not tracked separately
5. **No margin calls**: Assumes sufficient buying power
6. **No corporate actions**: Splits/dividends not yet handled

## Examples

See the `examples/` directory for complete examples:

- `run_backtest.py` - Basic buy-and-hold strategy with live data
- `run_backtest_mock.py` - Buy-and-hold with mock data (no network required)

## API Reference

### BacktestEngine

```python
BacktestEngine(
    initial_capital: float,
    data_provider: DataProvider,
    commission: float = 0.001,
    slippage: float = 0.0005
)
```

**Methods:**
- `add_strategy(strategy: Strategy)` - Register a strategy
- `run(start_date, end_date, symbols) -> BacktestResult` - Execute backtest
- `get_portfolio_value() -> float` - Get current portfolio value
- `get_positions() -> Dict[str, Position]` - Get current positions

### Strategy (Abstract Base Class)

```python
class Strategy(ABC):
    @abstractmethod
    def on_data(self, timestamp: datetime, data: pd.DataFrame) -> List[Order]:
        """Called on each data point. Return orders to execute."""
    
    def on_fill(self, fill: Fill) -> None:
        """Called when order is filled (optional)."""
    
    def initialize(self) -> None:
        """Called before backtest starts (optional)."""
    
    def finalize(self) -> None:
        """Called after backtest ends (optional)."""
```

### Order

```python
Order(
    symbol: str,
    quantity: float,
    order_type: str,  # 'market' or 'limit'
    side: str,  # 'buy' or 'sell'
    limit_price: Optional[float] = None,
    timestamp: Optional[datetime] = None
)
```

### Fill

```python
@dataclass
class Fill:
    order: Order
    fill_price: float
    fill_quantity: float
    commission: float
    timestamp: datetime
    
    @property
    def total_cost(self) -> float
    
    @property
    def net_proceeds(self) -> float
```

### Position

```python
@dataclass
class Position:
    symbol: str
    quantity: float
    avg_entry_price: float
    unrealized_pnl: float
    realized_pnl: float
    
    def update_from_fill(self, fill: Fill, current_price: float)
    def update_unrealized_pnl(self, current_price: float)
```

### BacktestResult

```python
@dataclass
class BacktestResult:
    strategy_name: str
    start_date: datetime
    end_date: datetime
    initial_capital: float
    final_capital: float
    total_return: float
    trades: List[Fill]
    portfolio_history: pd.DataFrame
    
    def get_trade_log() -> pd.DataFrame
    def get_equity_curve() -> pd.Series
    def get_summary_stats(risk_free_rate: float = 0.02) -> Dict
    def get_performance_metrics(risk_free_rate: float = 0.02) -> Dict
```

**Methods:**
- `get_trade_log()`: Returns DataFrame of all trades with timestamps, symbols, sides, quantities, prices, commissions
- `get_equity_curve()`: Returns time series of portfolio values
- `get_summary_stats(risk_free_rate)`: Calculate comprehensive performance metrics (same as get_performance_metrics)
- `get_performance_metrics(risk_free_rate)`: Calculate comprehensive performance metrics including Sharpe, Sortino, drawdown, win rate, etc.

### PerformanceAnalyzer

```python
class PerformanceAnalyzer:
    def __init__(self, risk_free_rate: float = 0.02)
    
    def calculate_metrics(
        equity_curve: pd.Series,
        trades: List[Fill],
        initial_capital: float
    ) -> Dict
    
    def calculate_returns(equity_curve: pd.Series) -> pd.Series
    def calculate_total_return(initial: float, final: float) -> float
    def calculate_sharpe_ratio(returns: pd.Series, risk_free_rate: float = None) -> float
    def calculate_sortino_ratio(returns: pd.Series, risk_free_rate: float = None) -> float
    def calculate_max_drawdown(equity_curve: pd.Series) -> float
    def calculate_win_rate(trades: List[Fill]) -> float
```

**Methods:**
- `calculate_metrics()`: Calculate all performance metrics in one call
- `calculate_returns()`: Convert equity curve to period returns
- `calculate_total_return()`: Calculate total return percentage
- `calculate_sharpe_ratio()`: Calculate annualized Sharpe ratio (risk-adjusted returns)
- `calculate_sortino_ratio()`: Calculate annualized Sortino ratio (downside risk-adjusted returns)
- `calculate_max_drawdown()`: Calculate maximum peak-to-trough decline
- `calculate_win_rate()`: Calculate percentage of profitable trades

## Support

For issues, questions, or contributions, please visit:
- GitHub: https://github.com/harryb2088/copilot_quant
- Documentation: https://github.com/harryb2088/copilot_quant/docs

## License

Copyright © 2024 Copilot Quant Platform
