# Signal Persistence Layer

This module provides a complete signal persistence layer for tracking trading signals from generation through execution.

## Overview

The signal persistence layer creates an audit trail for all trading signals, enabling:
- **Compliance**: Complete record of all trading decisions
- **Debugging**: Track signal lifecycle to identify issues
- **Strategy Attribution**: Analyze which strategies generate profitable signals
- **Performance Analysis**: Measure execution quality and slippage

## Components

### SignalRecord Model

SQLAlchemy model representing a persisted trading signal with:
- Signal identification (ID, strategy, symbol)
- Signal details (type, direction, strength, quality score)
- Timing information (generated, processed, executed)
- Execution details (status, prices, quantities)
- Risk check results
- Metadata

### SignalStatus Enum

Lifecycle states:
- `GENERATED`: Signal created by strategy
- `PASSED_RISK`: Passed risk checks
- `REJECTED`: Failed risk checks
- `SUBMITTED`: Order submitted to broker
- `EXECUTED`: Order filled
- `PARTIALLY_FILLED`: Partial execution
- `CANCELLED`: Order cancelled
- `EXPIRED`: Signal expired before execution
- `MISSED`: Signal missed (market closed, etc.)
- `ERROR`: Error during processing

### SignalRepository

Data access layer providing:

#### CRUD Operations
- `save_signal(signal, status, **kwargs)`: Persist new signal
- `update_signal_status(signal_id, status, **kwargs)`: Update signal status
- `get_signal_by_id(signal_id)`: Retrieve specific signal
- `get_signals(filters, limit)`: Query signals with filters

#### Analytics Methods
- `get_signals_by_strategy(strategy_name, start_date, end_date)`: Strategy-specific signals
- `get_execution_stats(start_date, end_date)`: Aggregated execution statistics
- `get_rejection_summary(start_date, end_date)`: Rejection reason analysis

## Usage Examples

### Basic Usage

```python
from copilot_quant.backtest.signals import TradingSignal
from copilot_quant.data import SignalRepository, SignalStatus

# Initialize repository (auto-creates tables)
repo = SignalRepository(db_url="sqlite:///data/signals.db")

# Create a trading signal
signal = TradingSignal(
    symbol="AAPL",
    side="buy",
    confidence=0.8,
    sharpe_estimate=1.5,
    entry_price=150.0,
    stop_loss=145.0,
    take_profit=155.0,
    strategy_name="MomentumStrategy",
)

# Persist signal
record = repo.save_signal(
    signal,
    status=SignalStatus.GENERATED.value,
    signal_type="entry",
    requested_quantity=100,
)
```

### Signal Lifecycle Tracking

```python
# Pass risk check
repo.update_signal_status(
    record.signal_id,
    SignalStatus.PASSED_RISK.value,
    risk_check_passed=True,
    risk_check_details={"max_position_size": True, "portfolio_risk": True},
)

# Submit to broker
repo.update_signal_status(
    record.signal_id,
    SignalStatus.SUBMITTED.value,
    order_id="ORDER-12345",
    processed_at=datetime.utcnow(),
)

# Mark as executed
repo.update_signal_status(
    record.signal_id,
    SignalStatus.EXECUTED.value,
    executed_price=151.0,
    executed_quantity=100,
    executed_at=datetime.utcnow(),
)
# Slippage is automatically calculated: $1.00
```

### Querying Signals

```python
# Get all executed signals
executed = repo.get_signals(filters={"status": "executed"})

# Get signals for specific strategy
strategy_signals = repo.get_signals_by_strategy(
    "MomentumStrategy",
    start_date=datetime(2024, 1, 1),
    end_date=datetime(2024, 12, 31),
)

# Filter by multiple criteria
aapl_signals = repo.get_signals(
    filters={
        "symbol": "AAPL",
        "strategy": "MomentumStrategy",
        "status": "executed",
        "start_date": datetime(2024, 1, 1),
        "end_date": datetime(2024, 12, 31),
    },
    limit=100,
)
```

### Analytics

```python
# Get execution statistics
stats = repo.get_execution_stats(
    start_date=datetime(2024, 1, 1),
    end_date=datetime(2024, 12, 31),
)
print(f"Total signals: {stats['total_signals']}")
print(f"Executed: {stats['executed_count']}")
print(f"Rejected: {stats['rejected_count']}")
print(f"Average slippage: ${stats['avg_slippage']:.2f}")
print(f"Average quality score: {stats['avg_quality_score']:.3f}")

# Get rejection reasons
rejections = repo.get_rejection_summary(
    start_date=datetime(2024, 1, 1),
    end_date=datetime(2024, 12, 31),
)
for reason, count in rejections.items():
    print(f"{reason}: {count}")
```

## Integration Points

### With SignalExecutionPipeline (PR #106)

```python
# In SignalExecutionPipeline
class SignalExecutionPipeline:
    def __init__(self):
        self.repo = SignalRepository()
    
    def process_signal(self, signal: TradingSignal):
        # 1. Save signal when generated
        record = self.repo.save_signal(signal, status="generated")
        
        # 2. Update after risk check
        if self.risk_check.passes(signal):
            self.repo.update_signal_status(
                record.signal_id,
                "passed_risk",
                risk_check_details=self.risk_check.get_details(),
            )
        else:
            self.repo.update_signal_status(
                record.signal_id,
                "rejected",
                rejection_reason=self.risk_check.get_rejection_reason(),
            )
            return
        
        # 3. Update after order submission
        order_id = self.broker.submit_order(signal)
        self.repo.update_signal_status(
            record.signal_id,
            "submitted",
            order_id=order_id,
        )
        
        # 4. Update after execution
        fill = self.broker.wait_for_fill(order_id)
        self.repo.update_signal_status(
            record.signal_id,
            "executed",
            executed_price=fill.price,
            executed_quantity=fill.quantity,
            executed_at=fill.timestamp,
        )
```

### With LiveSignalMonitor

```python
# In LiveSignalMonitor
class LiveSignalMonitor:
    def __init__(self):
        self.repo = SignalRepository()
    
    def on_signal_generated(self, signal: TradingSignal):
        # Persist immediately, even if pipeline is paused
        self.repo.save_signal(
            signal,
            status="generated",
            generated_at=datetime.utcnow(),
        )
```

## Database Configuration

### SQLite (Development)

```python
# Default configuration
repo = SignalRepository()  # Uses sqlite:///data/signals.db

# Custom path
repo = SignalRepository(db_url="sqlite:///path/to/signals.db")

# In-memory (for testing)
repo = SignalRepository(db_url="sqlite:///:memory:")
```

### PostgreSQL (Production)

```python
repo = SignalRepository(
    db_url="postgresql://user:password@localhost/trading_db"
)
```

## Data Retention

- All signals are persisted indefinitely
- No automatic deletion
- Manual cleanup can be done via SQL if needed
- Consider archiving old signals for long-running systems

## Testing

The module includes comprehensive tests covering:
- Model creation and serialization
- CRUD operations
- Signal lifecycle transitions
- Query filtering and pagination
- Execution statistics
- Rejection summaries
- TradingSignal to SignalRecord conversion

Run tests:
```bash
pytest tests/test_data/test_signal_persistence.py -v
```

## Future Enhancements

Potential additions (not yet implemented):
- Database migrations with Alembic
- Signal archiving and retention policies
- Real-time signal event streaming
- Signal versioning for strategy changes
- Performance optimization for large-scale queries
