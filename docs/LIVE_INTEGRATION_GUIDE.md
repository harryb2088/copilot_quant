# Live Data & Execution Integration Guide

## Overview

This document describes the integration of live IBKR data and execution with the strategy engine, enabling strategies to run in both backtest and live trading modes with minimal code changes.

## Architecture

### Components

The integration consists of three main adapter components:

1. **LiveDataFeedAdapter** (`copilot_quant/brokers/live_data_adapter.py`)
   - Implements `IDataFeed` interface from backtest engine
   - Provides real-time and historical data via IBKR
   - Handles reconnection and fallback scenarios
   - Caches recent data for resilience

2. **LiveBrokerAdapter** (`copilot_quant/brokers/live_broker_adapter.py`)
   - Implements `IBroker` interface from backtest engine
   - Executes orders through IBKR
   - Manages positions and buying power checks
   - Calculates commissions and slippage

3. **LiveStrategyEngine** (`copilot_quant/backtest/live_engine.py`)
   - Orchestrates live strategy execution
   - Processes real-time data updates
   - Manages strategy lifecycle
   - Handles errors and reconnection

### Design Pattern: Adapter Pattern

The integration uses the **Adapter Pattern** to bridge the gap between:
- **Target Interface**: Backtest engine interfaces (`IDataFeed`, `IBroker`)
- **Adaptee**: IBKR live modules (`IBKRLiveDataFeed`, `IBKRBroker`)
- **Adapter**: New adapter classes that implement target interfaces using adaptee

This allows strategies written for backtesting to run in live mode without modification.

```
┌─────────────────────────────────────────────────────────────┐
│                    Strategy (User Code)                     │
│                  Uses IDataFeed & IBroker                   │
└────────────────────────┬────────────────────────────────────┘
                         │
         ┌───────────────┴───────────────┐
         │                               │
         ▼                               ▼
┌──────────────────┐            ┌──────────────────┐
│ BacktestEngine   │            │ LiveStrategyEngine│
│ (Backtest Mode)  │            │  (Live Mode)     │
└────────┬─────────┘            └────────┬─────────┘
         │                               │
         ▼                               ▼
┌──────────────────┐            ┌──────────────────┐
│ YFinanceProvider │            │ LiveDataAdapter  │
│ SimpleBroker     │            │ LiveBrokerAdapter│
└──────────────────┘            └────────┬─────────┘
                                         │
                                         ▼
                                ┌──────────────────┐
                                │ IBKR Live Modules│
                                │ (ib_insync API)  │
                                └──────────────────┘
```

## Usage Examples

### Basic Live Trading

```python
from copilot_quant.backtest.live_engine import LiveStrategyEngine
from copilot_quant.strategies.my_strategy import MyStrategy

# Initialize live engine
engine = LiveStrategyEngine(
    paper_trading=True,  # Use paper trading for testing
    commission=0.001,    # 0.1% commission
    slippage=0.0005,     # 0.05% slippage
    update_interval=60.0 # Update every 60 seconds
)

# Add your strategy
strategy = MyStrategy()
engine.add_strategy(strategy)

# Connect to IBKR
if engine.connect():
    print("Connected to IBKR")
    
    # Start live trading
    engine.start(
        symbols=['AAPL', 'MSFT'],
        lookback_days=30,
        data_interval='1d'
    )
    
    # Let it run (or use signal handlers for graceful shutdown)
    try:
        while True:
            time.sleep(60)
            
            # Monitor performance
            summary = engine.get_performance_summary()
            print(f"Account Value: ${summary['account_value']:,.2f}")
            print(f"Positions: {summary['positions']}")
            print(f"Fills: {summary['total_fills']}")
    
    except KeyboardInterrupt:
        print("Stopping...")
    
    finally:
        # Stop and disconnect
        engine.stop()
        engine.disconnect()
```

### Using Adapters Directly

If you need more control, you can use the adapters directly:

```python
from copilot_quant.brokers.live_data_adapter import LiveDataFeedAdapter
from copilot_quant.brokers.live_broker_adapter import LiveBrokerAdapter
from copilot_quant.backtest.orders import Order
from datetime import datetime

# Initialize adapters
data_feed = LiveDataFeedAdapter(paper_trading=True)
broker = LiveBrokerAdapter(paper_trading=True)

# Connect
if data_feed.connect() and broker.connect():
    
    # Get historical data (backtest-compatible format)
    hist_data = data_feed.get_historical_data(
        symbol='AAPL',
        start_date=datetime(2024, 1, 1),
        interval='1d'
    )
    print(f"Loaded {len(hist_data)} bars")
    
    # Subscribe to real-time data
    data_feed.subscribe(['AAPL'])
    
    # Get latest price
    price = data_feed.get_latest_price('AAPL')
    print(f"Current price: ${price:.2f}")
    
    # Create and execute order
    order = Order(
        symbol='AAPL',
        quantity=10,
        order_type='market',
        side='buy'
    )
    
    # Check buying power
    if broker.check_buying_power(order, price):
        # Execute order
        fill = broker.execute_order(order, price, datetime.now())
        if fill:
            print(f"Order filled @ ${fill.fill_price:.2f}")
    
    # Get positions
    positions = broker.get_positions()
    for symbol, position in positions.items():
        print(f"{symbol}: {position.quantity} shares")
    
    # Disconnect
    data_feed.disconnect()
    broker.disconnect()
```

### Strategy Compatibility

Strategies designed for backtesting work seamlessly in live mode:

```python
from copilot_quant.backtest.strategy import Strategy
from copilot_quant.backtest.orders import Order
from datetime import datetime
import pandas as pd

class SimpleMovingAverage(Strategy):
    """
    Simple moving average crossover strategy.
    Works in both backtest and live mode.
    """
    
    def initialize(self):
        self.fast_period = 10
        self.slow_period = 30
        self.position = None
    
    def on_data(self, timestamp: datetime, data: pd.DataFrame) -> list:
        orders = []
        
        # Calculate moving averages
        if 'Close' in data.columns:
            close_prices = data['Close']
        else:
            # Handle multi-symbol data
            close_prices = data[('Close', 'AAPL')]
        
        if len(close_prices) < self.slow_period:
            return orders
        
        fast_ma = close_prices.tail(self.fast_period).mean()
        slow_ma = close_prices.tail(self.slow_period).mean()
        
        # Generate signals
        if fast_ma > slow_ma and self.position is None:
            # Buy signal
            orders.append(Order(
                symbol='AAPL',
                quantity=10,
                order_type='market',
                side='buy'
            ))
            self.position = 'long'
        
        elif fast_ma < slow_ma and self.position == 'long':
            # Sell signal
            orders.append(Order(
                symbol='AAPL',
                quantity=10,
                order_type='market',
                side='sell'
            ))
            self.position = None
        
        return orders
    
    def on_fill(self, fill):
        print(f"Fill: {fill.order.side} {fill.fill_quantity} @ ${fill.fill_price:.2f}")

# Use in backtest mode
from copilot_quant.backtest.engine import BacktestEngine
from copilot_quant.data.providers import YFinanceProvider

backtest_engine = BacktestEngine(
    initial_capital=100000,
    data_provider=YFinanceProvider(),
    commission=0.001
)
backtest_engine.add_strategy(SimpleMovingAverage())
result = backtest_engine.run(
    start_date=datetime(2023, 1, 1),
    end_date=datetime(2023, 12, 31),
    symbols=['AAPL']
)

# Use in live mode (same strategy!)
live_engine = LiveStrategyEngine(paper_trading=True)
live_engine.add_strategy(SimpleMovingAverage())
live_engine.connect()
live_engine.start(symbols=['AAPL'])
```

## Error Handling Strategies

### 1. Connection Loss Handling

The adapters implement automatic reconnection:

```python
# LiveDataFeedAdapter automatically attempts reconnection
adapter = LiveDataFeedAdapter(paper_trading=True)
adapter.connect()

# If connection is lost, adapter enters fallback mode
if adapter.is_fallback_mode():
    print("Using cached data due to connection loss")

# Manual reconnection attempt
if adapter.reconnect():
    print("Reconnected successfully")
```

### 2. Data Fallback

When live data feed disconnects, cached historical data is used:

```python
# Enable caching (enabled by default)
adapter = LiveDataFeedAdapter(
    paper_trading=True,
    enable_cache=True,
    cache_size=1000  # Keep last 1000 bars per symbol
)

# Historical data is automatically cached
hist_data = adapter.get_historical_data('AAPL', interval='1d')

# If connection lost, cached data is returned as fallback
current_data = adapter.get_historical_data('AAPL', interval='1d')
```

### 3. Order Execution Errors

The broker adapter handles order execution errors:

```python
# Check buying power before order execution
if broker.check_buying_power(order, price):
    fill = broker.execute_order(order, price, timestamp)
    if fill:
        print("Order executed")
    else:
        print("Order rejected or not filled")
else:
    print("Insufficient buying power")

# Register error callback
def on_error(order_record, error_msg):
    print(f"Order error: {error_msg}")
    # Implement custom error handling

broker.register_error_callback(on_error)
```

### 4. Strategy Errors

The live engine catches and logs strategy errors without stopping:

```python
# Errors in strategy.on_data() are caught and logged
# Engine continues running

# Check errors
summary = engine.get_performance_summary()
print(f"Total errors: {summary['total_errors']}")

# Access error log
for error in engine.errors:
    print(f"{error['timestamp']}: {error['error']}")
```

## Configuration

### Environment Variables

The adapters respect the same environment variables as IBKR modules:

```bash
# .env file
IB_HOST=127.0.0.1
IB_PORT=7497              # Paper trading TWS
IB_CLIENT_ID=1
IB_PAPER_ACCOUNT=DU12345  # Optional
```

### Connection Parameters

```python
# Explicit parameters override environment variables
adapter = LiveDataFeedAdapter(
    paper_trading=True,
    host='127.0.0.1',
    port=7497,
    client_id=1,
    use_gateway=False  # False = TWS, True = IB Gateway
)
```

### Port Reference

| Mode | Application | Port |
|------|------------|------|
| Paper | TWS | 7497 |
| Live | TWS | 7496 |
| Paper | IB Gateway | 4002 |
| Live | IB Gateway | 4001 |

## Best Practices

### 1. Start with Paper Trading

Always test strategies in paper trading mode first:

```python
engine = LiveStrategyEngine(paper_trading=True)
```

### 2. Implement Graceful Shutdown

Use signal handlers for clean shutdown:

```python
import signal

def signal_handler(sig, frame):
    print("Shutting down...")
    engine.stop()
    engine.disconnect()
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)
```

### 3. Monitor Connection Status

Periodically check connection:

```python
if not engine.is_connected():
    print("WARNING: Lost connection to IBKR")
    # Implement alerting
```

### 4. Log Everything

Enable comprehensive logging:

```python
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('live_trading.log'),
        logging.StreamHandler()
    ]
)
```

### 5. Set Reasonable Update Intervals

Balance between responsiveness and resource usage:

```python
engine = LiveStrategyEngine(
    update_interval=60.0  # 60 seconds for daily strategies
    # update_interval=1.0 for high-frequency strategies
)
```

### 6. Handle Market Hours

Check if market is open before trading:

```python
from datetime import datetime, time

def is_market_open():
    now = datetime.now()
    # NYSE: 9:30 AM - 4:00 PM ET
    market_open = time(9, 30)
    market_close = time(16, 0)
    
    if now.weekday() >= 5:  # Weekend
        return False
    
    current_time = now.time()
    return market_open <= current_time <= market_close

# In your strategy or engine loop
if not is_market_open():
    return []  # No orders outside market hours
```

## Testing

### Unit Testing Adapters

```python
import unittest
from copilot_quant.brokers.live_data_adapter import LiveDataFeedAdapter

class TestLiveDataAdapter(unittest.TestCase):
    
    def setUp(self):
        self.adapter = LiveDataFeedAdapter(paper_trading=True)
    
    def test_connect(self):
        # Test connection
        success = self.adapter.connect(timeout=30)
        self.assertTrue(success)
        self.assertTrue(self.adapter.is_connected())
    
    def test_historical_data(self):
        self.adapter.connect()
        
        # Test historical data retrieval
        data = self.adapter.get_historical_data(
            symbol='AAPL',
            start_date=datetime(2024, 1, 1),
            interval='1d'
        )
        
        self.assertIsNotNone(data)
        self.assertFalse(data.empty)
        self.assertIn('Close', data.columns)
    
    def tearDown(self):
        self.adapter.disconnect()
```

### Integration Testing

Test the full integration with a simple strategy:

```python
def test_live_integration():
    """Test complete live integration flow"""
    
    # Create simple test strategy
    class TestStrategy(Strategy):
        def on_data(self, timestamp, data):
            return []  # No orders for testing
    
    # Initialize engine
    engine = LiveStrategyEngine(paper_trading=True)
    engine.add_strategy(TestStrategy())
    
    # Connect
    assert engine.connect(), "Failed to connect"
    
    # Start
    assert engine.start(['AAPL']), "Failed to start"
    
    # Run briefly
    time.sleep(10)
    
    # Check status
    summary = engine.get_performance_summary()
    assert summary['is_running'], "Engine should be running"
    assert summary['is_connected'], "Should be connected"
    
    # Stop
    engine.stop()
    engine.disconnect()
    
    print("✓ Integration test passed")
```

## Troubleshooting

### Connection Issues

**Problem**: Cannot connect to IBKR

**Solutions**:
1. Verify TWS/IB Gateway is running
2. Check API settings in TWS (Enable ActiveX and Socket Clients)
3. Verify port number matches your setup
4. Check firewall settings
5. Ensure client_id is unique

### Data Issues

**Problem**: No historical data returned

**Solutions**:
1. Check symbol is valid
2. Verify market data subscriptions in IBKR account
3. Check date range is valid
4. Try different interval

### Order Execution Issues

**Problem**: Orders not executing

**Solutions**:
1. Check buying power
2. Verify market is open
3. Check order parameters are valid
4. Review IBKR order logs
5. Check for error callbacks

### Performance Issues

**Problem**: High CPU usage

**Solutions**:
1. Increase update_interval
2. Reduce number of symbols
3. Disable verbose logging
4. Optimize strategy logic

## API Reference

See individual module docstrings for complete API documentation:

- `LiveDataFeedAdapter`: `copilot_quant/brokers/live_data_adapter.py`
- `LiveBrokerAdapter`: `copilot_quant/brokers/live_broker_adapter.py`
- `LiveStrategyEngine`: `copilot_quant/backtest/live_engine.py`

## Support

For issues or questions:
1. Check the logs for error messages
2. Review this documentation
3. Check IBKR API documentation
4. Review test cases for examples
5. Open an issue on GitHub

## License

Same as main project (see LICENSE file).
