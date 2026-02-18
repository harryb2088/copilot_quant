# IBKR Paper/Live Trading Sync Behavior and Quirks

This document describes observed behavior, quirks, and best practices when syncing account, position, and balance data from Interactive Brokers using the ib_insync library.

## Account Balance Sync

### Expected Behavior
- Account values are available via `ib.accountValues()` and `ib.accountSummary()`
- Real-time updates delivered via `accountValueEvent`
- Paper trading and live trading behave similarly for account data

### Observed Quirks

#### 1. accountValues() vs accountSummary()
- `accountValues()`: Returns all account tags for the specific account
- `accountSummary()`: Returns summary values across all accounts
- **Best Practice**: Use `accountValues()` for single-account tracking, `accountSummary()` for multi-account

#### 2. Real-Time Update Frequency
- Account values update approximately every 3 seconds during market hours
- Updates may be slower or batched outside market hours
- Some values (like P&L) update more frequently than others (like margin requirements)

#### 3. Paper Trading Account Values
- Paper trading accounts have slightly different available tags than live accounts
- Some margin-related fields may show 0 or placeholder values in paper trading
- Net Liquidation, Total Cash Value, and Buying Power are reliable in both modes

#### 4. Currency-Specific Values
- Most account values are returned with a currency field (usually "USD")
- Some tags return "BASE" as currency for non-currency-specific values
- Always check the currency field when processing account values

#### 5. Initial Sync Timing
- After connection, it may take 1-2 seconds for account values to be fully populated
- First `accountValues()` call may return incomplete data
- **Best Practice**: Wait briefly after connection or use `reqAccountUpdates()` to ensure data is ready

### Common Account Value Tags

Essential tags that work reliably in both paper and live:
- `NetLiquidation`: Total account value (most important)
- `TotalCashValue`: Available cash
- `BuyingPower`: Available buying power
- `GrossPositionValue`: Total value of all positions
- `UnrealizedPnL`: Unrealized profit/loss
- `RealizedPnL`: Realized profit/loss

Additional useful tags (may vary by account type):
- `AvailableFunds`: Available funds for trading
- `ExcessLiquidity`: Excess liquidity
- `FullMaintMarginReq`: Maintenance margin requirement
- `FullInitMarginReq`: Initial margin requirement

## Position Sync

### Expected Behavior
- Positions available via `ib.positions()`
- Real-time updates delivered via `positionEvent`
- Each position includes symbol, quantity, average cost, and account

### Observed Quirks

#### 1. Position Updates Timing
- Position updates occur after order fills
- May have a 1-2 second delay between fill and position update
- **Best Practice**: Don't rely on immediate position updates; use order fill events for immediate feedback

#### 2. Average Cost Calculation
- Average cost includes commissions in some cases but not others
- Paper trading vs live may calculate average cost differently
- **Best Practice**: Track your own average cost if precision is critical

#### 3. Zero Positions
- When a position is fully closed, it may not immediately disappear from positions list
- May show as quantity=0 briefly before being removed
- **Best Practice**: Filter positions where `position != 0`

#### 4. Market Price in Position Object
- The Position object from IBKR does NOT include current market price
- Must separately request market data to get current price
- **Best Practice**: Use `reqMktData()` with snapshot=True to get current prices

#### 5. Multiple Accounts
- If managing multiple accounts, positions are account-specific
- Must filter by account when working with multi-account setups
- Position events include the account field

### Position P&L Calculation

The Position object provides:
- `position`: Number of shares (positive=long, negative=short)
- `avgCost`: Average cost per share
- `marketPrice`: NOT included in position object
- `marketValue`: NOT included in position object

To calculate P&L:
```python
# Cost basis
cost_basis = position.position * position.avgCost

# Get current market price
ticker = ib.reqMktData(position.contract, snapshot=True)
market_price = ticker.marketPrice()

# Calculate P&L
market_value = position.position * market_price
unrealized_pnl = market_value - cost_basis
```

## Market Data for Positions

### Real-Time Market Data Requirements

#### Paper Trading
- Paper trading accounts receive **delayed** market data by default
- Typically 15-minute delayed quotes
- Real-time data requires market data subscription
- **Quirk**: Some symbols may show real-time data in paper trading, but this is not guaranteed

#### Live Trading
- Live accounts also receive delayed data by default
- Must subscribe to market data feeds for real-time quotes
- Different feeds for different exchanges (NYSE, NASDAQ, etc.)

### Snapshot vs Streaming Data

```python
# Snapshot (one-time price)
ticker = ib.reqMktData(contract, snapshot=True)
ib.sleep(0.1)  # Brief wait for data
price = ticker.marketPrice()
ib.cancelMktData(contract)  # Clean up

# Streaming (continuous updates)
ticker = ib.reqMktData(contract)
# Updates delivered via ticker.updateEvent
```

**Best Practice**: Use snapshots for position valuation, streaming for active monitoring

## Reconciliation and Discrepancy Detection

### Sources of Discrepancies

1. **Timing Issues**
   - Order fills may not immediately update positions
   - Account values may lag by a few seconds
   - **Solution**: Allow small time buffer for updates

2. **Rounding Differences**
   - IBKR may round values differently than expected
   - Especially for fractional shares (if supported)
   - **Solution**: Use tolerance of 0.01 for float comparisons

3. **External Changes**
   - Corporate actions (splits, dividends)
   - Manual trades placed outside the platform
   - Account deposits/withdrawals
   - **Solution**: Regular full reconciliation, flag unexpected changes

4. **API Limitations**
   - Some account values update less frequently
   - Delayed market data affects position valuations
   - **Solution**: Don't rely on sub-second accuracy

### Recommended Reconciliation Strategy

```python
# 1. Full sync on connection
account_mgr.sync_account_state()
position_mgr.sync_positions()

# 2. Real-time updates via events
account_mgr.start_monitoring()
position_mgr.start_monitoring()

# 3. Periodic full reconciliation (every 15 minutes)
def periodic_reconciliation():
    account_mgr.sync_account_state()
    position_mgr.sync_positions()
    # Check for discrepancies
    # Flag significant differences

# 4. Log all changes
# Both managers log changes automatically
change_log = account_mgr.get_change_log()
position_log = position_mgr.get_change_log()
```

### Discrepancy Thresholds

Recommended tolerances:
- Account balance: $0.01 (1 cent)
- Position quantity: 0.0001 shares
- Position value: $1.00
- P&L: $0.10

## Connection and Reconnection

### Connection Stability
- TWS/Gateway connections are generally stable
- May disconnect during TWS updates or system maintenance
- Auto-reconnect is essential for production use

### Data After Reconnection
- Account values repopulate automatically after reconnect
- Positions repopulate automatically
- Event subscriptions (accountValueEvent, positionEvent) must be re-registered
- **Best Practice**: ConnectionManager handles auto-reconnect; managers should re-subscribe on reconnect

### Reconnect Event Handlers

```python
def on_reconnect():
    # Re-sync data
    account_mgr.sync_account_state()
    position_mgr.sync_positions()
    
    # Re-start monitoring
    account_mgr.start_monitoring()
    position_mgr.start_monitoring()

connection_mgr.add_connect_handler(on_reconnect)
```

## Performance Considerations

### API Rate Limits
- TWS API has rate limits on requests
- Excessive market data requests can trigger pacing violations
- **Best Practice**: Use snapshot market data sparingly; batch requests when possible

### Update Frequency
- Account values update every ~3 seconds
- Position updates occur on changes
- Don't poll more frequently than necessary
- **Best Practice**: Use event-driven updates instead of polling

### Data Volume
- Positions list grows with portfolio size
- Account values list is relatively fixed
- Keep change logs bounded (max 1000 entries recommended)

## Testing Recommendations

### Paper Trading Testing
1. Create positions manually in TWS
2. Verify position sync detects them
3. Close positions and verify sync
4. Test account balance updates with deposits/withdrawals

### Live Trading Testing
1. Start with small positions
2. Monitor sync accuracy closely
3. Verify P&L calculations match TWS reports
4. Test during market hours and after-hours

### Automated Testing
- Use mock IBKR data for unit tests
- Cannot fully replicate IBKR behavior without actual connection
- Integration tests require paper trading account
- Document any behavior differences between paper and live

## Known Limitations

1. **No Historical Position Data**
   - IBKR API doesn't provide historical positions directly
   - Must track changes in your own database

2. **No Intraday P&L History**
   - Real-time P&L only; no intraday snapshots from API
   - Must capture and store if needed

3. **Limited Options Support**
   - Position manager focuses on stocks
   - Options positions have additional complexity (Greeks, etc.)
   - May need separate options position manager

4. **No Multi-Currency P&L**
   - Multi-currency positions require currency conversion
   - IBKR provides currency-specific values but not consolidated

5. **Margin Requirements**
   - Margin calculation is complex and varies by account type
   - IBKR provides values but calculation logic is opaque

## Best Practices Summary

1. **Always use event-driven updates** instead of polling
2. **Implement periodic full reconciliation** (every 15 minutes)
3. **Use tolerances** when comparing values (0.01 for dollars)
4. **Log all changes** for audit trail and debugging
5. **Handle reconnections gracefully** with auto-sync
6. **Don't assume immediate updates** - allow small delays
7. **Use snapshot market data** for position valuation
8. **Keep change logs bounded** to avoid memory issues
9. **Test thoroughly in paper trading** before going live
10. **Monitor for discrepancies** and alert on significant differences

## References

- [IB API Documentation](https://interactivebrokers.github.io/tws-api/)
- [ib_insync Documentation](https://ib-insync.readthedocs.io/)
- [IBKR Account Values](https://interactivebrokers.github.io/tws-api/account_values.html)
- [IBKR Positions](https://interactivebrokers.github.io/tws-api/positions.html)
