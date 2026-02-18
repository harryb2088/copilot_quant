# IBKR Live Market Data Feed Documentation

## Overview

The `IBKRLiveDataFeed` class provides real-time market data streaming and historical data downloading through the Interactive Brokers API. It's designed to integrate seamlessly with the Copilot Quant platform's data normalization and backtesting infrastructure.

## Features

- **Real-time Price Streaming**: Subscribe to live market data for multiple symbols
- **Historical Data Download**: Retrieve historical bars for backfilling
- **Data Normalization**: Automatic conversion to internal data format
- **Subscription Management**: Easy subscribe/unsubscribe operations
- **Reconnection Handling**: Automatic reconnection with subscription restoration
- **Streaming Updates**: Tick-by-tick price, volume, and quote updates
- **Comprehensive Logging**: Detailed logging for debugging and monitoring
- **Error Handling**: Robust error handling for IBKR API issues

## Installation

### Prerequisites

1. **Interactive Brokers Account**
   - Paper trading or live account
   - TWS (Trader Workstation) or IB Gateway installed

2. **Python Dependencies**
   ```bash
   pip install ib_insync>=0.9.86
   ```

### TWS/Gateway Configuration

1. **Enable API Connections**
   - Open TWS/Gateway
   - Go to: Edit > Global Configuration > API > Settings
   - Check "Enable ActiveX and Socket Clients"
   - Check "Allow connections from localhost only" (for security)
   - Note the Socket port (7497 for paper, 7496 for live)

2. **Configure API Settings**
   - Set "Master API client ID" if using multiple clients
   - Disable "Read-Only API" if you want to place orders
   - Consider enabling "Download open orders on connection"

## Quick Start

### Basic Usage

```python
from copilot_quant.brokers.live_market_data import IBKRLiveDataFeed

# Create and connect to IBKR
feed = IBKRLiveDataFeed(paper_trading=True)
if feed.connect():
    # Subscribe to real-time data
    feed.subscribe(['AAPL', 'MSFT', 'GOOGL'])
    
    # Get latest price
    price = feed.get_latest_price('AAPL')
    print(f"AAPL: ${price}")
    
    # Download historical data
    df = feed.get_historical_bars('AAPL', duration='1 M', bar_size='1 day')
    print(df.head())
    
    # Clean up
    feed.disconnect()
```

### Using Context Manager

```python
with IBKRLiveDataFeed(paper_trading=True) as feed:
    feed.subscribe(['AAPL', 'MSFT'])
    price = feed.get_latest_price('AAPL')
    # Automatically disconnects when exiting context
```

### With Callbacks

```python
def on_update(symbol, data):
    """Called on each price update"""
    print(f"{symbol}: ${data.get('last', 'N/A')}")

feed = IBKRLiveDataFeed(paper_trading=True)
feed.connect()
feed.subscribe(['AAPL', 'MSFT'], callback=on_update)

# Prices will be printed as they update
import time
time.sleep(30)  # Monitor for 30 seconds

feed.disconnect()
```

## API Reference

### Class: IBKRLiveDataFeed

#### Constructor

```python
IBKRLiveDataFeed(
    paper_trading: bool = True,
    host: str = None,
    port: int = None,
    client_id: int = None,
    use_gateway: bool = False
)
```

**Parameters:**
- `paper_trading`: If True, connect to paper trading account (default: True)
- `host`: IB API host address (default: '127.0.0.1' or from IB_HOST env var)
- `port`: IB API port (default: auto-detected or from IB_PORT env var)
- `client_id`: Unique client ID (default: 1 or from IB_CLIENT_ID env var)
- `use_gateway`: If True, use IB Gateway ports; else use TWS ports

**Port Auto-Detection:**
- Paper TWS: 7497
- Live TWS: 7496
- Paper Gateway: 4002
- Live Gateway: 4001

#### Methods

##### connect()

```python
connect(timeout: int = 30, retry_count: int = 3) -> bool
```

Establish connection to IBKR with retry logic.

**Returns:** True if connected successfully, False otherwise

**Example:**
```python
if feed.connect():
    print("Connected!")
```

##### subscribe()

```python
subscribe(
    symbols: List[str],
    callback: Callable[[str, Dict], None] = None
) -> Dict[str, bool]
```

Subscribe to real-time market data.

**Parameters:**
- `symbols`: List of ticker symbols
- `callback`: Optional function(symbol, data) called on updates

**Returns:** Dictionary mapping symbols to subscription success status

**Example:**
```python
results = feed.subscribe(['AAPL', 'MSFT', 'GOOGL'])
# Returns: {'AAPL': True, 'MSFT': True, 'GOOGL': True}
```

##### unsubscribe()

```python
unsubscribe(symbols: List[str]) -> Dict[str, bool]
```

Unsubscribe from real-time market data.

**Returns:** Dictionary mapping symbols to unsubscription success status

**Example:**
```python
feed.unsubscribe(['AAPL'])
```

##### get_latest_price()

```python
get_latest_price(symbol: str) -> Optional[float]
```

Get the most recent price for a subscribed symbol.

**Returns:** Latest price or None if not available

**Example:**
```python
price = feed.get_latest_price('AAPL')
if price:
    print(f"AAPL: ${price:.2f}")
```

##### get_latest_data()

```python
get_latest_data(symbol: str) -> Dict[str, Any]
```

Get complete latest market data for a symbol.

**Returns:** Dictionary with bid, ask, last, volume, etc.

**Example:**
```python
data = feed.get_latest_data('AAPL')
print(f"Bid: ${data['bid']}, Ask: ${data['ask']}")
```

##### get_historical_bars()

```python
get_historical_bars(
    symbol: str,
    duration: str = '1 M',
    bar_size: str = '1 day',
    what_to_show: str = 'TRADES',
    use_rth: bool = True
) -> Optional[pd.DataFrame]
```

Download historical OHLCV data.

**Parameters:**
- `symbol`: Ticker symbol
- `duration`: How far back (e.g., '1 M', '1 Y', '5 D')
- `bar_size`: Bar size (e.g., '1 min', '5 mins', '1 hour', '1 day')
- `what_to_show`: Data type ('TRADES', 'MIDPOINT', 'BID', 'ASK')
- `use_rth`: Use regular trading hours only

**Returns:** DataFrame with normalized OHLCV data

**Example:**
```python
# Daily bars for 1 month
df = feed.get_historical_bars('AAPL', duration='1 M', bar_size='1 day')

# 5-minute bars for 5 days
df = feed.get_historical_bars('AAPL', duration='5 D', bar_size='5 mins')

# Hourly bars for 2 weeks
df = feed.get_historical_bars('AAPL', duration='2 W', bar_size='1 hour')
```

**Duration Strings:**
- `'S'` - Seconds
- `'D'` - Days
- `'W'` - Weeks
- `'M'` - Months
- `'Y'` - Years

**Bar Sizes:**
- `'1 secs'`, `'5 secs'`, `'10 secs'`, `'15 secs'`, `'30 secs'`
- `'1 min'`, `'2 mins'`, `'3 mins'`, `'5 mins'`, `'10 mins'`, `'15 mins'`, `'20 mins'`, `'30 mins'`
- `'1 hour'`, `'2 hours'`, `'3 hours'`, `'4 hours'`, `'8 hours'`
- `'1 day'`, `'1 week'`, `'1 month'`

##### reconnect()

```python
reconnect(timeout: int = 30) -> bool
```

Reconnect to IBKR and restore subscriptions.

**Returns:** True if reconnection successful

**Example:**
```python
if not feed.is_connected():
    if feed.reconnect():
        print("Reconnected and subscriptions restored!")
```

##### disconnect()

```python
disconnect()
```

Disconnect from IBKR and clean up subscriptions.

##### get_subscribed_symbols()

```python
get_subscribed_symbols() -> List[str]
```

Get list of currently subscribed symbols.

**Returns:** List of symbol strings

##### is_connected()

```python
is_connected() -> bool
```

Check if currently connected to IBKR.

**Returns:** True if connected, False otherwise

## Data Format

### Real-time Data Structure

The callback function receives data in the following format:

```python
{
    'symbol': 'AAPL',
    'time': datetime(2024, 1, 15, 14, 30, 0),
    'bid': 150.45,
    'ask': 150.55,
    'last': 150.50,
    'close': 150.00,  # Previous close
    'volume': 1000000,
    'bid_size': 100,
    'ask_size': 200,
    'high': 151.00,   # Day high
    'low': 149.00,    # Day low
    'open': 150.00    # Day open
}
```

### Historical Data Format

Historical data is returned as a pandas DataFrame with:

**Index:** DatetimeIndex (timezone-aware, US/Eastern for equities)

**Columns:**
- `open`: Opening price
- `high`: High price
- `low`: Low price
- `close`: Closing price
- `volume`: Trading volume
- `symbol`: Ticker symbol

**Example:**
```
                              open    high     low   close    volume symbol
date                                                                        
2024-01-01 00:00:00-05:00  150.00  152.00  149.00  151.50  10000000   AAPL
2024-01-02 00:00:00-05:00  151.50  153.00  150.50  152.00  11000000   AAPL
...
```

## Changing Symbol Universe

### Method 1: Initial Subscription

```python
# Define your watchlist
symbols = ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'META']

feed = IBKRLiveDataFeed(paper_trading=True)
feed.connect()
feed.subscribe(symbols)
```

### Method 2: Dynamic Updates

```python
# Add new symbols
feed.subscribe(['TSLA', 'NVDA'])

# Remove symbols
feed.unsubscribe(['AAPL'])

# Check active subscriptions
active = feed.get_subscribed_symbols()
print(f"Monitoring: {', '.join(active)}")
```

### Method 3: From File

```python
# Load from text file (one symbol per line)
with open('watchlist.txt') as f:
    symbols = [line.strip() for line in f if line.strip()]

feed.subscribe(symbols)
```

### Method 4: From Database

```python
import sqlite3

# Load from database
conn = sqlite3.connect('trades.db')
cursor = conn.execute("SELECT DISTINCT symbol FROM portfolio")
symbols = [row[0] for row in cursor]
conn.close()

feed.subscribe(symbols)
```

### Method 5: S&P 500 Universe

```python
# Use the existing S&P 500 loader
from copilot_quant.data.sp500 import load_sp500_symbols

symbols = load_sp500_symbols()[:50]  # First 50 symbols
feed.subscribe(symbols)
```

## Configuration

### Environment Variables

Set these in your `.env` file or environment:

```bash
# IBKR Connection
IB_HOST=127.0.0.1
IB_PORT=7497
IB_CLIENT_ID=1
IB_PAPER_ACCOUNT=DU123456
```

### Code Configuration

```python
# Explicit configuration
feed = IBKRLiveDataFeed(
    paper_trading=True,
    host='127.0.0.1',
    port=7497,
    client_id=1,
    use_gateway=False
)
```

## Error Handling

### Connection Errors

```python
feed = IBKRLiveDataFeed(paper_trading=True)

if not feed.connect():
    print("Connection failed. Check:")
    print("1. TWS/Gateway is running")
    print("2. API connections are enabled")
    print("3. Port number is correct")
    print("4. No firewall blocking the connection")
```

### Subscription Errors

```python
results = feed.subscribe(['AAPL', 'INVALID_SYMBOL'])

for symbol, success in results.items():
    if not success:
        print(f"Failed to subscribe to {symbol}")
        print("Possible reasons:")
        print("- Invalid symbol")
        print("- No market data permissions")
        print("- Symbol not available on SMART router")
```

### Reconnection

```python
# Automatic reconnection
while True:
    if not feed.is_connected():
        print("Connection lost, reconnecting...")
        if feed.reconnect():
            print("Reconnected successfully")
        else:
            print("Reconnection failed, waiting 30s...")
            time.sleep(30)
    
    # Your trading logic here
    time.sleep(1)
```

## Best Practices

### 1. Connection Management

```python
# Use context manager for automatic cleanup
with IBKRLiveDataFeed(paper_trading=True) as feed:
    feed.subscribe(['AAPL'])
    # ... your code ...
    # Automatically disconnects
```

### 2. Start Small

```python
# Begin with a small watchlist for testing
test_symbols = ['AAPL', 'MSFT', 'GOOGL']
feed.subscribe(test_symbols)

# Scale up after testing
# all_symbols = load_large_universe()
# feed.subscribe(all_symbols)
```

### 3. Monitor Subscription Status

```python
# Check which symbols are active
active = feed.get_subscribed_symbols()
print(f"Currently monitoring {len(active)} symbols: {active}")
```

### 4. Handle Market Data Delays

```python
def on_update(symbol, data):
    # Check if data is delayed
    last = data.get('last')
    if last is None:
        # No real-time data, using delayed/snapshot
        last = data.get('close') or data.get('bid')
    
    if last:
        print(f"{symbol}: ${last:.2f}")
```

### 5. Efficient Historical Data Loading

```python
# Load historical data in batches
symbols = ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'META']

for symbol in symbols:
    df = feed.get_historical_bars(symbol, duration='1 M', bar_size='1 day')
    if df is not None:
        # Process or store data
        df.to_csv(f'data/{symbol}_1M.csv')
    
    # Be nice to the API
    time.sleep(1)
```

## Troubleshooting

### Connection Issues

**Problem:** Connection fails with timeout

**Solutions:**
1. Check TWS/Gateway is running
2. Verify API settings are enabled
3. Check port number matches your configuration
4. Try restarting TWS/Gateway
5. Check firewall settings

### Subscription Issues

**Problem:** Subscription returns False

**Solutions:**
1. Verify symbol is valid
2. Check you have market data permissions for that symbol
3. Try using a different exchange (e.g., 'ISLAND' instead of 'SMART')
4. Check IBKR account has required data subscriptions

### No Price Updates

**Problem:** Subscribed but not receiving updates

**Solutions:**
1. Check if market is open
2. Verify you have real-time data (not just delayed)
3. Check callback function is properly defined
4. Monitor logs for error messages

### Historical Data Issues

**Problem:** Historical data returns None or empty

**Solutions:**
1. Check duration/bar size combination is valid
2. Verify symbol has historical data available
3. Try different `what_to_show` parameter
4. Check you're not requesting too much data at once

## Examples

See `examples/ibkr_live_data_example.py` for complete working examples:

1. Basic real-time monitoring
2. Historical data download
3. Multiple timeframes
4. Reconnection handling
5. Symbol universe management

## Integration with Copilot Quant

### With Backtesting Engine

```python
from copilot_quant.brokers.live_market_data import IBKRLiveDataFeed
from copilot_quant.backtest import BacktestEngine

# Download historical data for backtesting
feed = IBKRLiveDataFeed(paper_trading=True)
feed.connect()

# Get data for backtesting
symbols = ['AAPL', 'MSFT']
historical_data = {}

for symbol in symbols:
    df = feed.get_historical_bars(symbol, duration='1 Y', bar_size='1 day')
    if df is not None:
        historical_data[symbol] = df

feed.disconnect()

# Use in backtest
# engine = BacktestEngine(data=historical_data)
# ... run backtest ...
```

### With Data Pipeline

```python
# Integrate with existing data pipeline
from copilot_quant.data.normalization import validate_data_quality

feed = IBKRLiveDataFeed(paper_trading=True)
feed.connect()

df = feed.get_historical_bars('AAPL', duration='1 M', bar_size='1 day')

# Data is already normalized by the feed
# But you can add additional validation
errors = validate_data_quality(df)
if errors:
    print(f"Data quality issues: {errors}")
```

## Additional Resources

- [Interactive Brokers API Documentation](https://interactivebrokers.github.io/tws-api/)
- [ib_insync Documentation](https://ib-insync.readthedocs.io/)
- [Copilot Quant Documentation](../README.md)
- [IBKR Setup Guide](./ibkr_setup_guide.md)

## Support

For issues or questions:
1. Check the troubleshooting section above
2. Review IBKR API documentation
3. Check ib_insync documentation
4. Open an issue on GitHub
