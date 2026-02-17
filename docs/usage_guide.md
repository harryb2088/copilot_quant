# Backtesting Engine Usage Guide

## Quick Start

### Basic Backtest in 5 Minutes

```python
from datetime import datetime
from copilot_quant.backtest import BacktestEngine, Strategy, Order
from copilot_quant.data.providers import YFinanceProvider

# 1. Define your strategy
class BuyAndHold(Strategy):
    def __init__(self, symbol='SPY', quantity=100):
        super().__init__()
        self.symbol = symbol
        self.quantity = quantity
        self.invested = False
    
    def on_data(self, timestamp, data):
        # Buy once at the start
        if not self.invested:
            self.invested = True
            return [Order(
                symbol=self.symbol,
                quantity=self.quantity,
                order_type='market',
                side='buy'
            )]
        return []

# 2. Create the engine
engine = BacktestEngine(
    initial_capital=100000,
    data_provider=YFinanceProvider(),
    commission=0.001,
    slippage=0.0005
)

# 3. Add strategy
engine.add_strategy(BuyAndHold(symbol='SPY', quantity=100))

# 4. Run backtest
result = engine.run(
    start_date=datetime(2020, 1, 1),
    end_date=datetime(2023, 12, 31),
    symbols=['SPY']
)

# 5. View results
print(f"Total Return: {result.total_return:.2%}")
print(f"Final Capital: ${result.final_capital:,.2f}")
print(f"Number of Trades: {len(result.trades)}")
```

## Strategy Development

### Strategy Lifecycle

Every strategy goes through four phases:

```python
class MyStrategy(Strategy):
    def initialize(self):
        """
        Called once before backtest starts.
        
        Use this to:
        - Initialize indicators
        - Load configuration
        - Set up state variables
        """
        self.sma_period = 50
        self.position = 0
        self.trades_count = 0
    
    def on_data(self, timestamp, data):
        """
        Called for each new data point.
        
        Args:
            timestamp: Current datetime
            data: All data up to current timestamp
        
        Returns:
            List of Order objects to execute
        """
        orders = []
        
        # Your trading logic here
        # ...
        
        return orders
    
    def on_fill(self, fill):
        """
        Called when an order is filled.
        
        Use this to:
        - Track fills
        - Update internal state
        - Log executions
        """
        self.trades_count += 1
        print(f"Order filled: {fill.order.side} {fill.fill_quantity} @ ${fill.fill_price}")
    
    def finalize(self):
        """
        Called once after backtest ends.
        
        Use this to:
        - Calculate final metrics
        - Cleanup resources
        - Log summary
        """
        print(f"Strategy completed {self.trades_count} trades")
```

### Example Strategies

#### 1. Moving Average Crossover

```python
class MovingAverageCrossover(Strategy):
    """
    Classic moving average crossover strategy.
    
    Buy when short MA crosses above long MA.
    Sell when short MA crosses below long MA.
    """
    
    def __init__(self, symbol='SPY', short_window=50, long_window=200, quantity=100):
        super().__init__()
        self.symbol = symbol
        self.short_window = short_window
        self.long_window = long_window
        self.quantity = quantity
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
                quantity=self.quantity,
                order_type='market',
                side='buy'
            ))
            self.position = 1
        
        # Death cross - sell signal
        elif short_ma < long_ma and self.position > 0:
            orders.append(Order(
                symbol=self.symbol,
                quantity=self.quantity,
                order_type='market',
                side='sell'
            ))
            self.position = 0
        
        return orders
```

#### 2. Mean Reversion

```python
class MeanReversion(Strategy):
    """
    Mean reversion strategy using Bollinger Bands.
    
    Buy when price touches lower band.
    Sell when price touches upper band.
    """
    
    def __init__(self, symbol='SPY', period=20, num_std=2, quantity=100):
        super().__init__()
        self.symbol = symbol
        self.period = period
        self.num_std = num_std
        self.quantity = quantity
        self.position = 0
    
    def on_data(self, timestamp, data):
        if len(data) < self.period:
            return []
        
        # Calculate Bollinger Bands
        closes = data['Close'].tail(self.period)
        sma = closes.mean()
        std = closes.std()
        
        upper_band = sma + (self.num_std * std)
        lower_band = sma - (self.num_std * std)
        
        current_price = closes.iloc[-1]
        orders = []
        
        # Buy at lower band
        if current_price <= lower_band and self.position == 0:
            orders.append(Order(
                symbol=self.symbol,
                quantity=self.quantity,
                order_type='market',
                side='buy'
            ))
            self.position = 1
        
        # Sell at upper band
        elif current_price >= upper_band and self.position > 0:
            orders.append(Order(
                symbol=self.symbol,
                quantity=self.quantity,
                order_type='market',
                side='sell'
            ))
            self.position = 0
        
        return orders
```

#### 3. Momentum Strategy

```python
class MomentumStrategy(Strategy):
    """
    Momentum strategy based on relative strength.
    
    Buy the strongest performers.
    Rotate holdings monthly.
    """
    
    def __init__(self, symbols, top_n=5, lookback=90, quantity=10):
        super().__init__()
        self.symbols = symbols
        self.top_n = top_n
        self.lookback = lookback
        self.quantity = quantity
        self.last_rebalance = None
        self.holdings = set()
    
    def on_data(self, timestamp, data):
        # Rebalance monthly
        if self.last_rebalance and (timestamp - self.last_rebalance).days < 30:
            return []
        
        orders = []
        
        # Calculate momentum for each symbol
        momentum_scores = {}
        for symbol in self.symbols:
            symbol_data = data[data['Symbol'] == symbol]
            if len(symbol_data) >= self.lookback:
                old_price = symbol_data.iloc[-self.lookback]['Close']
                new_price = symbol_data.iloc[-1]['Close']
                momentum_scores[symbol] = (new_price - old_price) / old_price
        
        # Select top N by momentum
        top_symbols = sorted(
            momentum_scores.keys(),
            key=lambda s: momentum_scores[s],
            reverse=True
        )[:self.top_n]
        
        # Sell holdings not in top N
        for symbol in self.holdings:
            if symbol not in top_symbols:
                orders.append(Order(
                    symbol=symbol,
                    quantity=self.quantity,
                    order_type='market',
                    side='sell'
                ))
        
        # Buy top N
        for symbol in top_symbols:
            if symbol not in self.holdings:
                orders.append(Order(
                    symbol=symbol,
                    quantity=self.quantity,
                    order_type='market',
                    side='buy'
                ))
        
        self.holdings = set(top_symbols)
        self.last_rebalance = timestamp
        
        return orders
```

#### 4. Pairs Trading

```python
class PairsTradingStrategy(Strategy):
    """
    Statistical arbitrage using pairs trading.
    
    Trade based on spread between correlated assets.
    """
    
    def __init__(self, symbol1='SPY', symbol2='IWM', 
                 lookback=60, entry_z=2.0, exit_z=0.5, quantity=100):
        super().__init__()
        self.symbol1 = symbol1
        self.symbol2 = symbol2
        self.lookback = lookback
        self.entry_z = entry_z
        self.exit_z = exit_z
        self.quantity = quantity
        self.position = 0  # 1 = long spread, -1 = short spread
    
    def on_data(self, timestamp, data):
        if len(data) < self.lookback:
            return []
        
        # Get price series
        prices1 = data[data['Symbol'] == self.symbol1]['Close'].tail(self.lookback)
        prices2 = data[data['Symbol'] == self.symbol2]['Close'].tail(self.lookback)
        
        if len(prices1) != self.lookback or len(prices2) != self.lookback:
            return []
        
        # Calculate spread
        spread = prices1.values - prices2.values
        mean_spread = spread.mean()
        std_spread = spread.std()
        
        if std_spread == 0:
            return []
        
        current_spread = spread[-1]
        z_score = (current_spread - mean_spread) / std_spread
        
        orders = []
        
        # Entry signals
        if z_score > self.entry_z and self.position == 0:
            # Spread too high - short it
            orders.append(Order(self.symbol1, self.quantity, 'market', 'sell'))
            orders.append(Order(self.symbol2, self.quantity, 'market', 'buy'))
            self.position = -1
        
        elif z_score < -self.entry_z and self.position == 0:
            # Spread too low - long it
            orders.append(Order(self.symbol1, self.quantity, 'market', 'buy'))
            orders.append(Order(self.symbol2, self.quantity, 'market', 'sell'))
            self.position = 1
        
        # Exit signals
        elif abs(z_score) < self.exit_z and self.position != 0:
            # Close position
            if self.position == 1:
                orders.append(Order(self.symbol1, self.quantity, 'market', 'sell'))
                orders.append(Order(self.symbol2, self.quantity, 'market', 'buy'))
            else:
                orders.append(Order(self.symbol1, self.quantity, 'market', 'buy'))
                orders.append(Order(self.symbol2, self.quantity, 'market', 'sell'))
            self.position = 0
        
        return orders
```

## Working with Data

### Using Different Data Providers

```python
# Yahoo Finance (default)
from copilot_quant.data.providers import YFinanceProvider
provider = YFinanceProvider()

# Mock provider for testing
from tests.test_data.mock_prediction_markets.mock_data import MockDataProvider
provider = MockDataProvider()

# CSV provider (custom)
class CSVDataProvider(DataProvider):
    def __init__(self, data_dir):
        self.data_dir = data_dir
    
    def get_historical_data(self, symbol, start_date, end_date, interval='1d'):
        filepath = f"{self.data_dir}/{symbol}.csv"
        df = pd.read_csv(filepath, index_col='Date', parse_dates=True)
        return df.loc[start_date:end_date]
```

### Handling Multiple Symbols

```python
# Run backtest with multiple symbols
result = engine.run(
    start_date=datetime(2020, 1, 1),
    end_date=datetime(2023, 12, 31),
    symbols=['SPY', 'QQQ', 'IWM']
)

# In your strategy, filter data by symbol
def on_data(self, timestamp, data):
    spy_data = data[data['Symbol'] == 'SPY']
    qqq_data = data[data['Symbol'] == 'QQQ']
    
    # Compare performance
    if len(spy_data) > 0 and len(qqq_data) > 0:
        spy_return = spy_data.iloc[-1]['Close'] / spy_data.iloc[0]['Close'] - 1
        qqq_return = qqq_data.iloc[-1]['Close'] / qqq_data.iloc[0]['Close'] - 1
        
        # Buy the better performer
        if spy_return > qqq_return:
            return [Order('SPY', 100, 'market', 'buy')]
        else:
            return [Order('QQQ', 100, 'market', 'buy')]
    
    return []
```

## Order Management

### Market Orders

```python
# Simple market order
order = Order(
    symbol='AAPL',
    quantity=100,
    order_type='market',
    side='buy'
)

# The order will execute at:
# - Next available price
# - Plus slippage (e.g., +0.05% for buys, -0.05% for sells)
# - Plus commission (e.g., 0.1% of trade value)
```

### Limit Orders

```python
# Limit order - only execute if price reaches limit
order = Order(
    symbol='AAPL',
    quantity=100,
    order_type='limit',
    side='buy',
    limit_price=150.0  # Will only buy if price <= $150
)

# For sells, reverse logic:
order = Order(
    symbol='AAPL',
    quantity=100,
    order_type='limit',
    side='sell',
    limit_price=160.0  # Will only sell if price >= $160
)
```

### Position Sizing

```python
class PositionSizedStrategy(Strategy):
    """Example of dynamic position sizing."""
    
    def __init__(self, risk_per_trade=0.02):
        super().__init__()
        self.risk_per_trade = risk_per_trade
    
    def calculate_position_size(self, capital, price, stop_loss_pct):
        """Calculate position size based on risk."""
        risk_amount = capital * self.risk_per_trade
        risk_per_share = price * stop_loss_pct
        position_size = int(risk_amount / risk_per_share)
        return position_size
    
    def on_data(self, timestamp, data):
        current_price = data.iloc[-1]['Close']
        portfolio_value = 100000  # Would get from engine in real impl
        
        # Risk 2% of capital with 5% stop loss
        quantity = self.calculate_position_size(
            capital=portfolio_value,
            price=current_price,
            stop_loss_pct=0.05
        )
        
        return [Order('SPY', quantity, 'market', 'buy')]
```

## Results Analysis

### Basic Metrics

```python
result = engine.run(...)

# Performance metrics
print(f"Total Return: {result.total_return:.2%}")
print(f"Initial Capital: ${result.initial_capital:,.2f}")
print(f"Final Capital: ${result.final_capital:,.2f}")
print(f"Profit/Loss: ${result.final_capital - result.initial_capital:,.2f}")

# Trading activity
print(f"Number of Trades: {len(result.trades)}")
print(f"Start Date: {result.start_date.date()}")
print(f"End Date: {result.end_date.date()}")
print(f"Days: {(result.end_date - result.start_date).days}")
```

### Trade Log

```python
# Get detailed trade log
trade_log = result.get_trade_log()
print(trade_log)

# Output:
#                      symbol side  quantity   price  commission  total_cost
# timestamp                                                                  
# 2020-01-02 00:00:00    SPY  buy     100.0  323.87      32.387   32419.287
# 2020-06-15 00:00:00    SPY sell     100.0  311.28      31.128   31096.872
# ...

# Filter trades
buy_trades = trade_log[trade_log['side'] == 'buy']
sell_trades = trade_log[trade_log['side'] == 'sell']

# Calculate metrics
total_commission = trade_log['commission'].sum()
average_trade_size = trade_log['quantity'].mean()
```

### Equity Curve

```python
# Get equity curve
equity_curve = result.get_equity_curve()

# Plot with matplotlib
import matplotlib.pyplot as plt

plt.figure(figsize=(12, 6))
plt.plot(equity_curve.index, equity_curve.values)
plt.title('Portfolio Value Over Time')
plt.xlabel('Date')
plt.ylabel('Portfolio Value ($)')
plt.grid(True)
plt.show()

# Calculate drawdown
running_max = equity_curve.expanding().max()
drawdown = (equity_curve - running_max) / running_max
max_drawdown = drawdown.min()
print(f"Maximum Drawdown: {max_drawdown:.2%}")
```

### Portfolio History

```python
# Get complete portfolio history
history = result.portfolio_history
print(history.head())

# Output:
#             timestamp  portfolio_value      cash  positions_value  num_positions
# 0  2020-01-02 00:00:00      100000.00  67580.71         32419.29             1
# 1  2020-01-03 00:00:00      100123.45  67580.71         32542.74             1
# ...

# Analyze position sizes over time
if 'position_SPY' in history.columns:
    plt.plot(history['timestamp'], history['position_SPY'])
    plt.title('SPY Position Size Over Time')
    plt.show()
```

## Advanced Patterns

### Custom Indicators

```python
class RSIStrategy(Strategy):
    """Strategy using custom RSI indicator."""
    
    def __init__(self, symbol='SPY', rsi_period=14, oversold=30, overbought=70):
        super().__init__()
        self.symbol = symbol
        self.rsi_period = rsi_period
        self.oversold = oversold
        self.overbought = overbought
        self.position = 0
    
    def calculate_rsi(self, prices):
        """Calculate RSI indicator."""
        if len(prices) < self.rsi_period + 1:
            return None
        
        deltas = prices.diff()
        gains = deltas.where(deltas > 0, 0)
        losses = -deltas.where(deltas < 0, 0)
        
        avg_gain = gains.rolling(window=self.rsi_period).mean()
        avg_loss = losses.rolling(window=self.rsi_period).mean()
        
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        
        return rsi.iloc[-1]
    
    def on_data(self, timestamp, data):
        if len(data) < self.rsi_period + 1:
            return []
        
        rsi = self.calculate_rsi(data['Close'])
        if rsi is None:
            return []
        
        orders = []
        
        # Buy when oversold
        if rsi < self.oversold and self.position == 0:
            orders.append(Order(self.symbol, 100, 'market', 'buy'))
            self.position = 1
        
        # Sell when overbought
        elif rsi > self.overbought and self.position > 0:
            orders.append(Order(self.symbol, 100, 'market', 'sell'))
            self.position = 0
        
        return orders
```

### State Management

```python
class StatefulStrategy(Strategy):
    """Example of managing complex state."""
    
    def initialize(self):
        self.state = {
            'position': 0,
            'entry_price': None,
            'stop_loss': None,
            'take_profit': None,
            'trade_count': 0,
            'win_count': 0,
            'current_streak': 0
        }
    
    def on_data(self, timestamp, data):
        current_price = data.iloc[-1]['Close']
        orders = []
        
        # Check stop loss / take profit
        if self.state['position'] > 0:
            if current_price <= self.state['stop_loss']:
                # Stop loss hit
                orders.append(Order('SPY', 100, 'market', 'sell'))
                self.state['position'] = 0
                self.state['current_streak'] = 0
            
            elif current_price >= self.state['take_profit']:
                # Take profit hit
                orders.append(Order('SPY', 100, 'market', 'sell'))
                self.state['position'] = 0
                self.state['win_count'] += 1
                self.state['current_streak'] += 1
        
        return orders
    
    def on_fill(self, fill):
        if fill.order.side == 'buy':
            self.state['entry_price'] = fill.fill_price
            self.state['stop_loss'] = fill.fill_price * 0.95  # 5% stop
            self.state['take_profit'] = fill.fill_price * 1.10  # 10% target
        
        self.state['trade_count'] += 1
    
    def finalize(self):
        win_rate = self.state['win_count'] / self.state['trade_count']
        print(f"Strategy completed with {win_rate:.1%} win rate")
```

## Testing Strategies

### Unit Testing

```python
import pytest
from datetime import datetime
import pandas as pd

def test_strategy_initialization():
    """Test strategy initializes correctly."""
    strategy = MyStrategy(param1=10)
    assert strategy.param1 == 10

def test_strategy_generates_orders():
    """Test strategy generates valid orders."""
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
    
    # Call on_data
    orders = strategy.on_data(dates[-1], data)
    
    # Verify
    assert isinstance(orders, list)
    if len(orders) > 0:
        assert isinstance(orders[0], Order)

def test_strategy_with_mock_engine():
    """Test strategy with mock backtest engine."""
    from tests.test_data.mock_prediction_markets.mock_data import MockDataProvider
    
    engine = BacktestEngine(
        initial_capital=100000,
        data_provider=MockDataProvider(),
        commission=0.001,
        slippage=0.0005
    )
    
    engine.add_strategy(MyStrategy())
    
    result = engine.run(
        start_date=datetime(2020, 1, 1),
        end_date=datetime(2020, 12, 31),
        symbols=['SPY']
    )
    
    # Verify results
    assert result.final_capital > 0
    assert len(result.trades) >= 0
```

## Best Practices

### 1. Avoid Look-Ahead Bias

```python
# ❌ WRONG - Uses future data
def on_data(self, timestamp, data):
    max_price = data['Close'].max()  # Includes all data!
    
# ✅ CORRECT - Uses only past data
def on_data(self, timestamp, data):
    max_price = data.loc[:timestamp, 'Close'].max()
```

### 2. Handle Missing Data

```python
def on_data(self, timestamp, data):
    # Check for sufficient data
    if len(data) < self.lookback_period:
        return []
    
    # Check for NaN values
    if pd.isna(data['Close'].iloc[-1]):
        return []
    
    # Your logic here
    ...
```

### 3. Consider Transaction Costs

```python
# Don't trade too frequently
min_profit_threshold = 2 * (commission_rate + slippage_rate)

if expected_return > min_profit_threshold:
    # Only trade if expected profit exceeds round-trip costs
    return [order]
```

### 4. Use Limit Orders for Better Fills

```python
# Market order - might get bad price
market_order = Order('AAPL', 100, 'market', 'buy')

# Limit order - control maximum price
current_price = data.iloc[-1]['Close']
limit_order = Order('AAPL', 100, 'limit', 'buy', limit_price=current_price * 1.01)
```

### 5. Log Important Events

```python
import logging

logger = logging.getLogger(__name__)

def on_data(self, timestamp, data):
    signal = self.calculate_signal(data)
    
    logger.debug(f"{timestamp}: Signal = {signal:.2f}")
    
    if signal > self.threshold:
        logger.info(f"{timestamp}: BUY signal generated")
        return [Order('SPY', 100, 'market', 'buy')]
    
    return []
```

## Conclusion

The backtesting engine provides a flexible framework for developing and testing trading strategies. Key takeaways:

1. **Start Simple**: Begin with basic strategies and add complexity gradually
2. **Test Thoroughly**: Use unit tests and mock data before live backtests
3. **Be Realistic**: Account for transaction costs and avoid look-ahead bias
4. **Iterate Quickly**: The engine makes it easy to test variations
5. **Analyze Results**: Use the comprehensive results to improve strategies

For more details, see:
- [Architecture Documentation](architecture.md)
- [API Reference](backtesting.md)
- [Design Decisions](design_decisions.md)
