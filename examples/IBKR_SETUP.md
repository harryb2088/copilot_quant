# Interactive Brokers Paper Trading Setup

This directory contains a working example for testing your Interactive Brokers paper trading connection.

## Quick Start

### 1. Prerequisites

- Python 3.8+
- Interactive Brokers account (paper trading or live)
- TWS (Trader Workstation) or IB Gateway installed and running

### 2. Install Dependencies

```bash
pip install ib_insync>=0.9.86
```

Or install all project dependencies:
```bash
pip install -r requirements.txt
```

### 3. Configure TWS/IB Gateway

Before running the test, you must configure TWS or IB Gateway:

#### Option A: Using TWS (Trader Workstation)

1. Launch TWS
2. Login with your paper trading credentials
3. Go to **File** → **Global Configuration** (or press `Ctrl+Alt+F`)
4. Navigate to **API** → **Settings**
5. Enable the following:
   - ✅ **Enable ActiveX and Socket Clients**
   - ✅ **Allow connections from localhost only** (recommended)
6. Verify the socket port:
   - Paper Trading: **7497** (default)
   - Live Trading: **7496** (default)
7. Click **OK** to save

#### Option B: Using IB Gateway

1. Launch IB Gateway
2. Select **Paper Trading** mode
3. Login with your credentials
4. Click **Configure** → **Settings**
5. Navigate to **API** → **Settings**
6. Enable the following:
   - ✅ **Enable ActiveX and Socket Clients**
   - ✅ **Allow connections from localhost only** (recommended)
7. Verify the socket port:
   - Paper Trading: **4002** (default)
   - Live Trading: **4001** (default)
8. Click **OK** to save

### 4. Run the Test

```bash
python examples/test_ibkr_connection.py
```

Expected output:
```
======================================================================
Interactive Brokers Paper Trading Connection Test
======================================================================

Configuration:
  Paper Trading: True
  Application: TWS
  Expected Port: 7497

Step 1: Creating broker instance...
✓ Broker instance created

Step 2: Connecting to Interactive Brokers...
✓ Connected successfully!

Step 3: Retrieving account balance...
✓ Account Balance:
     NetLiquidation     : $    1,000,000.00
     TotalCashValue     : $    1,000,000.00
     BuyingPower        : $    4,000,000.00

Step 4: Retrieving current positions...
✓ No open positions

Step 5: Retrieving open orders...
✓ Found 0 open order(s)

Step 6: Order placement (example - disabled for safety)
  To enable, uncomment the code below and modify as needed.

Step 7: Disconnecting from IBKR...
✓ Disconnected

======================================================================
✅ All tests completed successfully!
======================================================================
```

## Configuration Options

Edit `test_ibkr_connection.py` to customize:

```python
# Use IB Gateway instead of TWS
USE_GATEWAY = True

# Change client ID if running multiple instances
client_id=2
```

## Port Reference

| Application | Mode | Port |
|------------|------|------|
| TWS | Paper Trading | 7497 |
| TWS | Live Trading | 7496 |
| IB Gateway | Paper Trading | 4002 |
| IB Gateway | Live Trading | 4001 |

## Troubleshooting

### Connection Failed

**Error:** "Failed to connect to IBKR"

**Solutions:**
1. Verify TWS/Gateway is running and logged in
2. Check API is enabled (see configuration steps above)
3. Confirm correct port:
   - `7497` for TWS paper trading
   - `4002` for Gateway paper trading
4. Wait 30 seconds after logging in before connecting
5. Check firewall isn't blocking the connection
6. Try a different client ID (1-999)

### Authentication Failed

**Error:** "Authentication failed"

**Solutions:**
1. Verify you're using paper trading credentials for paper mode
2. Check if 2FA is enabled (approve on mobile if required)
3. Ensure account is not locked or suspended

### Market Data Errors

**Error:** "Market data farm connection is broken"

**Solutions:**
1. Check if market is open
2. For real-time data, ensure subscriptions are active
3. Free accounts get 15-minute delayed data
4. Disconnect and reconnect

### Rate Limit Exceeded

**Error:** "Connectivity between IB and TWS has been lost"

**Solutions:**
1. Reduce request frequency
2. Add delays between API calls
3. Wait 2-10 minutes before retrying

## Next Steps

Once the test passes:

1. **Review the code**: Look at `copilot_quant/brokers/interactive_brokers.py` to see the implementation
2. **Test order placement**: Uncomment the order placement code in the test script
3. **Integrate with strategies**: Use `IBKRBroker` in your trading strategies
4. **Read the full guide**: See `docs/ibkr_setup_guide.md` for complete documentation

## Security Notes

- **Never commit credentials** to version control
- Use environment variables for sensitive data
- Test thoroughly in paper trading before going live
- Implement proper risk management (stop losses, position limits)
- Monitor your account regularly

## Additional Resources

- [Full IBKR Setup Guide](../docs/ibkr_setup_guide.md)
- [IBKR API Documentation](https://interactivebrokers.github.io/tws-api/)
- [ib_insync Documentation](https://ib-insync.readthedocs.io/)
- [Copilot Quant Documentation](../docs/README.md)

## Support

For issues:
- IBKR API: [IBKR Support](https://www.interactivebrokers.com/en/support/online.php)
- ib_insync: [GitHub Issues](https://github.com/erdewit/ib_insync/issues)
- Copilot Quant: [GitHub Issues](https://github.com/harryb2088/copilot_quant/issues)
