# IBKR Connection Manager

The IBKR Connection Manager provides centralized, robust connection handling for Interactive Brokers using the ib_insync library.

## Features

- ✅ **Automatic Connection Management**: Handles connection lifecycle automatically
- ✅ **Auto-Reconnection**: Automatically reconnects on disconnect with exponential backoff
- ✅ **Health Monitoring**: Real-time connection state and health metrics
- ✅ **Secure Configuration**: Uses environment variables for sensitive data
- ✅ **Multiple Application Support**: Supports both TWS and IB Gateway
- ✅ **Event Handlers**: Customizable disconnect/connect event handlers
- ✅ **Error Handling**: Comprehensive error logging with troubleshooting tips
- ✅ **Thread-Safe**: Safe for use in multi-threaded applications

## Quick Start

### Basic Usage

```python
from copilot_quant.brokers.connection_manager import IBKRConnectionManager

# Create connection manager
manager = IBKRConnectionManager(paper_trading=True)

# Connect to IBKR
try:
    manager.connect()
    print("Connected successfully!")
    
    # Get the underlying IB instance
    ib = manager.get_ib()
    
    # Use ib for trading operations
    accounts = ib.managedAccounts()
    print(f"Accounts: {accounts}")
    
finally:
    # Always disconnect when done
    manager.disconnect()
```

### Using Context Manager (Recommended)

```python
from copilot_quant.brokers.connection_manager import IBKRConnectionManager

# Connection is automatically managed
with IBKRConnectionManager(paper_trading=True) as manager:
    ib = manager.get_ib()
    
    # Do your work here
    balance = ib.accountSummary()
    print(f"Balance: {balance}")
    
# Automatically disconnects here
```

## Configuration

### Environment Variables

Create a `.env` file in your project root:

```bash
# Interactive Brokers Configuration
IB_HOST=127.0.0.1        # IBKR host address
IB_PORT=7497             # API port (auto-detected if not set)
IB_CLIENT_ID=1           # Unique client identifier
```

The connection manager will automatically use these values if no parameters are provided.

### Explicit Configuration

```python
manager = IBKRConnectionManager(
    paper_trading=True,      # Use paper trading account
    host='127.0.0.1',       # IBKR host
    port=7497,              # API port
    client_id=1,            # Unique client ID
    use_gateway=False,      # Use TWS (not Gateway)
    auto_reconnect=True     # Enable auto-reconnect
)
```

### Port Auto-Detection

If you don't specify a port, it's automatically detected based on your configuration:

| Configuration          | Port |
|-----------------------|------|
| TWS + Paper Trading   | 7497 |
| TWS + Live Trading    | 7496 |
| Gateway + Paper       | 4002 |
| Gateway + Live        | 4001 |

```python
# Automatically uses port 7497
manager = IBKRConnectionManager(paper_trading=True, use_gateway=False)

# Automatically uses port 4002  
manager = IBKRConnectionManager(paper_trading=True, use_gateway=True)
```

## Connection States

The connection manager tracks the following states:

```python
from copilot_quant.brokers.connection_manager import ConnectionState

# Possible states:
# - ConnectionState.DISCONNECTED
# - ConnectionState.CONNECTING
# - ConnectionState.CONNECTED
# - ConnectionState.RECONNECTING
# - ConnectionState.FAILED
```

Check the current state:

```python
manager = IBKRConnectionManager()
print(f"Current state: {manager.state}")
```

## Connection Monitoring

### Get Connection Status

```python
status = manager.get_status()

print(f"Connected: {status['connected']}")
print(f"State: {status['state']}")
print(f"Host: {status['host']}:{status['port']}")
print(f"Client ID: {status['client_id']}")
print(f"Uptime: {status['uptime_seconds']} seconds")
print(f"Reconnect count: {status['reconnect_count']}")
print(f"Accounts: {status['accounts']}")
```

### Event Handlers

Register custom handlers for connection events:

```python
def on_disconnect():
    print("Connection lost! Saving state...")
    # Save your trading state, positions, etc.

def on_connect():
    print("Connected! Resuming operations...")
    # Resume trading, resubscribe to data, etc.

manager = IBKRConnectionManager()
manager.add_disconnect_handler(on_disconnect)
manager.add_connect_handler(on_connect)
```

## Automatic Reconnection

By default, the connection manager automatically reconnects on disconnect:

```python
manager = IBKRConnectionManager(auto_reconnect=True)  # Default
manager.connect()

# If connection is lost, manager will automatically attempt to reconnect
# Your disconnect handlers will be called
# When reconnected, your connect handlers will be called
```

Disable auto-reconnect:

```python
manager = IBKRConnectionManager(auto_reconnect=False)
```

Manual reconnection:

```python
if not manager.is_connected():
    success = manager.reconnect(timeout=30)
    if success:
        print("Reconnected successfully")
    else:
        print("Reconnection failed")
```

## Error Handling

### Connection Errors

```python
from copilot_quant.brokers.connection_manager import IBKRConnectionManager

manager = IBKRConnectionManager()

try:
    manager.connect(timeout=30, retry_count=3)
except ConnectionError as e:
    print(f"Failed to connect: {e}")
    # Handle error appropriately
```

### Get Error Tips

The connection manager includes built-in troubleshooting tips for common errors:

```python
from copilot_quant.brokers.connection_manager import get_error_tips

tips = get_error_tips(502)  # Error code from IBKR

if tips:
    print(f"Error: {tips['description']}")
    print("Troubleshooting tips:")
    for tip in tips['tips']:
        print(f"  - {tip}")
```

Common error codes:
- **502**: Couldn't connect to TWS - TWS/Gateway not running or wrong port
- **504**: Not connected - Must call connect() first
- **1100**: Connection lost - Network issue or TWS closed
- **1101**: Connection restored - Data may need to be refreshed
- **200**: No security definition - Invalid symbol

See [IBKR_CONNECTION_TROUBLESHOOTING.md](IBKR_CONNECTION_TROUBLESHOOTING.md) for comprehensive error documentation.

## Integration with Broker and Data Feed

### Using with IBKRBroker

The `IBKRBroker` class uses the connection manager internally:

```python
from copilot_quant.brokers.interactive_brokers import IBKRBroker

broker = IBKRBroker(paper_trading=True)
broker.connect()

# The broker uses connection manager under the hood
# Auto-reconnect is enabled by default
balance = broker.get_account_balance()
print(f"Balance: {balance}")

broker.disconnect()
```

### Using with IBKRLiveDataFeed

The `IBKRLiveDataFeed` also uses the connection manager:

```python
from copilot_quant.brokers.live_market_data import IBKRLiveDataFeed

feed = IBKRLiveDataFeed(paper_trading=True)
feed.connect()

# Subscribe to market data
feed.subscribe(['AAPL', 'MSFT', 'GOOGL'])

# Get latest price
price = feed.get_latest_price('AAPL')
print(f"AAPL: ${price}")

feed.disconnect()
```

## Advanced Usage

### Multiple Connections

Use different client IDs for multiple simultaneous connections:

```python
# Trading connection
trading_mgr = IBKRConnectionManager(client_id=1)
trading_mgr.connect()

# Market data connection
data_mgr = IBKRConnectionManager(client_id=2)
data_mgr.connect()

# Both can run simultaneously
```

### Custom Timeout and Retries

```python
manager = IBKRConnectionManager()

# Custom connection parameters
manager.connect(
    timeout=60,      # Wait up to 60 seconds
    retry_count=5    # Try 5 times before giving up
)
```

### Monitoring in Background Thread

```python
import threading
import time

def monitor_connection(manager):
    while True:
        status = manager.get_status()
        if status['connected']:
            uptime = status['uptime_seconds'] / 60
            print(f"✅ Connected - Uptime: {uptime:.1f} mins")
        else:
            print(f"⚠️  Disconnected - State: {status['state']}")
        time.sleep(60)

manager = IBKRConnectionManager(paper_trading=True)
manager.connect()

# Start monitoring in background
monitor = threading.Thread(
    target=monitor_connection,
    args=(manager,),
    daemon=True
)
monitor.start()
```

## Best Practices

1. **Use context managers** when possible for automatic resource cleanup
2. **Enable auto-reconnect** for long-running applications
3. **Register disconnect/connect handlers** to manage application state
4. **Use unique client IDs** for multiple connections
5. **Monitor connection health** in production environments
6. **Handle connection errors gracefully** with try-except blocks
7. **Use environment variables** for configuration (don't hardcode credentials)

## Prerequisites

Before connecting, ensure:

1. ✅ TWS or IB Gateway is running
2. ✅ API is enabled in TWS settings (`Edit` → `Global Configuration` → `API` → `Settings`)
3. ✅ Socket port matches your configuration (default: 7497 for paper TWS)
4. ✅ `Enable ActiveX and Socket Clients` is checked
5. ✅ No other application is using the same client_id

## Troubleshooting

If you encounter connection issues, see:
- [IBKR Connection Troubleshooting Guide](IBKR_CONNECTION_TROUBLESHOOTING.md)

Enable debug logging:

```python
import logging

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

manager = IBKRConnectionManager()
manager.connect()
```

## API Reference

### IBKRConnectionManager

```python
class IBKRConnectionManager:
    def __init__(
        self,
        paper_trading: bool = True,
        host: Optional[str] = None,
        port: Optional[int] = None,
        client_id: Optional[int] = None,
        use_gateway: bool = False,
        auto_reconnect: bool = True
    )
```

#### Methods

- `connect(timeout: int = 30, retry_count: int = 3) -> bool`
  - Establish connection to IBKR
  - Returns True if successful, raises ConnectionError on failure

- `disconnect() -> None`
  - Disconnect from IBKR

- `reconnect(timeout: int = 30) -> bool`
  - Attempt to reconnect
  - Returns True if successful, False otherwise

- `is_connected() -> bool`
  - Check if currently connected

- `get_ib() -> IB`
  - Get the underlying ib_insync IB instance
  - Raises RuntimeError if not connected

- `get_status() -> dict`
  - Get detailed connection status information

- `add_disconnect_handler(handler: Callable) -> None`
  - Register a disconnect event handler

- `add_connect_handler(handler: Callable) -> None`
  - Register a connect event handler

### Helper Functions

```python
def get_error_tips(error_code: int) -> dict:
    """Get troubleshooting tips for an error code"""
```

## Examples

See the [examples](../examples/) directory for complete working examples:

- `examples/ibkr_connection_basic.py` - Basic connection example
- `examples/ibkr_connection_advanced.py` - Advanced features
- `examples/ibkr_monitoring.py` - Connection monitoring

## License

This module is part of the Copilot Quant project and is licensed under the MIT License.
