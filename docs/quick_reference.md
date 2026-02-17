# Backtesting Engine Quick Reference

A concise reference guide for developers working with the backtesting engine.

## Table of Contents
- [Quick Start](#quick-start)
- [Core Classes](#core-classes)
- [Strategy Methods](#strategy-methods)
- [Order Types](#order-types)
- [Common Patterns](#common-patterns)
- [Error Handling](#error-handling)
- [Performance Tips](#performance-tips)

## Quick Start

### Minimal Backtest

```python
from datetime import datetime
from copilot_quant.backtest import BacktestEngine, Strategy, Order
from copilot_quant.data.providers import YFinanceProvider

class SimpleStrategy(Strategy):
    def on_data(self, timestamp, data):
        return [Order('SPY', 100, 'market', 'buy')]

engine = BacktestEngine(100000, YFinanceProvider())
engine.add_strategy(SimpleStrategy())
result = engine.run(datetime(2020, 1, 1), datetime(2023, 12, 31), ['SPY'])
print(f"Return: {result.total_return:.2%}")
```

## Core Classes

### BacktestEngine

```python
BacktestEngine(
    initial_capital: float,           # Starting capital in $
    data_provider: DataProvider,      # Data source
    commission: float = 0.001,        # 0.1% commission
    slippage: float = 0.0005          # 0.05% slippage
)

# Methods
.add_strategy(strategy)               # Register strategy
.run(start_date, end_date, symbols)   # Execute backtest
.get_portfolio_value()                # Current portfolio value
.get_positions()                      # Current positions
```

### Strategy

```python
class MyStrategy(Strategy):
    def initialize(self):
        """Called once at start (optional)"""
        pass
    
    def on_data(self, timestamp, data) -> List[Order]:
        """Called for each data point (required)"""
        return []
    
    def on_fill(self, fill):
        """Called when order fills (optional)"""
        pass
    
    def finalize(self):
        """Called once at end (optional)"""
        pass
```

### Order

```python
Order(
    symbol: str,              # Ticker (e.g., 'AAPL')
    quantity: float,          # Number of shares
    order_type: str,          # 'market' or 'limit'
    side: str,                # 'buy' or 'sell'
    limit_price: float = None # For limit orders
)
```

### Fill

```python
@dataclass
class Fill:
    order: Order              # Original order
    fill_price: float         # Execution price
    fill_quantity: float      # Shares filled
    commission: float         # Commission paid
    timestamp: datetime       # Execution time
    
    # Properties
    .total_cost               # Price × quantity + commission
    .net_proceeds             # For P&L calculation
```

### Position

```python
@dataclass
class Position:
    symbol: str               # Ticker
    quantity: float           # Shares (+ = long, - = short)
    avg_entry_price: float    # Average cost basis
    unrealized_pnl: float     # Current unrealized P&L
    realized_pnl: float       # Cumulative realized P&L
    
    # Properties
    .total_pnl                # realized + unrealized
    .market_value             # Current market value
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
    total_return: float       # As decimal (0.15 = 15%)
    trades: List[Fill]
    portfolio_history: pd.DataFrame
    
    # Methods
    .get_trade_log()          # DataFrame of all trades
    .get_equity_curve()       # Series of portfolio values
    .get_summary_stats()      # Dict of metrics
```

## Strategy Methods

### initialize()
- **When**: Called once before backtest starts
- **Use for**: Setup indicators, load config, initialize state
- **Example**:
```python
def initialize(self):
    self.sma_period = 50
    self.position = 0
```

### on_data(timestamp, data)
- **When**: Called for each new data point
- **Args**: 
  - `timestamp`: Current datetime
  - `data`: DataFrame with all data up to timestamp
- **Returns**: List of Order objects
- **Example**:
```python
def on_data(self, timestamp, data):
    if len(data) < 50:
        return []
    
    sma = data['Close'].tail(50).mean()
    current = data['Close'].iloc[-1]
    
    if current > sma:
        return [Order('SPY', 100, 'market', 'buy')]
    return []
```

### on_fill(fill)
- **When**: Called immediately after order executes
- **Args**: Fill object with execution details
- **Use for**: Track fills, update state, logging
- **Example**:
```python
def on_fill(self, fill):
    print(f"Filled: {fill.order.side} {fill.fill_quantity} @ ${fill.fill_price}")
    self.trades_count += 1
```

### finalize()
- **When**: Called once after backtest ends
- **Use for**: Cleanup, final calculations, summary
- **Example**:
```python
def finalize(self):
    print(f"Strategy executed {self.trades_count} trades")
```

## Order Types

### Market Order
Executes immediately at next price + slippage

```python
Order('AAPL', 100, 'market', 'buy')
# Fills at: market_price × (1 + slippage_rate)

Order('AAPL', 100, 'market', 'sell')
# Fills at: market_price × (1 - slippage_rate)
```

### Limit Order
Executes only if price reaches limit

```python
Order('AAPL', 100, 'limit', 'buy', limit_price=150.0)
# Fills only if market_price <= 150.0

Order('AAPL', 100, 'limit', 'sell', limit_price=160.0)
# Fills only if market_price >= 160.0
```

## Common Patterns

### Check Data Availability
```python
def on_data(self, timestamp, data):
    if len(data) < self.lookback:
        return []  # Not enough data
    # ... your logic
```

### Calculate Indicators
```python
def on_data(self, timestamp, data):
    closes = data['Close']
    
    # Simple Moving Average
    sma = closes.tail(50).mean()
    
    # Exponential Moving Average
    ema = closes.ewm(span=50).mean().iloc[-1]
    
    # Standard Deviation
    std = closes.tail(50).std()
    
    # Returns
    returns = closes.pct_change()
```

### Track Position State
```python
def initialize(self):
    self.position = 0  # 0 = flat, 1 = long, -1 = short

def on_data(self, timestamp, data):
    # Only trade when flat
    if self.position == 0:
        return [Order('SPY', 100, 'market', 'buy')]
    return []

def on_fill(self, fill):
    if fill.order.side == 'buy':
        self.position = 1
    else:
        self.position = 0
```

### Multi-Symbol Trading
```python
def on_data(self, timestamp, data):
    orders = []
    
    for symbol in self.symbols:
        symbol_data = data[data['Symbol'] == symbol]
        if len(symbol_data) > 0:
            # Analyze each symbol
            signal = self.analyze(symbol_data)
            if signal:
                orders.append(Order(symbol, 10, 'market', 'buy'))
    
    return orders
```

### Rebalancing
```python
def initialize(self):
    self.last_rebalance = None

def on_data(self, timestamp, data):
    # Rebalance monthly
    if self.last_rebalance and (timestamp - self.last_rebalance).days < 30:
        return []
    
    self.last_rebalance = timestamp
    # ... rebalancing logic
```

## Error Handling

### Data Validation
```python
def on_data(self, timestamp, data):
    # Check for empty data
    if data.empty:
        return []
    
    # Check for NaN values
    if pd.isna(data['Close'].iloc[-1]):
        return []
    
    # Check for sufficient history
    if len(data) < self.min_periods:
        return []
```

### Safe Order Creation
```python
def on_data(self, timestamp, data):
    try:
        # Your logic that might fail
        signal = self.calculate_signal(data)
        if signal:
            return [Order('SPY', 100, 'market', 'buy')]
    except Exception as e:
        print(f"Error in strategy: {e}")
        return []
```

### Logging
```python
import logging

logger = logging.getLogger(__name__)

def on_data(self, timestamp, data):
    logger.debug(f"{timestamp}: Processing data")
    
    if some_error:
        logger.warning(f"{timestamp}: Unusual condition detected")
    
    logger.info(f"{timestamp}: Generated buy signal")
```

## Performance Tips

### Avoid Look-Ahead Bias
```python
# ❌ WRONG - Uses all data
max_price = data['Close'].max()

# ✅ CORRECT - Uses only past data
max_price = data.loc[:timestamp, 'Close'].max()
```

### Vectorize Calculations
```python
# ❌ SLOW - Loop
sma = sum(closes[-50:]) / 50

# ✅ FAST - Vectorized
sma = closes.tail(50).mean()
```

### Cache Expensive Calculations
```python
def initialize(self):
    self.indicator_cache = {}

def on_data(self, timestamp, data):
    cache_key = (timestamp, len(data))
    
    if cache_key not in self.indicator_cache:
        self.indicator_cache[cache_key] = self.expensive_calculation(data)
    
    indicator = self.indicator_cache[cache_key]
```

### Limit Order Over Market
```python
# Market order - pays slippage
Order('AAPL', 100, 'market', 'buy')

# Limit order - better price control
current_price = data.iloc[-1]['Close']
Order('AAPL', 100, 'limit', 'buy', limit_price=current_price * 1.01)
```

### Consider Transaction Costs
```python
# Only trade if profit exceeds costs
min_profit = 2 * (commission_rate + slippage_rate)  # ~0.3% round trip

if expected_return > min_profit:
    return [order]
```

## Data Structure Reference

### Data DataFrame Structure

Single symbol:
```python
# Index: DatetimeIndex
# Columns: Open, High, Low, Close, Volume
data.iloc[-1]['Close']  # Latest close price
data['Close'].tail(20)  # Last 20 closes
```

Multiple symbols:
```python
# With Symbol column
spy_data = data[data['Symbol'] == 'SPY']

# Or multi-index columns
data[('Close', 'SPY')]
```

### Portfolio History DataFrame

```python
# Columns:
#   - timestamp: datetime
#   - portfolio_value: float
#   - cash: float
#   - positions_value: float
#   - num_positions: int
#   - position_{symbol}: float (for each symbol)
#   - value_{symbol}: float (market value)

result.portfolio_history['portfolio_value']
result.portfolio_history['cash']
```

### Trade Log DataFrame

```python
# Columns:
#   - timestamp (index): datetime
#   - symbol: str
#   - side: str (buy/sell)
#   - quantity: float
#   - price: float
#   - commission: float
#   - total_cost: float

result.get_trade_log()
```

## Configuration Reference

### Engine Configuration
```python
engine = BacktestEngine(
    initial_capital=100000,              # Starting capital
    data_provider=YFinanceProvider(),    # Data source
    commission=0.001,                    # 0.1% commission
    slippage=0.0005                      # 0.05% slippage
)
```

### Common Commission Rates
- **Retail brokers**: 0.0% - 0.5% per trade
- **Interactive Brokers**: ~0.0005% ($0.005/share)
- **TD Ameritrade**: ~0.0% (commission-free)
- **Conservative estimate**: 0.1% (0.001)

### Common Slippage Rates
- **Large cap stocks**: 0.01% - 0.05%
- **Small cap stocks**: 0.1% - 0.5%
- **Conservative estimate**: 0.05% (0.0005)

## Common Gotchas

### 1. Modifying Data
```python
# ❌ Don't modify the data DataFrame
data['MyIndicator'] = calculate_indicator(data)

# ✅ Use local variables
my_indicator = calculate_indicator(data)
```

### 2. Position Tracking
```python
# ❌ Don't track positions manually
self.positions['SPY'] += 100

# ✅ Let the engine handle positions
# Query them if needed via on_fill() callback
```

### 3. Timezone Issues
```python
# Make sure dates are timezone-aware or naive consistently
start_date = datetime(2020, 1, 1)  # Naive
# data timestamps should also be naive
```

### 4. Order Timing
```python
# Orders execute at NEXT available price
# Not at current timestamp price
# Account for this in your logic
```

### 5. Data Alignment
```python
# Multi-symbol data may have different timestamps
# Check for data availability before using
if len(symbol_data) > 0:
    current_price = symbol_data.iloc[-1]['Close']
```

## Testing Quick Reference

### Unit Test Template
```python
import pytest
from datetime import datetime
import pandas as pd

def test_strategy():
    strategy = MyStrategy()
    
    # Create test data
    dates = pd.date_range('2020-01-01', periods=100)
    data = pd.DataFrame({
        'Close': range(100, 200),
        'Open': range(100, 200),
        'High': range(101, 201),
        'Low': range(99, 199),
        'Volume': [1000000] * 100
    }, index=dates)
    
    # Test on_data
    orders = strategy.on_data(dates[-1], data)
    
    # Assertions
    assert isinstance(orders, list)
    assert all(isinstance(o, Order) for o in orders)
```

### Integration Test
```python
def test_full_backtest():
    engine = BacktestEngine(
        initial_capital=100000,
        data_provider=MockDataProvider()
    )
    
    engine.add_strategy(MyStrategy())
    
    result = engine.run(
        start_date=datetime(2020, 1, 1),
        end_date=datetime(2020, 12, 31),
        symbols=['SPY']
    )
    
    assert result.final_capital > 0
    assert len(result.trades) >= 0
```

## Resources

- [Architecture](architecture.md) - System design
- [Usage Guide](usage_guide.md) - Detailed examples
- [Design Decisions](design_decisions.md) - Rationale
- [API Reference](backtesting.md) - Complete API

---

**Quick Tip**: Start with a simple strategy, test with mock data, then add complexity gradually.
