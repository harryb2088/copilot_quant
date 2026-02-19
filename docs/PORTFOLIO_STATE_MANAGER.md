# Portfolio State Manager Documentation

## Overview
The `PortfolioStateManager` maintains persistent local portfolio state with synchronization to IBKR. It stores NAV, drawdown, position snapshots, and ensures state survives restarts. This provides historical queryable data for analytics and ensures no positions or state are lost during system crashes.

## Basic Usage

### Initialization

```python
from copilot_quant.live import PortfolioStateManager
from copilot_quant.brokers.live_broker_adapter import LiveBrokerAdapter

# Initialize broker adapter
broker = LiveBrokerAdapter(paper_trading=True)
broker.connect()

# Initialize portfolio state manager
manager = PortfolioStateManager(
    broker=broker,
    database_url="postgresql://user:pass@localhost/portfolio",
    sync_interval_minutes=5,
    snapshot_interval_minutes=15
)

# Initialize and sync with broker
if manager.initialize():
    print("Portfolio state manager initialized")
    
    # State is automatically synced and snapshots taken
    # according to configured intervals
```

### Manual Operations

```python
# Force sync with broker
manager.sync_with_broker()

# Take snapshot
manager.take_snapshot()

# Get current state
state = manager.get_current_state()
print(f"NAV: ${state.nav:,.2f}")
print(f"Drawdown: {state.drawdown:.2%}")

# Get equity curve
equity_curve = manager.get_equity_curve(days=30)
print(equity_curve)
```

## Key Features

### 1. Portfolio State Persistence

Stores comprehensive portfolio state:

```python
@dataclass
class PortfolioSnapshot:
    timestamp: datetime       # Snapshot time
    nav: float               # Net Asset Value
    cash: float              # Cash balance
    equity_value: float      # Total equity value
    num_positions: int       # Number of positions
    drawdown: float          # Current drawdown from peak
    daily_pnl: float         # Daily P&L
```

### 2. Position Snapshots

Stores detailed position information:

```python
# For each position in the snapshot:
- symbol: Stock symbol
- quantity: Number of shares
- avg_cost: Average cost per share
- current_price: Current market price
- market_value: Total market value
- unrealized_pnl: Unrealized profit/loss
- realized_pnl: Realized profit/loss
```

### 3. IBKR Reconciliation

Automatic reconciliation with IBKR:

```python
# On startup
manager.initialize()  # Syncs with IBKR

# Periodic sync (every sync_interval_minutes)
if manager.should_sync():
    manager.sync_with_broker()

# Manual sync
manager.sync_with_broker()
```

Reconciliation logging:

```python
# Get reconciliation history
history = manager.get_reconciliation_history(days=7)

for log in history:
    print(f"{log.timestamp}: IBKR NAV=${log.ibkr_nav:,.2f}, "
          f"Local NAV=${log.local_nav:,.2f}, "
          f"Diff=${log.nav_difference:,.2f}")
```

### 4. Drawdown Tracking

Automatic peak NAV tracking and drawdown calculation:

```python
# Drawdown is calculated as:
# (peak_nav - current_nav) / peak_nav

# Peak NAV automatically updated when NAV increases
# Drawdown resets to 0 when new peak is reached
```

### 5. Equity Curve

Historical equity curve with multiple metrics:

```python
# Get 30-day equity curve
curve = manager.get_equity_curve(days=30)

# DataFrame with columns:
# - timestamp: Snapshot timestamp
# - nav: Net Asset Value
# - cash: Cash balance
# - equity_value: Equity value
# - drawdown: Drawdown percentage
# - daily_pnl: Daily P&L
# - num_positions: Number of positions

# Visualize
import matplotlib.pyplot as plt

curve['nav'].plot(title='Portfolio NAV')
plt.show()

curve['drawdown'].plot(title='Drawdown')
plt.show()
```

## Configuration Reference

### Constructor Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `broker` | LiveBrokerAdapter | Required | Broker adapter instance |
| `database_url` | str | `"sqlite:///portfolio_state.db"` | SQLAlchemy database URL |
| `sync_interval_minutes` | int | `5` | IBKR sync interval (minutes) |
| `snapshot_interval_minutes` | int | `15` | Snapshot interval (minutes) |

### Database URLs

#### SQLite (Development)
```python
database_url="sqlite:///portfolio_state.db"  # File-based
database_url="sqlite:///:memory:"  # In-memory
```

#### PostgreSQL (Production)
```python
database_url="postgresql://user:password@localhost:5432/copilot_quant"
database_url="postgresql://user:password@database:5432/copilot_quant"  # Docker
```

## Methods

### Initialization

#### `initialize() -> bool`
Initialize state manager and sync with IBKR.

**Returns:** `True` if successful, `False` otherwise

**Actions:**
1. Loads last known state from database
2. Syncs with IBKR broker
3. Takes initial snapshot
4. Sets initialized flag

### Synchronization

#### `sync_with_broker() -> bool`
Synchronize local state with IBKR broker.

**Returns:** `True` if successful, `False` otherwise

**Actions:**
1. Fetches current positions and NAV from IBKR
2. Compares with local state
3. Logs reconciliation results
4. Updates last sync time

#### `should_sync() -> bool`
Check if sync is due based on interval.

**Returns:** `True` if sync should be performed

### Snapshots

#### `take_snapshot() -> bool`
Take a snapshot of current portfolio state.

**Returns:** `True` if successful, `False` otherwise

**Actions:**
1. Fetches current state from broker
2. Calculates metrics (NAV, drawdown, PnL)
3. Stores portfolio snapshot
4. Stores position snapshots
5. Updates last snapshot time

#### `should_snapshot() -> bool`
Check if snapshot is due based on interval.

**Returns:** `True` if snapshot should be performed

### Queries

#### `get_current_state() -> Optional[PortfolioSnapshot]`
Get current portfolio state.

**Returns:** Most recent `PortfolioSnapshot` or `None`

#### `get_equity_curve(days: int = 30) -> pd.DataFrame`
Get historical equity curve.

**Parameters:**
- `days`: Number of days of history

**Returns:** DataFrame with equity curve data

#### `get_reconciliation_history(days: int = 7) -> List[ReconciliationLogModel]`
Get reconciliation history.

**Parameters:**
- `days`: Number of days of history

**Returns:** List of reconciliation log entries

## Database Schema

### portfolio_snapshots Table

| Column | Type | Description |
|--------|------|-------------|
| id | Integer | Primary key |
| timestamp | DateTime | Snapshot timestamp |
| snapshot_date | Date | Snapshot date (indexed) |
| nav | Float | Net Asset Value |
| cash | Float | Cash balance |
| equity_value | Float | Total equity value |
| num_positions | Integer | Number of positions |
| drawdown | Float | Drawdown percentage |
| daily_pnl | Float | Daily P&L |
| peak_nav | Float | Peak NAV to date |

### position_snapshots Table

| Column | Type | Description |
|--------|------|-------------|
| id | Integer | Primary key |
| portfolio_snapshot_id | Integer | Foreign key to portfolio_snapshots |
| symbol | String | Stock symbol (indexed) |
| quantity | Integer | Number of shares |
| avg_cost | Float | Average cost per share |
| current_price | Float | Current market price |
| market_value | Float | Total market value |
| unrealized_pnl | Float | Unrealized P&L |
| realized_pnl | Float | Realized P&L |

### reconciliation_logs Table

| Column | Type | Description |
|--------|------|-------------|
| id | Integer | Primary key |
| timestamp | DateTime | Reconciliation timestamp |
| reconciliation_date | Date | Date (indexed) |
| ibkr_nav | Float | IBKR account value |
| local_nav | Float | Local calculated NAV |
| nav_difference | Float | Difference (IBKR - Local) |
| positions_matched | Boolean | Whether positions matched |
| discrepancies_found | Integer | Number of discrepancies |
| notes | String | Additional notes |

## Usage Patterns

### 1. Continuous Monitoring

```python
import time

# Initialize
manager.initialize()

# Monitoring loop
while running:
    # Check if sync is due
    if manager.should_sync():
        manager.sync_with_broker()
    
    # Check if snapshot is due
    if manager.should_snapshot():
        manager.take_snapshot()
    
    # Sleep
    time.sleep(60)
```

### 2. Post-Restart Recovery

```python
# On system restart
manager = PortfolioStateManager(broker=broker)
manager.initialize()

# Loads last state from database
state = manager.get_current_state()

if state:
    print(f"Recovered state from {state.timestamp}")
    print(f"NAV: ${state.nav:,.2f}")
    print(f"Positions: {state.num_positions}")
else:
    print("No previous state found - starting fresh")
```

### 3. Daily Reconciliation

```python
# End-of-day reconciliation
def eod_reconciliation():
    # Force sync
    manager.sync_with_broker()
    
    # Get reconciliation history for today
    history = manager.get_reconciliation_history(days=1)
    
    # Check for discrepancies
    for log in history:
        diff_pct = abs(log.nav_difference / log.local_nav * 100)
        
        if diff_pct > 1.0:
            print(f"WARNING: NAV discrepancy {diff_pct:.2f}%")
            print(f"  IBKR: ${log.ibkr_nav:,.2f}")
            print(f"  Local: ${log.local_nav:,.2f}")
            
            # Take corrective action
            investigate_discrepancy(log)
```

### 4. Performance Analytics

```python
# Get equity curve
curve = manager.get_equity_curve(days=30)

# Calculate metrics
total_return = (curve['nav'].iloc[-1] / curve['nav'].iloc[0] - 1) * 100
max_drawdown = curve['drawdown'].max() * 100
sharpe_ratio = calculate_sharpe(curve['daily_pnl'])

print(f"30-Day Return: {total_return:.2f}%")
print(f"Max Drawdown: {max_drawdown:.2f}%")
print(f"Sharpe Ratio: {sharpe_ratio:.2f}")

# Visualize
import plotly.graph_objects as go
from plotly.subplots import make_subplots

fig = make_subplots(
    rows=2, cols=1,
    subplot_titles=('Portfolio NAV', 'Drawdown')
)

fig.add_trace(
    go.Scatter(x=curve.index, y=curve['nav'], name='NAV'),
    row=1, col=1
)

fig.add_trace(
    go.Scatter(x=curve.index, y=curve['drawdown']*100, name='Drawdown %'),
    row=2, col=1
)

fig.show()
```

## Best Practices

### 1. Database Selection

**Development:**
```python
# SQLite - simple, file-based
database_url="sqlite:///portfolio_state.db"
```

**Production:**
```python
# PostgreSQL - better concurrency, reliability
database_url="postgresql://user:pass@localhost/copilot_quant"
```

### 2. Sync/Snapshot Intervals

**Conservative (Low Frequency Trading):**
```python
sync_interval_minutes=15      # Sync every 15 minutes
snapshot_interval_minutes=60  # Snapshot every hour
```

**Aggressive (High Frequency Trading):**
```python
sync_interval_minutes=1       # Sync every minute
snapshot_interval_minutes=5   # Snapshot every 5 minutes
```

### 3. Monitoring Reconciliation

```python
# Regular reconciliation checks
def check_reconciliation():
    history = manager.get_reconciliation_history(days=1)
    
    for log in history:
        diff_pct = abs(log.nav_difference / log.local_nav * 100) if log.local_nav > 0 else 0
        
        if diff_pct > 0.5:  # Alert if >0.5% difference
            send_alert(f"NAV reconciliation discrepancy: {diff_pct:.2f}%")
```

### 4. Backup and Recovery

```python
# Regular database backups
import shutil
from datetime import datetime

def backup_database():
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_file = f"portfolio_backup_{timestamp}.db"
    shutil.copy("portfolio_state.db", f"backups/{backup_file}")
    print(f"Backup created: {backup_file}")

# Schedule backups
import schedule
schedule.every().day.at("00:00").do(backup_database)
```

## Error Handling

The manager handles errors gracefully:

```python
try:
    manager.initialize()
except Exception as e:
    logger.error(f"Failed to initialize: {e}")
    # Fallback to broker-only state

try:
    manager.take_snapshot()
except Exception as e:
    logger.error(f"Snapshot failed: {e}")
    # Continue without snapshot
```

## See Also

- [Live Signal Monitor Documentation](./LIVE_SIGNAL_MONITOR.md)
- [Docker Deployment Guide](./DOCKER_DEPLOYMENT.md)
- [Database Schema Reference](./DATABASE_SCHEMA.md)
