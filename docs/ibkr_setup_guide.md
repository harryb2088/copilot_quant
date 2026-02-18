# Interactive Brokers (IBKR) API Setup Guide

This guide provides comprehensive instructions for setting up and configuring Interactive Brokers TWS (Trader Workstation) or IB Gateway for API access with the Copilot Quant platform.

## 🚀 Quick Start

**Want to test your IB connection right away?**

1. Ensure TWS or IB Gateway is running with API enabled (see [Step-by-Step Configuration](#step-by-step-configuration))
2. Run the test script:
   ```bash
   python examples/test_ibkr_connection.py
   ```
3. See [examples/IBKR_SETUP.md](../examples/IBKR_SETUP.md) for detailed instructions

**Working Implementation:**
- Broker class: [`copilot_quant/brokers/interactive_brokers.py`](../copilot_quant/brokers/interactive_brokers.py)
- Test script: [`examples/test_ibkr_connection.py`](../examples/test_ibkr_connection.py)
- Quick guide: [`examples/IBKR_SETUP.md`](../examples/IBKR_SETUP.md)

---

## 📋 Table of Contents

1. [Prerequisites](#prerequisites)
2. [Installation Options](#installation-options)
3. [TWS vs IB Gateway](#tws-vs-ib-gateway)
4. [Paper Trading vs Live Trading](#paper-trading-vs-live-trading)
5. [Step-by-Step Configuration](#step-by-step-configuration)
6. [API Connection Settings](#api-connection-settings)
7. [Security Best Practices](#security-best-practices)
8. [Rate Limits and Restrictions](#rate-limits-and-restrictions)
9. [Connection Code Examples](#connection-code-examples)
10. [Troubleshooting](#troubleshooting)

---

## Prerequisites

Before setting up the IBKR API, ensure you have:

- **Active IBKR Account**: Either a live or paper trading account
- **Account Credentials**: Username and password for IBKR
- **Python Environment**: Python 3.8+ with `ib_insync` library installed
- **Network Access**: Firewall configured to allow API connections

### Installing ib_insync

```bash
pip install ib_insync>=0.9.86
```

Or add to your `requirements.txt`:
```
ib_insync>=0.9.86
```

---

## Installation Options

Interactive Brokers provides two primary applications for API access:

### Option 1: TWS (Trader Workstation)
- **Full-featured trading platform** with GUI
- **Size**: ~1-2 GB download
- **Best for**: Manual trading + automated trading
- **Download**: [Interactive Brokers TWS](https://www.interactivebrokers.com/en/trading/tws.php)

### Option 2: IB Gateway
- **Lightweight API-only application**
- **Size**: ~300 MB download
- **Best for**: Automated/algorithmic trading only
- **Download**: [IB Gateway](https://www.interactivebrokers.com/en/trading/ibgateway-stable.php)

### Recommendation
**For Copilot Quant**: Use **IB Gateway** for production deployments (lighter, more stable) and **TWS** for development/testing (easier to monitor).

---

## TWS vs IB Gateway

| Feature | TWS | IB Gateway |
|---------|-----|------------|
| **User Interface** | Full trading GUI | Minimal login window |
| **Size** | ~1-2 GB | ~300 MB |
| **Features** | Complete trading platform | API access only |
| **Resource Usage** | Higher (500MB+ RAM) | Lower (100-200MB RAM) |
| **Best For** | Manual + Auto trading | Automated trading |
| **Monitoring** | Built-in charts/tools | Requires external tools |
| **API Access** | Yes | Yes |
| **Auto-restart** | Yes (with config) | Yes (with config) |

---

## Paper Trading vs Live Trading

### Paper Trading (Recommended for Testing)

**Description**: Simulated trading environment with live market data but **NO REAL MONEY**.

**Port**: `7497` (TWS) or `4002` (IB Gateway)

**Features**:
- ✅ Live market data (15-minute delayed for free accounts)
- ✅ Realistic order execution simulation
- ✅ Full API functionality
- ✅ Risk-free testing environment
- ✅ Separate account from live trading

**Restrictions**:
- Maximum position sizes may differ from live
- Order execution may be more optimistic
- Not all order types may be available
- Market data subscriptions may be limited

**How to Access**:
1. Log in to [IBKR Client Portal](https://www.interactivebrokers.com/portal)
2. Go to **Settings** → **Account Settings**
3. Navigate to **Paper Trading Account**
4. Enable paper trading and note your paper account credentials

### Live Trading (Production)

**Description**: Real money trading environment.

**Port**: `7496` (TWS) or `4001` (IB Gateway)

**⚠️ WARNING**: 
- **REAL MONEY IS AT RISK**
- Start with small positions
- Test thoroughly in paper trading first
- Implement proper risk management
- Use stop losses and position limits

---

## Step-by-Step Configuration

### Step 1: Install TWS or IB Gateway

1. Download the appropriate installer from IBKR website
2. Run the installer and follow installation prompts
3. Complete the installation process

### Step 2: Launch the Application

**For Paper Trading (TWS)**:
```
1. Launch TWS
2. Select "Paper Trading" from login dropdown
3. Enter your paper trading credentials
4. Click "Login"
```

**For Paper Trading (IB Gateway)**:
```
1. Launch IB Gateway
2. Select "Paper Trading" mode
3. Enter your paper trading credentials
4. Click "Login"
```

**For Live Trading**:
```
1. Launch TWS/Gateway
2. Select "Live Trading" mode
3. Enter your live account credentials
4. Complete two-factor authentication if enabled
5. Click "Login"
```

### Step 3: Enable API Access

Once logged in, configure API settings:

#### In TWS:
1. Go to **File** → **Global Configuration** (or press `Ctrl+Alt+F`)
2. Navigate to **API** → **Settings**
3. Configure the following:

**Required Settings**:
- ✅ **Enable ActiveX and Socket Clients** - CHECK THIS
- ✅ **Allow connections from localhost only** - RECOMMENDED (unless connecting remotely)
- ⚠️ **Read-Only API** - UNCHECK for trading (check for data only)
- ✅ **Download open orders on connection** - Recommended

**Socket Port**:
- Paper Trading: `7497` (default)
- Live Trading: `7496` (default)

**Optional Settings**:
- **Master API Client ID**: Leave blank (allows any client ID)
- **Trusted IP Addresses**: Add if connecting from specific IPs
- **Bypass Order Precautions for API Orders**: USE WITH CAUTION

4. Click **OK** to save changes

#### In IB Gateway:
1. Click **Configure** → **Settings** in the login window
2. Navigate to **API** → **Settings**
3. Apply the same settings as TWS above
4. Click **OK** to save

### Step 4: Configure Auto-Restart (Optional but Recommended)

IBKR applications automatically log out daily. To prevent interruptions:

#### In TWS:
1. Go to **Edit** → **Global Configuration**
2. Navigate to **Lock and Exit**
3. Configure:
   - **Auto restart**: Enable
   - **Auto logoff time**: Set to preferred time (default: 11:50 PM ET)
   - **Auto restart time**: 5-10 minutes after logoff

#### In IB Gateway:
1. Go to **Configure** → **Settings**
2. Navigate to **Auto Restart**
3. Set restart time (e.g., 12:05 AM ET)

**Note**: You may need additional tools (like `systemd` on Linux or Task Scheduler on Windows) to fully automate restarts.

---

## API Connection Settings

### Connection Parameters

| Parameter | Description | Paper Trading | Live Trading |
|-----------|-------------|---------------|--------------|
| **Host** | IP address or hostname | `127.0.0.1` or `localhost` | `127.0.0.1` or `localhost` |
| **Port (TWS)** | Socket port number | `7497` | `7496` |
| **Port (Gateway)** | Socket port number | `4002` | `4001` |
| **Client ID** | Unique identifier for connection | `1` (or any unique integer) | `1` (or any unique integer) |

### Client ID Guidelines

- **Purpose**: Identifies your application to IBKR
- **Range**: Any positive integer (0-32767)
- **Uniqueness**: Each concurrent connection needs a unique Client ID
- **Master Client ID**: Client ID 0 has special privileges (can modify all orders)
- **Recommendation**: Use different Client IDs for different strategies/instances

**Example**:
- Strategy A: Client ID `1`
- Strategy B: Client ID `2`
- Monitoring Tool: Client ID `99`

### Trusted IP Addresses

If connecting from remote machines:

1. In API Settings, add trusted IP addresses
2. Format: `192.168.1.100` or `192.168.1.0/24` (CIDR notation)
3. **Security Warning**: Only add trusted IPs, never open to `0.0.0.0/0`

---

## Security Best Practices

### 1. Credential Management

**❌ NEVER**:
```python
# DO NOT hardcode credentials
username = "myusername"
password = "mypassword"
```

**✅ RECOMMENDED**:
```python
# Use environment variables
import os
username = os.getenv('IBKR_USERNAME')
password = os.getenv('IBKR_PASSWORD')
```

Or use a secure credential manager:
```python
from keyring import get_password
username = get_password('ibkr', 'username')
password = get_password('ibkr', 'password')
```

### 2. Connection Security

**Best Practices**:
- ✅ Use `localhost` (127.0.0.1) when running on same machine
- ✅ Enable "Allow connections from localhost only" in API settings
- ✅ Use VPN or SSH tunnel for remote connections
- ✅ Add specific IP addresses to trusted list (not ranges)
- ❌ NEVER expose API port to public internet
- ❌ NEVER use Read-Only API disabled unless necessary

### 3. API Key Security

IBKR doesn't use traditional API keys, but:
- Protect your account credentials
- Enable two-factor authentication (2FA)
- Use strong, unique passwords
- Monitor account activity regularly
- Set up alerts for large orders/withdrawals

### 4. Risk Management

**Trading Controls**:
```python
# Implement position limits
MAX_POSITION_SIZE = 1000
MAX_TOTAL_EXPOSURE = 50000

# Implement rate limiting
from time import sleep
def place_order_with_limit(order):
    place_order(order)
    sleep(1)  # Prevent rapid-fire orders
```

**Recommended Safeguards**:
- Set maximum position sizes
- Implement daily loss limits
- Use stop-loss orders
- Validate order quantities before submission
- Log all trading activity

---

## Rate Limits and Restrictions

### Message Rate Limits

Interactive Brokers enforces rate limits to prevent abuse:

| Action | Limit | Period |
|--------|-------|--------|
| **Messages** | 50 | 1 second |
| **Order Placement** | 50 | 1 second |
| **Market Data Requests** | 100 | 10 seconds |
| **Historical Data Requests** | 60 | 10 minutes |

### Consequences of Exceeding Limits

- **Soft Limit**: Throttling (requests queued)
- **Hard Limit**: Temporary ban (2-10 minutes)
- **Repeated Violations**: Account suspension

### Rate Limit Best Practices

```python
from ib_insync import IB
import time

ib = IB()
ib.connect('127.0.0.1', 7497, clientId=1)

# Method 1: Add delays between requests
def place_orders_safely(orders):
    for order in orders:
        ib.placeOrder(contract, order)
        time.sleep(0.1)  # 10 orders/second max

# Method 2: Use ib_insync built-in rate limiting
ib.RequestTimeout = 30  # Increase timeout
ib.MaxSyncedSubAccounts = 50  # Limit concurrent operations

# Method 3: Batch requests
def request_historical_data_batch(contracts):
    results = []
    for i, contract in enumerate(contracts):
        if i > 0 and i % 5 == 0:  # Every 5 requests
            time.sleep(1)  # Wait 1 second
        data = ib.reqHistoricalData(contract, ...)
        results.append(data)
    return results
```

### Market Data Subscriptions

**Free Account Limits**:
- US stocks: 15-minute delayed data
- Number of concurrent subscriptions: Limited
- Snapshot data: Limited requests per minute

**Paid Market Data**:
- Real-time data requires subscriptions
- Monthly fees vary by exchange
- Check [IBKR Market Data](https://www.interactivebrokers.com/en/trading/market-data.php)

### Recommended Settings

```python
# Connection configuration
CONNECTION_TIMEOUT = 30  # seconds
RETRY_DELAY = 5  # seconds
MAX_RETRIES = 3

# Rate limiting
REQUEST_DELAY = 0.1  # 100ms between requests
BATCH_SIZE = 50  # Orders per batch
BATCH_DELAY = 1.0  # 1 second between batches

# Data requests
MAX_CONCURRENT_DATA_REQUESTS = 5
HISTORICAL_DATA_DELAY = 10  # seconds between requests
```

---

## Connection Code Examples

### Basic Connection (ib_insync)

```python
from ib_insync import IB

# Create IB instance
ib = IB()

# Connect to paper trading (TWS)
ib.connect('127.0.0.1', 7497, clientId=1)

# Verify connection
if ib.isConnected():
    print("Successfully connected to IBKR")
    print(f"Account: {ib.managedAccounts()}")
else:
    print("Failed to connect")

# Disconnect when done
ib.disconnect()
```

### Connection with Error Handling

```python
from ib_insync import IB
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def connect_to_ibkr(host='127.0.0.1', port=7497, client_id=1, timeout=30):
    """
    Connect to Interactive Brokers with error handling
    
    Args:
        host: IBKR host (default: localhost)
        port: IBKR port (7497 for paper, 7496 for live)
        client_id: Unique client identifier
        timeout: Connection timeout in seconds
    
    Returns:
        IB instance if connected, None otherwise
    """
    ib = IB()
    
    try:
        logger.info(f"Connecting to IBKR at {host}:{port} (Client ID: {client_id})")
        ib.connect(host, port, clientId=client_id, timeout=timeout)
        
        if ib.isConnected():
            accounts = ib.managedAccounts()
            logger.info(f"✓ Connected successfully")
            logger.info(f"Accounts: {accounts}")
            return ib
        else:
            logger.error("Connection failed")
            return None
            
    except Exception as e:
        logger.error(f"Connection error: {e}")
        return None

# Usage
ib = connect_to_ibkr()
if ib:
    # Your trading logic here
    pass
```

### Connection with Auto-Reconnect

```python
from ib_insync import IB
import time
import logging

logger = logging.getLogger(__name__)

class IBKRConnection:
    """IBKR connection with auto-reconnect capability"""
    
    def __init__(self, host='127.0.0.1', port=7497, client_id=1):
        self.host = host
        self.port = port
        self.client_id = client_id
        self.ib = IB()
        self.is_connected = False
        
    def connect(self, max_retries=3, retry_delay=5):
        """Connect with retry logic"""
        for attempt in range(max_retries):
            try:
                logger.info(f"Connection attempt {attempt + 1}/{max_retries}")
                self.ib.connect(self.host, self.port, clientId=self.client_id)
                
                if self.ib.isConnected():
                    self.is_connected = True
                    logger.info("✓ Connected to IBKR")
                    self._setup_handlers()
                    return True
                    
            except Exception as e:
                logger.error(f"Connection failed: {e}")
                if attempt < max_retries - 1:
                    logger.info(f"Retrying in {retry_delay} seconds...")
                    time.sleep(retry_delay)
        
        logger.error("Failed to connect after all retries")
        return False
    
    def _setup_handlers(self):
        """Setup event handlers for disconnection"""
        def on_disconnect():
            logger.warning("Disconnected from IBKR")
            self.is_connected = False
            self._auto_reconnect()
        
        self.ib.disconnectedEvent += on_disconnect
    
    def _auto_reconnect(self):
        """Automatically reconnect on disconnection"""
        logger.info("Attempting auto-reconnect...")
        time.sleep(5)
        self.connect()
    
    def disconnect(self):
        """Disconnect from IBKR"""
        if self.is_connected:
            self.ib.disconnect()
            self.is_connected = False
            logger.info("Disconnected from IBKR")

# Usage
conn = IBKRConnection(host='127.0.0.1', port=7497, client_id=1)
if conn.connect():
    # Your trading logic
    try:
        # Trading operations
        pass
    finally:
        conn.disconnect()
```

### Complete Example: Fetch Account Info

```python
from ib_insync import IB
import pandas as pd

# Connect
ib = IB()
ib.connect('127.0.0.1', 7497, clientId=1)

# Get account summary
account_values = ib.accountValues()
df = pd.DataFrame([
    {
        'tag': av.tag,
        'value': av.value,
        'currency': av.currency,
        'account': av.account
    }
    for av in account_values
])

print("\nAccount Summary:")
print(df[df['tag'].isin(['NetLiquidation', 'TotalCashValue', 'BuyingPower'])])

# Get positions
positions = ib.positions()
if positions:
    print("\nCurrent Positions:")
    for pos in positions:
        print(f"{pos.contract.symbol}: {pos.position} @ {pos.avgCost}")
else:
    print("\nNo open positions")

# Get open orders
orders = ib.openOrders()
if orders:
    print("\nOpen Orders:")
    for order in orders:
        print(f"{order.action} {order.totalQuantity} {order.contract.symbol}")
else:
    print("\nNo open orders")

# Disconnect
ib.disconnect()
```

### Example: Place a Simple Order

```python
from ib_insync import IB, Stock, MarketOrder, LimitOrder

# Connect
ib = IB()
ib.connect('127.0.0.1', 7497, clientId=1)

# Define contract (stock)
contract = Stock('AAPL', 'SMART', 'USD')

# Qualify contract (get full details)
ib.qualifyContracts(contract)

# Create a market order
order = MarketOrder('BUY', 100)

# Place order
trade = ib.placeOrder(contract, order)

print(f"Order placed: {trade.order.orderId}")
print(f"Status: {trade.orderStatus.status}")

# Wait for order to fill (with timeout)
import time
timeout = 30
elapsed = 0
while not trade.isDone() and elapsed < timeout:
    ib.sleep(1)
    elapsed += 1
    print(f"Status: {trade.orderStatus.status}")

if trade.isDone():
    print(f"Order completed: {trade.orderStatus.status}")
    if trade.fills:
        for fill in trade.fills:
            print(f"Filled: {fill.execution.shares} @ {fill.execution.avgPrice}")
else:
    print("Order timeout - cancelling")
    ib.cancelOrder(order)

# Disconnect
ib.disconnect()
```

### Integration with Copilot Quant

```python
"""
Example integration with Copilot Quant platform
"""
from ib_insync import IB, Stock, MarketOrder
import os
from datetime import datetime

class IBKRBroker:
    """Interactive Brokers integration for Copilot Quant"""
    
    def __init__(self, paper_trading=True):
        """
        Initialize IBKR broker connection
        
        Args:
            paper_trading: If True, connect to paper trading (port 7497)
                          If False, connect to live trading (port 7496)
        """
        self.ib = IB()
        self.paper_trading = paper_trading
        self.port = 7497 if paper_trading else 7496
        self.client_id = 1
        
    def connect(self):
        """Establish connection to IBKR"""
        host = '127.0.0.1'
        
        try:
            self.ib.connect(host, self.port, clientId=self.client_id)
            
            if self.ib.isConnected():
                mode = "Paper" if self.paper_trading else "Live"
                print(f"✓ Connected to IBKR ({mode} Trading)")
                print(f"Accounts: {self.ib.managedAccounts()}")
                return True
            else:
                print("✗ Failed to connect to IBKR")
                return False
                
        except Exception as e:
            print(f"Connection error: {e}")
            return False
    
    def get_account_balance(self):
        """Get current account balance"""
        account_values = self.ib.accountSummary()
        
        balance_info = {}
        for av in account_values:
            if av.tag in ['NetLiquidation', 'TotalCashValue', 'BuyingPower']:
                balance_info[av.tag] = float(av.value)
        
        return balance_info
    
    def execute_order(self, symbol, quantity, order_type='market', side='buy'):
        """
        Execute trading order
        
        Args:
            symbol: Stock symbol (e.g., 'AAPL')
            quantity: Number of shares
            order_type: 'market' or 'limit'
            side: 'buy' or 'sell'
        
        Returns:
            Trade object if successful, None otherwise
        """
        # Create contract
        contract = Stock(symbol, 'SMART', 'USD')
        self.ib.qualifyContracts(contract)
        
        # Create order
        action = 'BUY' if side.lower() == 'buy' else 'SELL'
        
        if order_type.lower() == 'market':
            order = MarketOrder(action, quantity)
        else:
            # Limit order requires price
            raise NotImplementedError("Limit orders require price parameter")
        
        # Place order
        trade = self.ib.placeOrder(contract, order)
        
        print(f"Order placed: {action} {quantity} {symbol}")
        print(f"Order ID: {trade.order.orderId}")
        
        return trade
    
    def get_positions(self):
        """Get current positions"""
        positions = self.ib.positions()
        
        position_list = []
        for pos in positions:
            position_list.append({
                'symbol': pos.contract.symbol,
                'position': pos.position,
                'avg_cost': pos.avgCost,
                'market_value': pos.position * pos.avgCost
            })
        
        return position_list
    
    def disconnect(self):
        """Disconnect from IBKR"""
        if self.ib.isConnected():
            self.ib.disconnect()
            print("Disconnected from IBKR")

# Usage example
if __name__ == '__main__':
    # Initialize broker (paper trading)
    broker = IBKRBroker(paper_trading=True)
    
    # Connect
    if broker.connect():
        # Get account balance
        balance = broker.get_account_balance()
        print(f"\nAccount Balance: {balance}")
        
        # Get positions
        positions = broker.get_positions()
        print(f"\nPositions: {positions}")
        
        # Place order (example - uncomment to execute)
        # trade = broker.execute_order('AAPL', 10, order_type='market', side='buy')
        
        # Disconnect
        broker.disconnect()
```

---

## Troubleshooting

### Common Issues and Solutions

#### 1. Connection Refused

**Error**: `Connection refused` or `Cannot connect to 127.0.0.1:7497`

**Solutions**:
- ✅ Verify TWS/Gateway is running
- ✅ Check API is enabled in settings
- ✅ Confirm correct port number (7497 for paper, 7496 for live)
- ✅ Ensure "Enable ActiveX and Socket Clients" is checked
- ✅ Check firewall isn't blocking the connection

#### 2. "Not connected" Error

**Error**: `Error 502: Couldn't connect to TWS`

**Solutions**:
- ✅ Ensure you're logged into TWS/Gateway
- ✅ Wait 30 seconds after login before connecting
- ✅ Check if another application is using the same client ID
- ✅ Try a different client ID

#### 3. Authentication Failed

**Error**: `Authentication failed`

**Solutions**:
- ✅ Verify credentials are correct
- ✅ Check if 2FA is enabled (may need to approve on mobile app)
- ✅ Ensure paper trading credentials are used for paper mode
- ✅ Check if account is locked or suspended

#### 4. Order Rejection

**Error**: `Order rejected`

**Solutions**:
- ✅ Verify sufficient buying power
- ✅ Check if trading permissions are enabled for the security type
- ✅ Ensure market is open for the security
- ✅ Verify order parameters (quantity, price, etc.)
- ✅ Check if Read-Only API is enabled (should be disabled for trading)

#### 5. Rate Limit Exceeded

**Error**: `Connectivity between IB and TWS has been lost`

**Solutions**:
- ✅ Reduce request frequency
- ✅ Add delays between API calls (see Rate Limits section)
- ✅ Implement request queuing
- ✅ Wait 2-10 minutes before retrying

#### 6. Market Data Subscription Error

**Error**: `Market data farm connection is broken`

**Solutions**:
- ✅ Check if market data subscriptions are active
- ✅ Verify market is open
- ✅ For real-time data, ensure subscriptions are paid
- ✅ Try disconnecting and reconnecting

#### 7. Auto-Restart Not Working

**Issue**: Application doesn't restart automatically

**Solutions**:
- ✅ Enable auto-restart in settings
- ✅ Check scheduled task/cron job is configured
- ✅ Verify credentials are saved (if using automated login)
- ✅ Use external restart script (see below)

### Debug Mode

Enable detailed logging:

```python
import logging

# Enable ib_insync debug logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger('ib_insync')
logger.setLevel(logging.DEBUG)

# Or use ib_insync util
from ib_insync import util
util.logToConsole(logging.DEBUG)

# Now connect
from ib_insync import IB
ib = IB()
ib.connect('127.0.0.1', 7497, clientId=1)
```

### Testing Connection

```python
"""Quick connection test script"""
from ib_insync import IB
import sys

def test_connection(host='127.0.0.1', port=7497):
    """Test IBKR connection"""
    print(f"Testing connection to {host}:{port}...")
    
    ib = IB()
    
    try:
        ib.connect(host, port, clientId=999, timeout=10)
        
        if ib.isConnected():
            print("✓ Connection successful!")
            print(f"  Accounts: {ib.managedAccounts()}")
            print(f"  Connection time: {ib.client.connTime}")
            
            # Test API functionality
            account_values = ib.accountValues()
            print(f"  Account values: {len(account_values)} entries")
            
            ib.disconnect()
            return True
        else:
            print("✗ Connection failed")
            return False
            
    except Exception as e:
        print(f"✗ Connection error: {e}")
        return False

if __name__ == '__main__':
    # Test paper trading
    print("\n=== Paper Trading ===")
    test_connection('127.0.0.1', 7497)
    
    # Uncomment to test live trading
    # print("\n=== Live Trading ===")
    # test_connection('127.0.0.1', 7496)
```

---

## Additional Resources

### Official Documentation
- [IBKR API Reference](https://interactivebrokers.github.io/tws-api/)
- [ib_insync Documentation](https://ib-insync.readthedocs.io/)
- [IBKR Webinars](https://www.interactivebrokers.com/en/index.php?f=7235)

### Useful Links
- [IBKR Client Portal](https://www.interactivebrokers.com/portal)
- [Market Data Subscriptions](https://www.interactivebrokers.com/en/trading/market-data.php)
- [Paper Trading Account Setup](https://www.interactivebrokers.com/en/trading/free-trial.php)
- [API System Status](https://www.interactivebrokers.com/en/trading/system-status.php)

### Community Resources
- [ib_insync GitHub Issues](https://github.com/erdewit/ib_insync/issues)
- [IBKR Reddit Community](https://www.reddit.com/r/interactivebrokers/)
- [Elite Trader Forums](https://www.elitetrader.com/et/forums/automated-trading.52/)

---

## Security Checklist

Before going live, verify:

- [ ] Paper trading tested thoroughly
- [ ] Error handling implemented
- [ ] Rate limiting in place
- [ ] Position limits configured
- [ ] Stop-loss orders implemented
- [ ] Credentials stored securely (not in code)
- [ ] Two-factor authentication enabled on account
- [ ] API access restricted to localhost or trusted IPs
- [ ] Logging and monitoring configured
- [ ] Emergency stop mechanism implemented
- [ ] Risk management rules defined
- [ ] Account alerts configured

---

## Quick Reference Card

| Task | Command/Setting |
|------|----------------|
| **Paper Trading Port (TWS)** | `7497` |
| **Live Trading Port (TWS)** | `7496` |
| **Paper Trading Port (Gateway)** | `4002` |
| **Live Trading Port (Gateway)** | `4001` |
| **Enable API** | File → Global Config → API → Enable ActiveX and Socket Clients |
| **Connect** | `ib.connect('127.0.0.1', 7497, clientId=1)` |
| **Check Connection** | `ib.isConnected()` |
| **Get Accounts** | `ib.managedAccounts()` |
| **Get Positions** | `ib.positions()` |
| **Place Order** | `ib.placeOrder(contract, order)` |
| **Disconnect** | `ib.disconnect()` |

---

## Support

For issues specific to:
- **Copilot Quant Platform**: Open an issue on the [GitHub repository](https://github.com/harryb2088/copilot_quant)
- **IBKR API**: Contact [IBKR Support](https://www.interactivebrokers.com/en/support/online.php)
- **ib_insync Library**: Check [ib_insync documentation](https://ib-insync.readthedocs.io/) or [GitHub issues](https://github.com/erdewit/ib_insync/issues)

---

**Last Updated**: 2026-02-17  
**Version**: 1.0  
**Status**: Complete

---

**⚠️ Disclaimer**: This guide is for educational purposes only. Trading involves substantial risk of loss. Always test thoroughly in paper trading before using real money. The authors and contributors are not responsible for any financial losses incurred through the use of this guide or associated software.
