# Interactive Brokers (IBKR) - Comprehensive Setup & Usage Guide

**Complete end-to-end documentation for IBKR integration with Copilot Quant Platform**

> 🎯 **New to IBKR?** Start with the [5-Minute Quick Start](#quick-start-5-minutes)  
> 🔧 **Having issues?** Jump to [Troubleshooting](#troubleshooting)  
> 💡 **Need examples?** See [Usage Examples](#usage-examples)  
> 📚 **Looking for details?** Check [Additional Resources](#additional-resources)

---

## 📖 Table of Contents

1. [Overview](#overview)
2. [Prerequisites](#prerequisites)
3. [Quick Start (5 Minutes)](#quick-start-5-minutes)
4. [Detailed Setup](#detailed-setup)
   - [TWS vs IB Gateway](#tws-vs-ib-gateway)
   - [Installation](#installation)
   - [API Configuration](#api-configuration)
   - [Environment Setup](#environment-setup)
5. [Trading Modes](#trading-modes)
   - [Paper Trading](#paper-trading-recommended)
   - [Live Trading](#live-trading)
   - [Switching Between Modes](#switching-between-modes)
6. [Service Requirements](#service-requirements)
7. [Usage Examples](#usage-examples)
8. [Advanced Configuration](#advanced-configuration)
9. [Troubleshooting](#troubleshooting)
10. [Best Practices](#best-practices)
11. [Additional Resources](#additional-resources)

---

## Overview

This guide provides **complete, step-by-step instructions** for integrating Interactive Brokers (IBKR) with the Copilot Quant platform. Whether you're setting up paper trading for testing or live trading with real money, this guide has you covered.

### What This Guide Covers

✅ **Installation & Setup**
- Installing TWS or IB Gateway
- Configuring API access
- Setting up environment variables
- Testing your connection

✅ **Trading Modes**
- Paper trading (risk-free testing with simulated money)
- Live trading (real money trading)
- How to switch between modes safely

✅ **Service Requirements**
- System requirements
- Network configuration
- Running as a background service
- Auto-restart configuration
- High availability setup

✅ **Usage & Integration**
- Real-time market data streaming
- Historical data downloads
- Order execution
- Portfolio management
- Live strategy execution

✅ **Troubleshooting & Support**
- Common issues and solutions
- Debug techniques
- Getting help

### What You'll Be Able to Do

- ✅ How to install and configure TWS or IB Gateway
- ✅ How to enable API access for automated trading
- ✅ How to configure paper vs live trading modes
- ✅ How to use the Copilot Quant IBKR integration
- ✅ How to troubleshoot common issues
- ✅ Best practices for safe, reliable trading

---

## Prerequisites

### Required

1. **Interactive Brokers Account**
   - Paper trading account (free, no real money)
   - OR Live trading account (for real trading)
   - Sign up at: https://www.interactivebrokers.com

2. **Python Environment**
   - Python 3.8 or higher
   - Copilot Quant platform installed

3. **TWS or IB Gateway**
   - Download from IBKR website (see [Installation](#installation))
   - Approximately 300MB - 2GB disk space

4. **Network Access**
   - Localhost connection (127.0.0.1)
   - Or configured firewall rules for remote access

### Recommended

- Basic understanding of trading concepts
- Familiarity with Python and command line
- Trading experience (for live trading)

---

## Quick Start (5 Minutes)

**Get up and running with paper trading in 5 minutes:**

### Step 1: Configure Environment (1 min)

Copy the example environment file and set your paper trading account:

```bash
cd /path/to/copilot_quant
cp .env.example .env
```

Edit `.env` with your settings:
```bash
# Paper Trading Configuration (DEFAULT - Safe Mode)
IB_PAPER_HOST=127.0.0.1
IB_PAPER_PORT=7497              # TWS Paper Trading
IB_PAPER_CLIENT_ID=1
IB_PAPER_ACCOUNT=DUB267514      # Replace with YOUR paper account number
IB_PAPER_USE_GATEWAY=false      # Using TWS (not Gateway)
```

### Step 2: Setup TWS (2 min)

1. Download & install TWS from: https://www.interactivebrokers.com/en/trading/tws.php
2. Launch TWS and select "**Paper Trading**" mode
3. Login with your paper trading credentials

### Step 3: Enable API Access (1 min)

In TWS:
1. Go to **File** → **Global Configuration** (or press `Ctrl+Alt+F`)
2. Navigate to **API** → **Settings**
3. Check ✅ **"Enable ActiveX and Socket Clients"**
4. Verify port is **7497** (for paper trading)
5. Click **OK**

### Step 4: Test Connection (1 min)

```bash
python examples/test_ibkr_connection.py
```

**Expected output:**
```
✓ Connected successfully!
✓ Account Balance: $1,000,000.00 (paper money)
✓ Connection test passed
```

🎉 **Done!** You're now connected to IBKR paper trading.

**Next Steps:**
- Try the [Usage Examples](#usage-examples) below
- Read about [Paper vs Live Trading](#trading-modes)
- Review [Best Practices](#best-practices)

---

## Detailed Setup

### TWS vs IB Gateway

Choose the right application for your needs:

| Feature | TWS (Trader Workstation) | IB Gateway |
|---------|-------------------------|------------|
| **Type** | Full trading platform | API-only application |
| **Size** | ~1-2 GB | ~300 MB |
| **Interface** | Complete trading GUI | Minimal login window |
| **Resource Usage** | 500MB+ RAM | 100-200MB RAM |
| **Best For** | Manual + Automated trading | Automated trading only |
| **Monitoring** | Built-in charts and tools | External tools required |
| **Setup Complexity** | More complex | Simpler |

**Recommendation:**
- **Development/Testing**: Use **TWS** (easier to monitor and debug)
- **Production/Automated**: Use **IB Gateway** (lighter, more stable)

### Installation

#### Option 1: TWS (Trader Workstation)

1. **Download**: Visit https://www.interactivebrokers.com/en/trading/tws.php
2. **Select**: Choose your operating system (Windows, macOS, Linux)
3. **Install**: Run the installer and follow prompts
4. **Launch**: Find TWS in your applications and launch it

#### Option 2: IB Gateway

1. **Download**: Visit https://www.interactivebrokers.com/en/trading/ibgateway-stable.php
2. **Select**: Choose your operating system
3. **Install**: Run the installer and follow prompts
4. **Launch**: Start IB Gateway from your applications

### API Configuration

After launching TWS or IB Gateway, configure API access:

#### In TWS:

1. **Open Settings**:
   - Go to **File** → **Global Configuration**
   - Or press `Ctrl+Alt+F` (Windows) / `Cmd+Alt+F` (Mac)

2. **Navigate to API Settings**:
   - Click **API** in the left menu
   - Click **Settings** submenu

3. **Enable API Access**:
   - ✅ Check **"Enable ActiveX and Socket Clients"**
   - ✅ Check **"Allow connections from localhost only"** (recommended)
   - ⚠️ **UNCHECK** "Read-Only API" (required for trading)
   - ✅ Check "Download open orders on connection" (recommended)

4. **Configure Port**:
   - **Paper Trading**: Port `7497` (default)
   - **Live Trading**: Port `7496` (default)
   - Note: Don't change unless you have a specific reason

5. **Optional Settings**:
   - **Master API Client ID**: Leave blank (allows any client ID)
   - **Trusted IP Addresses**: Leave empty if using localhost only

6. **Save**: Click **OK** to apply changes

#### In IB Gateway:

1. **Open Settings**: Click **Configure** → **Settings** in login window
2. **API Settings**: Navigate to **API** → **Settings**
3. **Configure**: Apply same settings as TWS above
4. **Save**: Click **OK**

### Environment Setup

#### 1. Install Python Dependencies

Ensure you have the required Python packages:

```bash
# If you haven't already installed project dependencies
pip install -r requirements.txt

# Or install ib_insync specifically
pip install ib_insync>=0.9.86
```

#### 2. Configure Environment Variables

Create a `.env` file in your project root:

```bash
cp .env.example .env
```

**For Paper Trading** (recommended for testing):

```bash
# ============================================================================
# PAPER TRADING Configuration (Simulated Trading - DEFAULT)
# ============================================================================
IB_PAPER_HOST=127.0.0.1
IB_PAPER_PORT=7497              # TWS: 7497, Gateway: 4002
IB_PAPER_CLIENT_ID=1
IB_PAPER_ACCOUNT=DUB267514      # Replace with YOUR account number
IB_PAPER_USE_GATEWAY=false      # false=TWS, true=Gateway
```

**For Live Trading** (real money - use with caution):

```bash
# ============================================================================
# LIVE TRADING Configuration (Real Money - USE WITH CAUTION)
# ============================================================================
IB_LIVE_HOST=127.0.0.1
IB_LIVE_PORT=7496               # TWS: 7496, Gateway: 4001
IB_LIVE_CLIENT_ID=2             # Different from paper
IB_LIVE_ACCOUNT=U1234567        # Replace with YOUR live account
IB_LIVE_USE_GATEWAY=false
```

#### 3. Port Reference

| Application | Mode | Default Port |
|------------|------|--------------|
| TWS | Paper Trading | 7497 |
| TWS | Live Trading | 7496 |
| IB Gateway | Paper Trading | 4002 |
| IB Gateway | Live Trading | 4001 |

---

## Trading Modes

### Paper Trading (Recommended)

**What is Paper Trading?**
- Simulated trading environment with **NO REAL MONEY**
- Uses real market data (15-minute delay for free accounts)
- Perfect for testing strategies and learning
- Separate from your live account

**Features:**
- ✅ Risk-free testing
- ✅ Realistic order execution simulation
- ✅ Full API functionality
- ✅ Live market data
- ✅ Unlimited virtual funds ($1M default)

**Limitations:**
- 15-minute delayed market data (unless you have subscriptions)
- Order execution may be more optimistic than live
- Some order types may not be available
- Position size limits may differ

**Setup Paper Trading:**

1. **Get Paper Account Credentials**:
   - Login to [IBKR Client Portal](https://www.interactivebrokers.com/portal)
   - Go to **Settings** → **Account Settings**
   - Find **Paper Trading Account** section
   - Note your paper account number (e.g., DUB267514)

2. **Configure `.env`**:
   ```bash
   IB_PAPER_ACCOUNT=DUB267514  # Your paper account number
   IB_PAPER_PORT=7497          # TWS paper port
   ```

3. **Login to TWS/Gateway**:
   - Select "**Paper Trading**" mode in dropdown
   - Use your paper trading username/password
   - These are different from live credentials

4. **Connect via Code**:
   ```python
   from copilot_quant.brokers.connection_manager import IBKRConnectionManager
   
   # Connect to paper trading
   manager = IBKRConnectionManager(paper_trading=True)
   manager.connect()
   ```

### Live Trading

**⚠️ WARNING: LIVE TRADING USES REAL MONEY**

Only proceed with live trading after:
- ✅ Thoroughly testing in paper trading
- ✅ Understanding all risks involved
- ✅ Implementing proper risk management
- ✅ Starting with small position sizes

**Setup Live Trading:**

1. **Ensure Live Account is Funded**:
   - Login to [IBKR Client Portal](https://www.interactivebrokers.com/portal)
   - Verify account has sufficient funds
   - Check trading permissions are enabled

2. **Configure `.env`**:
   ```bash
   IB_LIVE_ACCOUNT=U1234567    # Your live account number
   IB_LIVE_PORT=7496           # TWS live port
   ```

3. **Login to TWS/Gateway**:
   - Select "**Live Trading**" mode
   - Use live account credentials
   - Complete 2FA if enabled

4. **Connect via Code**:
   ```python
   from copilot_quant.brokers.connection_manager import IBKRConnectionManager
   
   # Connect to LIVE trading
   manager = IBKRConnectionManager(paper_trading=False)
   manager.connect()
   ```

### Switching Between Modes

**Via Environment Variables:**

The platform reads from `.env` file and uses separate configurations:

```bash
# Paper trading config
IB_PAPER_ACCOUNT=DUB267514
IB_PAPER_PORT=7497

# Live trading config
IB_LIVE_ACCOUNT=U1234567
IB_LIVE_PORT=7496
```

**Via Code Parameter:**

```python
# Paper trading
manager = IBKRConnectionManager(paper_trading=True)

# Live trading
manager = IBKRConnectionManager(paper_trading=False)
```

**Safety Features:**
- Separate account numbers prevent accidental cross-mode trading
- Different ports ensure you connect to the right mode
- Different client IDs recommended for each mode
- Explicit `paper_trading` flag required in code

---

## Service Requirements

### System Requirements

**Hardware:**
- **CPU**: 2+ cores recommended
- **RAM**: 2GB minimum, 4GB+ recommended
- **Disk**: 500MB for Gateway, 2GB for TWS
- **Network**: Stable internet connection (10+ Mbps recommended)

**Software:**
- **Operating System**: Windows 10+, macOS 10.14+, or Linux (Ubuntu 18.04+)
- **Java**: Java Runtime Environment (JRE) 11+ (included with TWS/Gateway)
- **Python**: 3.8 or higher
- **ib_insync**: 0.9.86 or higher

### Network Requirements

**Ports:**
- Outbound connections to IBKR servers
- Localhost ports for API (7496, 7497, 4001, 4002)
- No inbound connections required (unless remote access needed)

**Firewall Rules:**
```
Allow outbound: HTTPS (443) to *.interactivebrokers.com
Allow localhost: TCP ports 7496, 7497, 4001, 4002
```

### Running TWS/Gateway as a Service

For production deployments, you may want TWS/Gateway to run as a background service:

#### Linux (systemd)

Create `/etc/systemd/system/ibgateway.service`:

```ini
[Unit]
Description=IB Gateway
After=network.target

[Service]
Type=simple
User=YOUR_USERNAME
WorkingDirectory=/home/YOUR_USERNAME/Jts
ExecStart=/home/YOUR_USERNAME/Jts/ibgateway/1019/ibgateway
Restart=on-failure
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
sudo systemctl enable ibgateway
sudo systemctl start ibgateway
```

#### Windows (Task Scheduler)

1. Open Task Scheduler
2. Create Basic Task → Name it "IB Gateway"
3. Trigger: "When the computer starts"
4. Action: "Start a program"
5. Program: Path to `ibgateway.exe`
6. Finish and test

#### macOS (launchd)

Create `~/Library/LaunchAgents/com.interactivebrokers.gateway.plist`:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.interactivebrokers.gateway</string>
    <key>ProgramArguments</key>
    <array>
        <string>/Applications/IB Gateway.app/Contents/MacOS/ibgateway</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
</dict>
</plist>
```

Load:
```bash
launchctl load ~/Library/LaunchAgents/com.interactivebrokers.gateway.plist
```

### Auto-Restart Configuration

IBKR applications automatically log out daily. Configure auto-restart:

**In TWS:**
1. **Edit** → **Global Configuration**
2. **Lock and Exit** settings
3. Enable **"Auto restart"**
4. Set **Auto logoff time**: 11:50 PM ET (default)
5. Set **Auto restart time**: 12:05 AM ET

**In IB Gateway:**
1. **Configure** → **Settings**
2. **Auto Restart** section
3. Set restart time: 12:05 AM ET

**Note**: This requires storing credentials (security consideration) or external restart script.

### High Availability Setup

For production trading systems requiring high availability:

1. **Multiple Client IDs**: Run backup connections with different client IDs
2. **Monitoring**: Implement health checks and alerts
3. **Automatic Failover**: Switch to backup connection on primary failure
4. **Logging**: Comprehensive logging for debugging
5. **Redundancy**: Consider running TWS/Gateway on separate machines

Example health check:
```python
import time
from copilot_quant.brokers.connection_manager import IBKRConnectionManager

def health_check():
    """Check if IBKR connection is healthy"""
    manager = IBKRConnectionManager(paper_trading=True)
    try:
        if manager.connect():
            # Test basic functionality
            ib = manager.get_ib()
            accounts = ib.managedAccounts()
            manager.disconnect()
            return True
    except Exception as e:
        print(f"Health check failed: {e}")
    return False

# Run health check every 5 minutes
while True:
    if not health_check():
        # Alert/restart logic here
        print("⚠️ Connection unhealthy!")
    time.sleep(300)
```

---

## Usage Examples

### Example 1: Basic Connection Test

```python
from copilot_quant.brokers.connection_manager import IBKRConnectionManager

# Create connection manager
manager = IBKRConnectionManager(paper_trading=True)

# Connect
if manager.connect():
    print("✓ Connected to IBKR")
    
    # Get IB instance
    ib = manager.get_ib()
    
    # Get account info
    accounts = ib.managedAccounts()
    print(f"Accounts: {accounts}")
    
    # Disconnect
    manager.disconnect()
else:
    print("✗ Failed to connect")
```

### Example 2: Get Account Balance

```python
from copilot_quant.brokers.interactive_brokers import IBKRBroker

# Initialize broker
broker = IBKRBroker(paper_trading=True)

# Connect
if broker.connect():
    # Get balance
    balance = broker.get_account_balance()
    
    print(f"Net Liquidation: ${balance.get('NetLiquidation', 0):,.2f}")
    print(f"Cash Balance: ${balance.get('TotalCashValue', 0):,.2f}")
    print(f"Buying Power: ${balance.get('BuyingPower', 0):,.2f}")
    
    broker.disconnect()
```

### Example 3: Get Real-Time Market Data

```python
from copilot_quant.brokers.live_market_data import IBKRLiveDataFeed

# Create data feed
feed = IBKRLiveDataFeed(paper_trading=True)

# Connect
feed.connect()

# Subscribe to symbols
feed.subscribe(['AAPL', 'MSFT', 'GOOGL'])

# Get latest price
price = feed.get_latest_price('AAPL')
print(f"AAPL current price: ${price}")

# Get historical data
historical = feed.get_historical_bars(
    symbol='AAPL',
    duration='1 M',      # 1 month
    bar_size='1 day'     # Daily bars
)
print(f"Historical data: {len(historical)} bars")

# Cleanup
feed.disconnect()
```

### Example 4: Place an Order (Paper Trading)

```python
from copilot_quant.brokers.interactive_brokers import IBKRBroker

broker = IBKRBroker(paper_trading=True)

if broker.connect():
    # Place market order
    order_result = broker.execute_order(
        symbol='AAPL',
        quantity=10,
        order_type='market',
        side='buy'
    )
    
    print(f"Order placed: {order_result}")
    
    # Get current positions
    positions = broker.get_positions()
    for pos in positions:
        print(f"{pos['symbol']}: {pos['position']} shares @ ${pos['avg_cost']}")
    
    broker.disconnect()
```

### Example 5: Live Strategy Execution

```python
from copilot_quant.backtest.live_engine import LiveStrategyEngine
from copilot_quant.strategies.my_strategy import MyStrategy

# Initialize live engine
engine = LiveStrategyEngine(
    paper_trading=True,      # Paper trading mode
    commission=0.001,        # 0.1% commission
    slippage=0.0005,        # 0.05% slippage
    update_interval=60.0     # Update every 60 seconds
)

# Add your strategy
strategy = MyStrategy()
engine.add_strategy(strategy)

# Connect and start
if engine.connect():
    print("Connected to IBKR - Starting live trading")
    
    # Start trading
    engine.start(
        symbols=['AAPL', 'MSFT', 'GOOGL'],
        lookback_days=30,
        data_interval='1d'
    )
    
    # Run until interrupted
    try:
        import time
        while True:
            time.sleep(60)
    except KeyboardInterrupt:
        print("\nStopping live trading...")
        engine.stop()
        engine.disconnect()
```

### Example 6: Using Context Manager (Recommended)

```python
from copilot_quant.brokers.connection_manager import IBKRConnectionManager

# Automatically manages connection lifecycle
with IBKRConnectionManager(paper_trading=True) as manager:
    ib = manager.get_ib()
    
    # Get account summary
    summary = ib.accountSummary()
    for item in summary:
        print(f"{item.tag}: {item.value}")
    
    # Get positions
    positions = ib.positions()
    for pos in positions:
        print(f"{pos.contract.symbol}: {pos.position}")

# Automatically disconnects here
```

---

## Advanced Configuration

### Rate Limiting

IBKR enforces rate limits. Best practices:

```python
import time
from copilot_quant.brokers.live_market_data import IBKRLiveDataFeed

feed = IBKRLiveDataFeed(paper_trading=True)
feed.connect()

# Batch historical data requests with delays
symbols = ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'META']
data = {}

for i, symbol in enumerate(symbols):
    # Add delay every 5 requests
    if i > 0 and i % 5 == 0:
        time.sleep(10)  # Wait 10 seconds
    
    data[symbol] = feed.get_historical_bars(symbol, '1 M', '1 day')
    time.sleep(1)  # Small delay between requests
```

**Rate Limits:**
- Messages: 50 per second
- Order placement: 50 per second
- Market data requests: 100 per 10 seconds
- Historical data: 60 requests per 10 minutes

### Custom Client IDs

Use different client IDs for different purposes:

```python
# Strategy A
manager_a = IBKRConnectionManager(paper_trading=True, client_id=1)

# Strategy B
manager_b = IBKRConnectionManager(paper_trading=True, client_id=2)

# Monitoring tool
manager_monitor = IBKRConnectionManager(paper_trading=True, client_id=99)
```

### Event Handlers

Implement custom event handlers:

```python
from copilot_quant.brokers.connection_manager import IBKRConnectionManager

def on_disconnect():
    print("⚠️ Disconnected from IBKR - attempting reconnect...")

def on_connect():
    print("✓ Connected to IBKR")

manager = IBKRConnectionManager(
    paper_trading=True,
    on_disconnect=on_disconnect,
    on_connect=on_connect
)

manager.connect()
```

### Logging Configuration

Enable detailed logging for debugging:

```python
import logging

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('ibkr.log'),
        logging.StreamHandler()
    ]
)

# Enable ib_insync logging
from ib_insync import util
util.logToConsole(logging.DEBUG)

# Now use the IBKR connection
from copilot_quant.brokers.connection_manager import IBKRConnectionManager
manager = IBKRConnectionManager(paper_trading=True)
manager.connect()
```

---

## Troubleshooting

### Common Issues

#### Issue 1: Connection Refused

**Error**: `Connection refused` or `Cannot connect to 127.0.0.1:7497`

**Solutions**:
1. ✅ Verify TWS/Gateway is running and logged in
2. ✅ Check API is enabled: File → Global Configuration → API → Settings
3. ✅ Confirm "Enable ActiveX and Socket Clients" is checked
4. ✅ Verify correct port (7497 for TWS paper, 7496 for live)
5. ✅ Wait 30 seconds after login before connecting
6. ✅ Check firewall isn't blocking localhost connections
7. ✅ Try restarting TWS/Gateway

**Debug steps**:
```bash
# Check if port is listening (Linux/Mac)
netstat -an | grep 7497

# Windows
netstat -an | findstr 7497
```

#### Issue 2: Authentication Failed

**Error**: `Authentication failed` or `Login failed`

**Solutions**:
1. ✅ Verify credentials are correct
2. ✅ Ensure using paper credentials for paper mode
3. ✅ Check if 2FA is enabled (approve on mobile)
4. ✅ Verify account is not locked or suspended
5. ✅ Try logging in via web portal first

#### Issue 3: Market Data Issues

**Error**: `Market data farm connection is broken`

**Solutions**:
1. ✅ Check if market is currently open
2. ✅ Verify market data subscriptions are active
3. ✅ For real-time data, ensure subscriptions are paid
4. ✅ Free accounts have 15-minute delayed data
5. ✅ Try disconnecting and reconnecting
6. ✅ Check IBKR system status: https://www.interactivebrokers.com/en/trading/system-status.php

#### Issue 4: Order Rejection

**Error**: `Order rejected` or insufficient buying power

**Solutions**:
1. ✅ Verify sufficient account balance/buying power
2. ✅ Check trading permissions for security type
3. ✅ Ensure market is open for the security
4. ✅ Verify order parameters (quantity, price valid)
5. ✅ Check "Read-Only API" is DISABLED
6. ✅ Review order precautions settings

#### Issue 5: Rate Limit Exceeded

**Error**: `Connectivity between IB and TWS has been lost` or pacing violation

**Solutions**:
1. ✅ Reduce request frequency
2. ✅ Add delays between API calls (see [Rate Limiting](#rate-limiting))
3. ✅ Implement request queuing
4. ✅ Wait 2-10 minutes before retrying
5. ✅ Use batch requests instead of individual calls

#### Issue 6: Client ID Already in Use

**Error**: `Client ID already in use`

**Solutions**:
1. ✅ Use a different client ID (1-32767)
2. ✅ Disconnect other applications using same ID
3. ✅ Wait a few seconds and retry
4. ✅ Restart TWS/Gateway if issue persists

### Debug Mode

Enable detailed logging to diagnose issues:

```python
import logging
from ib_insync import util

# Enable debug logging
logging.basicConfig(level=logging.DEBUG)
util.logToConsole(logging.DEBUG)

# Now run your code
from copilot_quant.brokers.connection_manager import IBKRConnectionManager
manager = IBKRConnectionManager(paper_trading=True)
manager.connect()
```

### Testing Connection

Quick connection test script:

```python
from ib_insync import IB
import sys

def test_connection(host='127.0.0.1', port=7497):
    print(f"Testing connection to {host}:{port}...")
    ib = IB()
    
    try:
        ib.connect(host, port, clientId=999, timeout=10)
        
        if ib.isConnected():
            print("✓ Connection successful!")
            print(f"  Accounts: {ib.managedAccounts()}")
            ib.disconnect()
            return True
        else:
            print("✗ Connection failed")
            return False
    except Exception as e:
        print(f"✗ Error: {e}")
        return False

# Test
success = test_connection()
sys.exit(0 if success else 1)
```

### Getting Help

If you're still having issues:

1. **Check documentation**:
   - [IBKR Connection Troubleshooting](IBKR_CONNECTION_TROUBLESHOOTING.md)
   - [IBKR API Documentation](https://interactivebrokers.github.io/tws-api/)

2. **Check IBKR resources**:
   - [IBKR Support](https://www.interactivebrokers.com/en/support/online.php)
   - [System Status](https://www.interactivebrokers.com/en/trading/system-status.php)

3. **Community resources**:
   - [ib_insync GitHub Issues](https://github.com/erdewit/ib_insync/issues)
   - [Copilot Quant GitHub Issues](https://github.com/harryb2088/copilot_quant/issues)

---

## Best Practices

### Security

1. **Never hardcode credentials**:
   ```python
   # ❌ DON'T DO THIS
   username = "myusername"
   password = "mypassword"
   
   # ✅ DO THIS
   import os
   username = os.getenv('IBKR_USERNAME')
   password = os.getenv('IBKR_PASSWORD')
   ```

2. **Use environment variables**: Store sensitive data in `.env` file (never commit to git)

3. **Enable 2FA**: Use two-factor authentication on your IBKR account

4. **Restrict API access**: 
   - Enable "Allow connections from localhost only"
   - Only add trusted IPs if remote access needed

5. **Monitor account activity**: Set up alerts for large orders/withdrawals

### Risk Management

1. **Start with paper trading**: Always test thoroughly before going live

2. **Implement position limits**:
   ```python
   MAX_POSITION_SIZE = 1000  # shares
   MAX_TOTAL_EXPOSURE = 50000  # dollars
   ```

3. **Use stop-loss orders**: Protect against large losses

4. **Validate orders before submission**:
   ```python
   def validate_order(symbol, quantity, price, buying_power):
       order_value = quantity * price
       if order_value > buying_power:
           raise ValueError("Insufficient buying power")
       if quantity > MAX_POSITION_SIZE:
           raise ValueError("Position size too large")
       return True
   ```

5. **Log all trading activity**: Maintain audit trail

### Performance

1. **Use connection pooling**: Reuse connections instead of reconnecting

2. **Batch requests**: Group multiple requests together

3. **Implement caching**: Cache frequently accessed data

4. **Rate limit proactively**: Don't wait for IBKR to throttle you

5. **Monitor performance**: Track API latency and throughput

### Reliability

1. **Implement auto-reconnection**: Handle disconnections gracefully

2. **Use health checks**: Regularly verify connection is alive

3. **Handle errors gracefully**: Don't let one error crash your system

4. **Implement circuit breakers**: Stop trading if error rate is too high

5. **Use context managers**: Ensure resources are properly cleaned up
   ```python
   with IBKRConnectionManager(paper_trading=True) as manager:
       # Your code here
       pass
   # Automatically disconnects
   ```

### Testing

1. **Test in paper trading first**: Always

2. **Test edge cases**: Market closed, network issues, invalid orders

3. **Test failover scenarios**: What happens when TWS crashes?

4. **Use mock data for unit tests**: Don't rely on live connection for tests

5. **Monitor paper trading performance**: Ensure strategies work as expected

---

## Additional Resources

### Official Documentation

- [IBKR API Reference](https://interactivebrokers.github.io/tws-api/)
- [TWS User Guide](https://www.interactivebrokers.com/en/trading/tws-guide.php)
- [ib_insync Documentation](https://ib-insync.readthedocs.io/)
- [IBKR Webinars](https://www.interactivebrokers.com/en/index.php?f=7235)

### Copilot Quant Documentation Map

This comprehensive guide is part of a larger documentation ecosystem. Here's how all the IBKR docs fit together:

```
📚 IBKR Documentation Structure
│
├── 🎯 IBKR_COMPREHENSIVE_GUIDE.md (YOU ARE HERE) ⭐
│   └── Best for: New users, complete setup from scratch
│       • Quick start (5 minutes)
│       • All essential information in one place
│       • Step-by-step tutorials
│       • Troubleshooting
│
├── 📘 ibkr_setup_guide.md
│   └── Best for: Developers needing technical details
│       • Detailed API reference
│       • Advanced configuration options
│       • Rate limits and restrictions
│       • Advanced code examples
│
├── 🔌 IBKR_CONNECTION_MANAGER.md
│   └── Best for: Understanding connection management
│       • Connection manager API
│       • Auto-reconnection features
│       • Health monitoring
│       • Event handlers
│
├── 🔧 IBKR_CONNECTION_TROUBLESHOOTING.md
│   └── Best for: Solving connection issues
│       • Common problems and solutions
│       • Debug techniques
│       • Network diagnostics
│
├── 🚀 LIVE_INTEGRATION_GUIDE.md
│   └── Best for: Integrating with strategy engine
│       • Live trading integration
│       • Adapter pattern
│       • Strategy execution
│
├── 📡 live_market_data_guide.md
│   └── Best for: Working with market data
│       • Real-time data streaming
│       • Historical data downloads
│       • Subscription management
│
└── ⚡ examples/IBKR_SETUP.md
    └── Best for: Quick 5-minute setup
        • Minimal instructions
        • Quick reference
```

**Which guide should you read?**

- **Never used IBKR before?** → Start with this guide (IBKR_COMPREHENSIVE_GUIDE.md)
- **Already have IBKR setup?** → Jump to [Usage Examples](#usage-examples)
- **Having connection issues?** → See [Troubleshooting](#troubleshooting) or IBKR_CONNECTION_TROUBLESHOOTING.md
- **Need API details?** → See ibkr_setup_guide.md
- **Want to integrate with strategies?** → See LIVE_INTEGRATION_GUIDE.md
- **Working with market data?** → See live_market_data_guide.md

### Copilot Quant Specific Docs

- [IBKR Setup Guide](ibkr_setup_guide.md) - Detailed technical setup
- [IBKR Connection Manager](IBKR_CONNECTION_MANAGER.md) - Connection management
- [Live Integration Guide](LIVE_INTEGRATION_GUIDE.md) - Live trading integration
- [Live Market Data Guide](live_market_data_guide.md) - Market data streaming
- [Quick Setup](../examples/IBKR_SETUP.md) - Quick start guide

### Useful Links

- [IBKR Client Portal](https://www.interactivebrokers.com/portal)
- [Market Data Subscriptions](https://www.interactivebrokers.com/en/trading/market-data.php)
- [Paper Trading Setup](https://www.interactivebrokers.com/en/trading/free-trial.php)
- [System Status](https://www.interactivebrokers.com/en/trading/system-status.php)

### Community Resources

- [ib_insync GitHub](https://github.com/erdewit/ib_insync)
- [IBKR Reddit](https://www.reddit.com/r/interactivebrokers/)
- [Copilot Quant Issues](https://github.com/harryb2088/copilot_quant/issues)

### Code Examples

All examples are in the `examples/` directory:
- `test_ibkr_connection.py` - Basic connection test
- `ibkr_live_data_example.py` - Market data streaming
- See [Usage Examples](#usage-examples) above

---

## Quick Reference

### Common Commands

```bash
# Test connection
python examples/test_ibkr_connection.py

# Run live strategy
python examples/run_live_strategy.py

# View logs
tail -f ibkr.log
```

### Common Code Snippets

```python
# Connect to paper trading
from copilot_quant.brokers.connection_manager import IBKRConnectionManager
manager = IBKRConnectionManager(paper_trading=True)
manager.connect()

# Get account balance
from copilot_quant.brokers.interactive_brokers import IBKRBroker
broker = IBKRBroker(paper_trading=True)
broker.connect()
balance = broker.get_account_balance()

# Get real-time data
from copilot_quant.brokers.live_market_data import IBKRLiveDataFeed
feed = IBKRLiveDataFeed(paper_trading=True)
feed.connect()
price = feed.get_latest_price('AAPL')
```

### Port Quick Reference

| Mode | TWS | Gateway |
|------|-----|---------|
| Paper | 7497 | 4002 |
| Live | 7496 | 4001 |

---

## Pre-Live Trading Checklist

Before going live with real money, verify:

- [ ] Thoroughly tested in paper trading (minimum 1 month)
- [ ] Error handling implemented for all edge cases
- [ ] Rate limiting configured and tested
- [ ] Position limits and risk controls in place
- [ ] Stop-loss orders implemented
- [ ] Credentials stored securely (not in code)
- [ ] Two-factor authentication enabled on account
- [ ] API access restricted to localhost or trusted IPs
- [ ] Logging and monitoring configured
- [ ] Emergency stop mechanism implemented
- [ ] Risk management rules defined and tested
- [ ] Account alerts configured in IBKR portal
- [ ] Start with small position sizes
- [ ] Have manual override capability
- [ ] Reviewed all code for potential bugs
- [ ] Have rollback/shutdown plan

---

**Last Updated**: 2026-02-19  
**Version**: 2.0  
**Status**: Comprehensive Guide

---

**⚠️ Disclaimer**: Trading involves substantial risk of loss and is not suitable for all investors. This guide is for educational purposes only. Always test thoroughly in paper trading before using real money. The authors and contributors are not responsible for any financial losses incurred through the use of this guide or associated software. Past performance is not indicative of future results.
