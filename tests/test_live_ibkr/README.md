# Live IBKR API Tests

⚠️ **These tests require a live connection to an IBKR paper trading account.**

## Prerequisites

1. **IB Gateway or TWS** running and configured for paper trading
2. **Paper Trading Account** from Interactive Brokers
3. **Connection Details** properly configured

## Setup

### 1. Start IB Gateway or TWS

- For paper trading, use port **7497** (TWS) or **4002** (Gateway)
- Enable API connections in the settings
- Accept API connections from localhost

### 2. Configure Environment Variables

Create a `.env` file or set these environment variables:

```bash
IB_HOST=127.0.0.1
IB_PORT=7497
IB_CLIENT_ID=1
IB_PAPER_ACCOUNT=DU123456  # Your paper trading account number
```

### 3. Run Live API Tests

By default, live API tests are **skipped** in the test suite. To run them explicitly:

```bash
# Run only live API tests
pytest -m live_api tests/test_live_ibkr/

# Run with verbose output
pytest -m live_api tests/test_live_ibkr/ -v

# Run specific test
pytest -m live_api tests/test_live_ibkr/test_live_connection.py::TestLiveConnection::test_live_connect -v
```

## Test Markers

All tests in this directory use the `@pytest.mark.live_api` decorator to indicate they require a live connection.

## Test Categories

### Connection Tests (`test_live_connection.py`)
- Verify connection to paper trading account
- Test connection parameters
- Validate account access

### Order Tests (`test_live_orders.py`)
- Place and cancel orders in paper account
- Verify order status updates
- Test order fills (with small quantities)

### Market Data Tests (`test_live_market_data.py`)
- Request real-time market data
- Verify data streaming
- Test different data types

## Safety

- **Always use paper trading accounts** for these tests
- Tests use small order quantities (1-10 shares)
- All orders are market orders that fill immediately
- Tests clean up orders after execution

## Troubleshooting

### Connection Refused
- Ensure IB Gateway/TWS is running
- Check that API is enabled in settings
- Verify port number matches (7497 for paper TWS)

### Authentication Failed
- Verify account credentials
- Check paper trading account is active
- Ensure client ID is unique

### Permission Denied
- Enable API connections in TWS/Gateway settings
- Add localhost to trusted IPs
- Check firewall settings

## CI/CD

These tests are **excluded** from CI/CD pipelines by default. They should only be run manually or in dedicated test environments with IB Gateway access.
