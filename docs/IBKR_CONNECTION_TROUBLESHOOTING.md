# Interactive Brokers Connection Troubleshooting Guide

This guide helps you diagnose and fix common connection issues when using the IBKR Connection Manager.

## Quick Start Connection Test

Before troubleshooting, verify your basic setup:

```python
from copilot_quant.brokers.connection_manager import IBKRConnectionManager

# Test connection to paper trading
manager = IBKRConnectionManager(paper_trading=True)
status = manager.get_status()
print(f"Connection status: {status}")

try:
    manager.connect()
    print("✅ Connection successful!")
except ConnectionError as e:
    print(f"❌ Connection failed: {e}")
```

## Prerequisites Checklist

Before you can connect, ensure:

- [ ] TWS (Trader Workstation) or IB Gateway is running
- [ ] API connections are enabled in TWS:
  - Go to `Edit` → `Global Configuration` → `API` → `Settings`
  - Check `Enable ActiveX and Socket Clients`
  - Note the `Socket Port` number (default: 7497 for paper, 7496 for live)
  - (Optional) Check `Read-Only API` if you only need market data
- [ ] Firewall allows connections to localhost (127.0.0.1)
- [ ] No other application is using the same `client_id`

## Common Error Codes

### Error 502: "Couldn't connect to TWS"

**Description:** Cannot establish connection to TWS/Gateway.

**Common Causes:**
- TWS or IB Gateway is not running
- Wrong port number
- API connections not enabled in TWS
- Firewall blocking the connection

**Solutions:**

1. **Verify TWS/Gateway is running:**
   - Look for the TWS or IB Gateway window
   - Restart if needed

2. **Check port configuration:**
   ```python
   # Paper trading with TWS (default)
   manager = IBKRConnectionManager(paper_trading=True, use_gateway=False)
   # Port 7497 is used automatically
   
   # Live trading with TWS
   manager = IBKRConnectionManager(paper_trading=False, use_gateway=False)
   # Port 7496 is used automatically
   
   # Paper trading with IB Gateway
   manager = IBKRConnectionManager(paper_trading=True, use_gateway=True)
   # Port 4002 is used automatically
   ```

3. **Enable API in TWS:**
   - Open TWS
   - Go to `Edit` → `Global Configuration` → `API` → `Settings`
   - Check `Enable ActiveX and Socket Clients`
   - Click `Apply` and `OK`

4. **Check if another client is connected:**
   - Only one connection per `client_id` is allowed
   - Try using a different `client_id`:
   ```python
   manager = IBKRConnectionManager(paper_trading=True, client_id=2)
   ```

### Error 504: "Not connected"

**Description:** Attempting to use API without an active connection.

**Solutions:**

1. **Always connect before using the API:**
   ```python
   manager = IBKRConnectionManager()
   manager.connect()  # Must call this first!
   
   # Now you can use the connection
   ib = manager.get_ib()
   ```

2. **Check connection status:**
   ```python
   if not manager.is_connected():
       print("Not connected - attempting to connect...")
       manager.connect()
   ```

3. **Use context manager for automatic connection:**
   ```python
   with IBKRConnectionManager() as manager:
       # Connection established automatically
       ib = manager.get_ib()
       # ... do work ...
   # Disconnected automatically
   ```

### Error 1100: "Connectivity between IB and TWS has been lost"

**Description:** Connection to TWS was lost (network issue or TWS closed).

**Solutions:**

1. **Enable auto-reconnect (default):**
   ```python
   manager = IBKRConnectionManager(auto_reconnect=True)  # Default
   # Will automatically attempt to reconnect
   ```

2. **Manual reconnection:**
   ```python
   if not manager.is_connected():
       success = manager.reconnect()
       if success:
           print("Reconnected successfully")
       else:
           print("Reconnection failed")
   ```

3. **Register disconnect handlers:**
   ```python
   def on_disconnect():
       print("Connection lost! Attempting to save state...")
       # Save your data, pause trading, etc.
   
   manager.add_disconnect_handler(on_disconnect)
   ```

4. **Check network connectivity:**
   - Ensure TWS/Gateway is still running
   - Check if your internet connection is stable
   - Look for firewall or antivirus interference

### Error 1101: "Connectivity between IB and TWS has been restored - data lost"

**Description:** Connection restored but some data may be missing.

**Solutions:**

1. **Re-request critical data:**
   ```python
   def on_reconnect():
       print("Connection restored - refreshing data...")
       # Re-request positions, orders, market data, etc.
   
   manager.add_connect_handler(on_reconnect)
   ```

2. **For market data feeds, resubscribe:**
   ```python
   from copilot_quant.brokers.live_market_data import IBKRLiveDataFeed
   
   feed = IBKRLiveDataFeed()
   # Reconnect method automatically resubscribes
   feed.reconnect()
   ```

### Error 1102: "Connectivity between IB and TWS has been restored - data maintained"

**Description:** Connection restored and data stream resumed.

**Action Required:** Usually no action needed, but verify your data is current.

### Error 200: "No security definition found"

**Description:** The requested contract/symbol was not found.

**Solutions:**

1. **Verify the symbol is correct:**
   ```python
   # Use the correct exchange symbol
   symbol = "AAPL"  # ✓ Correct
   # Not: "Apple" or "AAPL.US"
   ```

2. **Qualify the contract:**
   ```python
   from ib_insync import Stock
   
   ib = manager.get_ib()
   contract = Stock("AAPL", "SMART", "USD")
   qualified = ib.qualifyContracts(contract)
   
   if not qualified:
       print("Symbol not found or not tradeable")
   ```

3. **Check trading hours:**
   - Some symbols are only available during market hours
   - Use `useRTH=False` for extended hours data

### Error 10167: "Delayed market data"

**Description:** You are receiving delayed market data (15-20 minutes behind).

**Solutions:**

1. **This is normal for non-professional accounts** - delayed data is free

2. **To get real-time data:**
   - Subscribe to real-time market data in TWS
   - Go to `Account` → `Market Data Subscriptions`
   - Select the exchanges you need
   - Accept the exchange agreements

3. **For testing, delayed data is usually sufficient:**
   ```python
   # Delayed data works fine for testing
   feed = IBKRLiveDataFeed(paper_trading=True)
   # No additional configuration needed
   ```

## Connection Monitoring

### Check Connection Status

```python
status = manager.get_status()
print(f"Connected: {status['connected']}")
print(f"State: {status['state']}")
print(f"Uptime: {status['uptime_seconds']} seconds")
print(f"Reconnects: {status['reconnect_count']}")
print(f"Accounts: {status['accounts']}")
```

### Monitor Connection Health

```python
import time

def monitor_connection(manager, interval=60):
    """Monitor connection health every interval seconds"""
    while True:
        status = manager.get_status()
        
        if not status['connected']:
            print(f"⚠️  Connection lost at {time.strftime('%H:%M:%S')}")
            print(f"   Attempting reconnection...")
        else:
            uptime_mins = status['uptime_seconds'] / 60
            print(f"✅ Connected - Uptime: {uptime_mins:.1f} mins")
        
        time.sleep(interval)

# Run in background thread
import threading
monitor_thread = threading.Thread(
    target=monitor_connection,
    args=(manager, 60),
    daemon=True
)
monitor_thread.start()
```

## Best Practices

### 1. Always Use Try-Except for Connection Operations

```python
try:
    manager.connect(timeout=30, retry_count=3)
    # ... do work ...
except ConnectionError as e:
    print(f"Failed to connect: {e}")
    # Handle error appropriately
```

### 2. Use Context Managers When Possible

```python
with IBKRConnectionManager(paper_trading=True) as manager:
    ib = manager.get_ib()
    # Connection is automatically managed
    # ... do work ...
# Automatically disconnects
```

### 3. Enable Auto-Reconnect for Long-Running Applications

```python
manager = IBKRConnectionManager(
    paper_trading=True,
    auto_reconnect=True  # Enabled by default
)
```

### 4. Register Event Handlers

```python
def on_disconnect():
    # Save state, pause trading
    print("Connection lost - saving state")

def on_connect():
    # Resume operations
    print("Connection restored - resuming operations")

manager.add_disconnect_handler(on_disconnect)
manager.add_connect_handler(on_connect)
```

### 5. Use Unique Client IDs for Multiple Connections

```python
# Trading connection
trading_manager = IBKRConnectionManager(client_id=1)

# Data feed connection
data_manager = IBKRConnectionManager(client_id=2)
```

### 6. Gracefully Handle Shutdown

```python
import signal
import sys

def signal_handler(sig, frame):
    print("\nShutting down gracefully...")
    manager.disconnect()
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)
```

## Environment Configuration

### Using Environment Variables

Create a `.env` file:

```bash
# Interactive Brokers Configuration
IB_HOST=127.0.0.1
IB_PORT=7497              # Paper Trading (TWS)
IB_CLIENT_ID=1
IB_PAPER_ACCOUNT=DU123456 # Your paper account number
```

Load in your application:

```python
import os
from dotenv import load_dotenv

load_dotenv()  # Load .env file

# Connection manager will automatically use these values
manager = IBKRConnectionManager(paper_trading=True)
```

### Port Reference

| Mode                    | Port |
|------------------------|------|
| TWS Paper Trading      | 7497 |
| TWS Live Trading       | 7496 |
| Gateway Paper Trading  | 4002 |
| Gateway Live Trading   | 4001 |

## Debugging Connection Issues

### Enable Debug Logging

```python
import logging

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

manager = IBKRConnectionManager(paper_trading=True)
manager.connect()
```

### Check TWS Logs

TWS logs are located at:
- **Windows:** `C:\Users\<username>\Jts\<account>\log`
- **macOS:** `~/Jts/<account>/log`
- **Linux:** `~/Jts/<account>/log`

Look for API-related messages in:
- `api.<date>.log`
- `tws.<date>.log`

### Verify API Settings in TWS

1. Open TWS
2. Go to `Edit` → `Global Configuration` → `API` → `Settings`
3. Verify:
   - `Enable ActiveX and Socket Clients` is checked
   - `Socket Port` matches your configuration
   - `Trusted IP Addresses` includes `127.0.0.1` (or `0.0.0.0` for all)
   - `Master API client ID` is not conflicting with your client_id

### Test with Different Client IDs

```python
# Try different client IDs if one fails
for client_id in range(1, 5):
    try:
        manager = IBKRConnectionManager(client_id=client_id)
        manager.connect(retry_count=1)
        print(f"✅ Connected with client_id={client_id}")
        break
    except ConnectionError:
        print(f"❌ Failed with client_id={client_id}")
        continue
```

## Getting Help

If you continue to experience issues:

1. **Check the Interactive Brokers API documentation:**
   - https://interactivebrokers.github.io/tws-api/

2. **Review the ib_insync documentation:**
   - https://ib-insync.readthedocs.io/

3. **Search the error code:**
   ```python
   from copilot_quant.brokers.connection_manager import get_error_tips
   
   tips = get_error_tips(502)  # Replace with your error code
   print(f"Error: {tips['description']}")
   print("Tips:")
   for tip in tips['tips']:
       print(f"  - {tip}")
   ```

4. **Enable detailed logging and review logs**

5. **Test with IB's sample applications** to rule out configuration issues

6. **Contact Interactive Brokers support** for account-specific issues
