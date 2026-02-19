# Live Signal Monitor API Documentation

## Overview
The `LiveSignalMonitor` provides real-time signal generation and execution for signal-based trading strategies. It continuously monitors multiple strategies, generates trading signals, performs risk checks, and executes orders through the live broker.

## Basic Usage

### Initialization

```python
from copilot_quant.live import LiveSignalMonitor
from copilot_quant.strategies.my_strategy import MySignalStrategy

# Initialize monitor
monitor = LiveSignalMonitor(
    database_url="sqlite:///live_trading.db",
    paper_trading=True,
    update_interval=60.0,  # Check for signals every 60 seconds
    max_position_size=0.1,  # Max 10% of NAV per position
    max_total_exposure=0.8,  # Max 80% total exposure
    enable_risk_checks=True
)

# Add strategies
monitor.add_strategy(MySignalStrategy())

# Connect to IBKR
if monitor.connect():
    print("Connected to IBKR successfully")
    
    # Start monitoring
    monitor.start(['AAPL', 'MSFT', 'GOOGL'])
    
    # Monitor runs in background thread
    # Check status with dashboard
    monitor.print_dashboard()
    
    # When done, stop and disconnect
    monitor.stop()
    monitor.disconnect()
```

### Context Manager Pattern

```python
with LiveSignalMonitor(database_url="sqlite:///trading.db") as monitor:
    monitor.add_strategy(MySignalStrategy())
    monitor.start(['AAPL', 'MSFT'])
    
    # Monitor runs...
    time.sleep(3600)  # Run for 1 hour
    
    # Automatically stops and disconnects on exit
```

## Key Features

### 1. Signal Generation
Continuously calls `generate_signals()` on all registered strategies:

```python
class MySignalStrategy(SignalBasedStrategy):
    def generate_signals(self, timestamp, data):
        signals = []
        
        # Analyze data and generate signals
        if buy_condition_met:
            signals.append(TradingSignal(
                symbol='AAPL',
                side='buy',
                confidence=0.8,
                sharpe_estimate=1.5,
                entry_price=150.0,
                strategy_name=self.name
            ))
        
        return signals
```

### 2. Risk Checks
Automatic risk checking before execution:

- **Quality Score**: Filters signals below quality threshold (0.3)
- **Position Sizing**: Limits individual position size (default 10% of NAV)
- **Total Exposure**: Limits total portfolio exposure (default 80% of NAV)

Configure risk parameters:

```python
monitor = LiveSignalMonitor(
    max_position_size=0.15,  # 15% max per position
    max_total_exposure=0.9,  # 90% max total exposure
    enable_risk_checks=True  # Enable/disable risk checks
)
```

### 3. Position Sizing
Automatic position sizing based on signal quality:

```python
# Position size = Account Value × Max Position Size × Signal Quality Score

# Example:
# Account Value: $100,000
# Max Position Size: 10% = $10,000
# Signal Quality: 0.75
# → Allocation: $7,500
# → Shares at $150: 50 shares
```

### 4. Signal Persistence
All signals are persisted to database for audit trail, even if not executed:

```python
# Signals stored with:
# - Timestamp
# - Symbol, side, confidence
# - Quality score, Sharpe estimate
# - Strategy name
# - Execution status
```

### 5. Dashboard Monitoring

```python
# Get dashboard summary
summary = monitor.get_dashboard_summary()
print(f"Active signals: {summary['active_signals']}")
print(f"Total signals: {summary['stats']['total_signals_generated']}")
print(f"Executed: {summary['stats']['signals_executed']}")

# Print dashboard to console
monitor.print_dashboard()
```

Output:
```
============================================================
LIVE SIGNAL MONITOR DASHBOARD
============================================================
Status: RUNNING
Connected: YES
Strategies: 2
Symbols: 3
Account Value: $100,000.00
Positions: 5

Statistics:
  Total Signals: 127
  Executed: 45
  Rejected: 82
  Errors: 0

Active Signals: 3

Recent Signals:
  14:32:15 | AAPL   | buy  | Quality: 0.85 | Strategy: MomentumSignals
  14:31:42 | MSFT   | sell | Quality: 0.72 | Strategy: MeanReversion
  14:30:18 | GOOGL  | buy  | Quality: 0.68 | Strategy: MomentumSignals
============================================================
```

## Configuration Reference

### Constructor Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `database_url` | str | `"sqlite:///live_trading.db"` | SQLAlchemy database URL |
| `paper_trading` | bool | `True` | Use paper trading account |
| `host` | str | `None` | IB API host (auto-detected if None) |
| `port` | int | `None` | IB API port (auto-detected if None) |
| `client_id` | int | `None` | Unique client ID |
| `use_gateway` | bool | `False` | Use IB Gateway vs TWS |
| `update_interval` | float | `60.0` | Signal check interval (seconds) |
| `max_position_size` | float | `0.1` | Max position size (fraction of NAV) |
| `max_total_exposure` | float | `0.8` | Max total exposure (fraction of NAV) |
| `enable_risk_checks` | bool | `True` | Enable/disable risk checks |

## Methods

### Core Methods

#### `add_strategy(strategy: SignalBasedStrategy)`
Register a signal-based strategy for monitoring.

**Parameters:**
- `strategy`: Instance of `SignalBasedStrategy`

**Raises:**
- `ValueError`: If strategy is not a `SignalBasedStrategy`

#### `connect(timeout: int = 30, retry_count: int = 3) -> bool`
Establish connections to IBKR for data and execution.

**Returns:** `True` if connected, `False` otherwise

#### `start(symbols: List[str], lookback_days: int = 30, data_interval: str = '1d') -> bool`
Start live signal monitoring.

**Parameters:**
- `symbols`: List of symbols to monitor
- `lookback_days`: Days of historical data to load
- `data_interval`: Data interval ('1d', '1h', etc.)

**Returns:** `True` if started, `False` otherwise

#### `stop()`
Stop signal monitoring gracefully.

#### `disconnect()`
Disconnect from IBKR and clean up resources.

### Monitoring Methods

#### `get_dashboard_summary() -> Dict`
Get current dashboard summary.

**Returns:** Dictionary with:
- `is_running`: Monitor running status
- `is_connected`: Connection status
- `num_strategies`: Number of registered strategies
- `num_symbols`: Number of monitored symbols
- `active_signals`: Number of active signals
- `recent_signals`: List of recent signals
- `stats`: Statistics dictionary
- `account_value`: Current account value
- `positions`: Number of open positions

#### `print_dashboard()`
Print formatted dashboard to console.

#### `is_connected() -> bool`
Check if monitor is connected to IBKR.

## Signal Lifecycle

1. **Generation**: Strategies generate signals every `update_interval`
2. **Persistence**: All signals persisted to database
3. **Risk Check**: Signals evaluated against risk limits
4. **Position Sizing**: Calculate position size based on quality
5. **Execution**: Create and execute order through broker
6. **Tracking**: Update active signals and statistics

## Best Practices

### 1. Strategy Design
```python
class WellDesignedSignals(SignalBasedStrategy):
    def generate_signals(self, timestamp, data):
        # Return empty list when no signals
        if not self._conditions_met(data):
            return []
        
        # Set realistic confidence and Sharpe estimates
        return [TradingSignal(
            symbol='AAPL',
            side='buy',
            confidence=0.75,  # 0.0 to 1.0
            sharpe_estimate=1.5,  # Realistic estimate
            entry_price=current_price,
            stop_loss=stop_price,  # Optional
            take_profit=target_price,  # Optional
            strategy_name=self.name
        )]
```

### 2. Update Interval
- **Short interval (60s)**: More responsive, higher load
- **Medium interval (300s)**: Balanced for most strategies
- **Long interval (900s)**: Lower frequency strategies

### 3. Risk Management
```python
# Conservative setup
monitor = LiveSignalMonitor(
    max_position_size=0.05,  # 5% max per position
    max_total_exposure=0.6,  # 60% max exposure
    enable_risk_checks=True
)

# Aggressive setup (use with caution)
monitor = LiveSignalMonitor(
    max_position_size=0.15,  # 15% max per position
    max_total_exposure=0.9,  # 90% max exposure
    enable_risk_checks=True
)
```

### 4. Monitoring and Logging
```python
import logging

# Enable detailed logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('copilot_quant.live.live_signal_monitor')
logger.setLevel(logging.DEBUG)

# Periodic dashboard checks
import time
while monitor._running:
    monitor.print_dashboard()
    time.sleep(300)  # Every 5 minutes
```

## Error Handling

The monitor handles errors gracefully:

- **Connection Loss**: Logs warning, attempts reconnection
- **Strategy Errors**: Logged, other strategies continue
- **Execution Errors**: Logged, tracking updated
- **Data Errors**: Logged, skips current cycle

Check error count:
```python
summary = monitor.get_dashboard_summary()
if summary['stats']['errors'] > 10:
    print("High error count - investigate!")
```

## Thread Safety

The monitor runs in a background thread. Access is thread-safe for:
- `get_dashboard_summary()`
- `print_dashboard()`
- `stop()`
- `disconnect()`

## Performance Considerations

- **Update Interval**: Balance responsiveness vs system load
- **Number of Strategies**: Each strategy checked every interval
- **Number of Symbols**: Data fetched for all symbols
- **Database**: Use PostgreSQL for production (better concurrency)

## See Also

- [Portfolio State Manager Documentation](./PORTFOLIO_STATE_MANAGER.md)
- [Signal-Based Strategy Guide](./SIGNAL_STRATEGIES.md)
- [Docker Deployment Guide](./DOCKER_DEPLOYMENT.md)
