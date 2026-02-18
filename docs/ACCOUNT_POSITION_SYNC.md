# IBKR Account & Position Sync

This module provides comprehensive account and position synchronization for Interactive Brokers using the ib_insync library.

## Features

### Account Manager (`IBKRAccountManager`)

- ✅ Load account balances and buying power on startup
- ✅ Real-time account value updates via event callbacks
- ✅ Comprehensive account summary with all key metrics
- ✅ Change detection and logging
- ✅ Discrepancy flagging between expected and actual values
- ✅ Support for custom update callbacks

### Position Manager (`IBKRPositionManager`)

- ✅ Load positions on startup
- ✅ Real-time position updates via event callbacks
- ✅ Position P&L tracking (realized and unrealized)
- ✅ Position change detection and logging
- ✅ Discrepancy flagging for position mismatches
- ✅ Support for long/short position filtering
- ✅ Support for custom update callbacks

## Quick Start

### Basic Usage

```python
from copilot_quant.brokers import IBKRBroker

# Initialize broker with managers enabled
broker = IBKRBroker(
    paper_trading=True,
    enable_account_manager=True,
    enable_position_manager=True
)

# Connect
broker.connect()

# Access managers
account_mgr = broker.account_manager
position_mgr = broker.position_manager

# Get account summary
summary = account_mgr.get_account_summary()
print(f"Net Liquidation: ${summary.net_liquidation:,.2f}")
print(f"Buying Power: ${summary.buying_power:,.2f}")

# Get positions
positions = position_mgr.get_positions()
for pos in positions:
    print(f"{pos.symbol}: {pos.quantity} shares, P&L: ${pos.unrealized_pnl:+,.2f}")

# Disconnect
broker.disconnect()
```

### Real-Time Monitoring

```python
# Define callbacks
def on_account_update(summary):
    print(f"Account updated: Net Liq = ${summary.net_liquidation:,.2f}")

def on_position_update(positions):
    print(f"Positions updated: {len(positions)} positions")

# Register callbacks
account_mgr.register_update_callback(on_account_update)
position_mgr.register_update_callback(on_position_update)

# Start monitoring
broker.start_real_time_monitoring()

# ... monitoring happens in background ...

# Stop monitoring
broker.stop_real_time_monitoring()
```

### Using Managers Directly

```python
from copilot_quant.brokers import (
    IBKRConnectionManager,
    IBKRAccountManager,
    IBKRPositionManager
)

# Create connection
conn_mgr = IBKRConnectionManager(paper_trading=True)
conn_mgr.connect()

# Create managers
account_mgr = IBKRAccountManager(conn_mgr)
position_mgr = IBKRPositionManager(conn_mgr)

# Use managers...
```

## Account Manager API

### Key Methods

#### `get_account_summary(force_refresh=False)`
Get comprehensive account summary.

Returns `AccountSummary` with:
- `net_liquidation`: Total account value
- `total_cash_value`: Available cash
- `buying_power`: Available buying power
- `unrealized_pnl`: Unrealized P&L
- `realized_pnl`: Realized P&L
- `margin_available`: Available margin
- `gross_position_value`: Total position value
- `timestamp`: When snapshot was taken

#### `get_account_value(tag, currency="USD")`
Get specific account value by tag.

Common tags:
- `NetLiquidation`
- `TotalCashValue`
- `BuyingPower`
- `UnrealizedPnL`
- `RealizedPnL`
- `AvailableFunds`
- `GrossPositionValue`

#### `get_all_account_values()`
Get all account values as a dictionary.

#### `sync_account_state()`
Manually trigger a full account sync.

#### `start_monitoring()` / `stop_monitoring()`
Start/stop real-time account monitoring.

#### `register_update_callback(callback)` / `unregister_update_callback(callback)`
Register/unregister callbacks for account updates.

Callback signature: `def callback(summary: AccountSummary) -> None`

#### `get_change_log(max_entries=100)`
Get recent account change history.

## Position Manager API

### Key Methods

#### `get_positions(force_refresh=False)`
Get all current positions.

Returns list of `Position` objects with:
- `symbol`: Stock symbol
- `quantity`: Number of shares (positive=long, negative=short)
- `avg_cost`: Average cost per share
- `market_price`: Current market price
- `market_value`: Current market value
- `unrealized_pnl`: Unrealized P&L
- `cost_basis`: Total cost basis (property)
- `pnl_percentage`: P&L as percentage (property)

#### `get_position(symbol, force_refresh=False)`
Get position for a specific symbol.

#### `has_position(symbol)`
Check if we have a position in a symbol.

#### `get_total_market_value()`
Get total market value of all positions.

#### `get_total_unrealized_pnl()`
Get total unrealized P&L across all positions.

#### `get_long_positions()` / `get_short_positions()`
Get long or short positions only.

#### `sync_positions()`
Manually trigger a full position sync.

#### `start_monitoring()` / `stop_monitoring()`
Start/stop real-time position monitoring.

#### `register_update_callback(callback)` / `unregister_update_callback(callback)`
Register/unregister callbacks for position updates.

Callback signature: `def callback(positions: List[Position]) -> None`

#### `flag_discrepancy(symbol, expected_quantity, actual_quantity)`
Flag a discrepancy between expected and actual position.

#### `get_change_log(max_entries=100)`
Get recent position change history.

## Data Models

### AccountSummary

```python
@dataclass
class AccountSummary:
    account_id: str
    net_liquidation: float = 0.0
    total_cash_value: float = 0.0
    buying_power: float = 0.0
    unrealized_pnl: float = 0.0
    realized_pnl: float = 0.0
    margin_available: float = 0.0
    gross_position_value: float = 0.0
    timestamp: datetime
    raw_values: Dict[str, Any]
```

### Position

```python
@dataclass
class Position:
    symbol: str
    quantity: float
    avg_cost: float
    market_price: float = 0.0
    market_value: float = 0.0
    unrealized_pnl: float = 0.0
    realized_pnl: float = 0.0
    account_id: str = ""
    timestamp: datetime
    
    @property
    def cost_basis(self) -> float
    
    @property
    def pnl_percentage(self) -> float
```

### PositionChange

```python
@dataclass
class PositionChange:
    timestamp: datetime
    symbol: str
    change_type: str  # "opened", "closed", "increased", "decreased", "discrepancy"
    previous_quantity: float = 0.0
    new_quantity: float = 0.0
    previous_value: float = 0.0
    new_value: float = 0.0
    pnl_impact: float = 0.0
```

## Synchronization Strategy

### On Startup
1. Initial full sync when managers are initialized
2. Account values loaded from `ib.accountValues()`
3. Positions loaded from `ib.positions()`

### Real-Time Updates
1. Subscribe to IBKR events (`accountValueEvent`, `positionEvent`)
2. Updates delivered automatically to registered callbacks
3. Internal state updated on each event

### Periodic Reconciliation
Recommended to run periodic full syncs for reconciliation:

```python
import time

def periodic_sync():
    while running:
        time.sleep(900)  # Every 15 minutes
        account_mgr.sync_account_state()
        position_mgr.sync_positions()
```

### Discrepancy Detection
- Account changes logged automatically
- Position changes logged automatically
- Manual discrepancy flagging available via `flag_discrepancy()`

## Change Logging

Both managers maintain change logs:

```python
# Get account change log
account_changes = account_mgr.get_change_log(max_entries=10)
for change in account_changes:
    print(f"{change['field']}: ${change['previous']} → ${change['current']}")

# Get position change log
position_changes = position_mgr.get_change_log(max_entries=10)
for change in position_changes:
    print(f"{change.symbol}: {change.change_type}")
```

Change logs are automatically bounded to prevent memory issues (max 1000 entries).

## Examples

See `examples/account_position_sync_example.py` for a comprehensive example showing:
- Account summary retrieval
- Position tracking
- Real-time monitoring
- Change detection
- Manual sync

Run it with:
```bash
python examples/account_position_sync_example.py
```

## IBKR Quirks and Behavior

See `docs/IBKR_SYNC_QUIRKS.md` for detailed documentation on:
- Account value update frequency
- Position sync timing
- Market data requirements
- Reconciliation best practices
- Known limitations
- Testing recommendations

## Testing

Comprehensive unit tests are available:

```bash
# Test account manager
python -m unittest tests.test_brokers.test_account_manager

# Test position manager
python -m unittest tests.test_brokers.test_position_manager
```

## Requirements

- `ib_insync>=0.9.86`
- Active IBKR account (paper or live)
- TWS or IB Gateway running
- API connections enabled

## Configuration

Managers are automatically initialized when creating `IBKRBroker`:

```python
broker = IBKRBroker(
    paper_trading=True,
    enable_account_manager=True,   # Enable account manager
    enable_position_manager=True   # Enable position manager
)
```

To disable managers:
```python
broker = IBKRBroker(
    paper_trading=True,
    enable_account_manager=False,
    enable_position_manager=False
)
```

## Error Handling

Managers handle errors gracefully:
- Failed syncs return `False`
- Errors logged via Python logging
- Callbacks wrapped in try/except
- Partial data still available on errors

## Performance Considerations

- Account values update every ~3 seconds
- Position updates occur on changes
- Change logs bounded to 1000 entries
- Use event-driven updates instead of polling
- Market data requests are throttled

## Thread Safety

⚠️ **Warning**: Managers are NOT thread-safe. Use from the same thread that runs the event loop, or implement your own synchronization.

## Related Documentation

- [IB API Documentation](https://interactivebrokers.github.io/tws-api/)
- [ib_insync Documentation](https://ib-insync.readthedocs.io/)
- [Connection Manager](../copilot_quant/brokers/connection_manager.py)
- [IBKR Sync Quirks](./IBKR_SYNC_QUIRKS.md)
