# Issue: Integration with Strategy Engine and Data Adapters

**Epic**: Live Trading & Interactive Brokers (IBKR) Integration  
**Priority**: High  
**Status**: Not Started  
**Created**: 2026-02-18

## Overview
Integrate the IBKR broker with the existing strategy engine and data adapters to enable live strategy execution, signal processing, and automated trading.

## Requirements

### 1. Strategy Engine Integration
- [ ] Connect strategies to live broker
- [ ] Route signals to order execution
- [ ] Handle strategy state management
- [ ] Support multiple concurrent strategies
- [ ] Strategy lifecycle management (start, stop, pause)
- [ ] Strategy performance tracking in live mode

### 2. Signal Processing
- [ ] Convert strategy signals to broker orders
- [ ] Signal validation and filtering
- [ ] Signal priority and conflict resolution
- [ ] Signal-to-order mapping
- [ ] Partial signal execution handling
- [ ] Signal performance analytics

### 3. Data Adapter Integration
- [ ] Connect live data feeds to strategies
- [ ] Merge real-time and historical data
- [ ] Handle data source switching (paper data vs live)
- [ ] Data quality validation
- [ ] Missing data handling
- [ ] Data buffering and caching

### 4. Position Management
- [ ] Sync broker positions with strategy state
- [ ] Handle position discrepancies
- [ ] Position rebalancing logic
- [ ] Exit position management
- [ ] Position sizing calculations
- [ ] Portfolio-level position management

### 5. Risk Integration
- [ ] Apply risk rules to live orders
- [ ] Real-time risk limit monitoring
- [ ] Circuit breaker integration
- [ ] Position limit enforcement
- [ ] Loss limit monitoring
- [ ] Emergency shutdown triggers

## Implementation Tasks

### Live Strategy Adapter
```python
class LiveStrategyAdapter:
    """
    Adapts strategies to work with live broker
    """
    - register_strategy(strategy: Strategy) -> None
    - start_strategy(strategy_id: str) -> bool
    - stop_strategy(strategy_id: str) -> bool
    - process_signal(signal: Signal) -> Order
    - sync_strategy_state(strategy_id: str) -> None
    - get_strategy_status(strategy_id: str) -> StrategyStatus
```

### Signal Router
```python
class SignalRouter:
    """
    Routes strategy signals to appropriate handlers
    """
    - route_signal(signal: Signal) -> None
    - validate_signal(signal: Signal) -> ValidationResult
    - resolve_conflicts(signals: List[Signal]) -> List[Signal]
    - prioritize_signals(signals: List[Signal]) -> List[Signal]
    - register_signal_handler(handler: Callable) -> None
```

### Live Data Adapter
```python
class LiveDataAdapter:
    """
    Adapts live broker data to strategy format
    """
    - get_live_data(symbol: str) -> pd.DataFrame
    - merge_data_sources(live: pd.DataFrame, historical: pd.DataFrame) -> pd.DataFrame
    - validate_data_quality(data: pd.DataFrame) -> bool
    - handle_missing_data(data: pd.DataFrame) -> pd.DataFrame
    - register_data_callback(symbol: str, callback: Callable) -> None
```

### Position Reconciler
```python
class PositionReconciler:
    """
    Reconciles broker positions with strategy state
    """
    - reconcile_positions() -> ReconciliationReport
    - detect_discrepancies() -> List[Discrepancy]
    - sync_positions(strategy_id: str) -> bool
    - handle_external_trades(trades: List[Trade]) -> None
    - generate_reconciliation_report() -> Report
```

### Data Models
```python
@dataclass
class Signal:
    strategy_id: str
    symbol: str
    action: SignalAction  # BUY, SELL, HOLD
    quantity: Optional[int]
    price: Optional[float]
    signal_strength: float
    timestamp: datetime
    metadata: Dict[str, Any]

@dataclass
class StrategyStatus:
    strategy_id: str
    state: StrategyState  # RUNNING, STOPPED, PAUSED, ERROR
    positions: List[Position]
    orders: List[Order]
    pnl: float
    last_signal: Optional[Signal]
    errors: List[str]

class SignalAction(Enum):
    BUY = "buy"
    SELL = "sell"
    HOLD = "hold"
    CLOSE = "close"
    REBALANCE = "rebalance"

class StrategyState(Enum):
    INITIALIZED = "initialized"
    RUNNING = "running"
    PAUSED = "paused"
    STOPPED = "stopped"
    ERROR = "error"
```

### Integration Flow
```
Strategy → Signal Generation → Signal Router → Risk Checks
                                                     ↓
                                              Order Validator
                                                     ↓
                                              Broker Execution
                                                     ↓
                                              Fill Notification
                                                     ↓
                                         Position Reconciliation
                                                     ↓
                                         Strategy State Update
```

## Acceptance Criteria
- [ ] Strategies can execute on live broker
- [ ] Signals correctly converted to orders
- [ ] Multiple strategies can run concurrently
- [ ] Position reconciliation working
- [ ] Risk checks applied to all orders
- [ ] Data feeds integrated with strategies
- [ ] Strategy state persists across restarts
- [ ] All integrations are logged
- [ ] Unit tests for all adapters
- [ ] Integration tests with mock strategies

## Testing Requirements
- [ ] Unit tests for strategy adapter
- [ ] Unit tests for signal router
- [ ] Unit tests for data adapter
- [ ] Unit tests for position reconciler
- [ ] Integration tests with mock broker
- [ ] Integration tests with sample strategies
- [ ] End-to-end tests (signal → execution → fill)
- [ ] Tests for concurrent strategies
- [ ] Tests for error handling

## Strategy Migration Checklist
For each strategy to work with live broker:
- [ ] Strategy implements required interface
- [ ] Signal generation is event-driven (not batch)
- [ ] State management is compatible
- [ ] Risk parameters are configured
- [ ] Performance metrics are tracked
- [ ] Error handling is robust
- [ ] Logging is comprehensive

## Related Files
- `copilot_quant/strategies/` - Existing strategies
- `copilot_quant/backtest/strategy.py` - Strategy base class
- `copilot_quant/brokers/live_strategy_adapter.py` - New module (to create)
- `copilot_quant/brokers/signal_router.py` - New module (to create)
- `copilot_quant/brokers/live_data_adapter.py` - New module (to create)
- `copilot_quant/brokers/position_reconciler.py` - New module (to create)
- `tests/test_brokers/test_strategy_integration.py` - Tests (to create)

## Dependencies
- pandas
- Issue #02 (Connection Management) - Required
- Issue #03 (Market Data) - Required
- Issue #04 (Account Sync) - Required
- Issue #05 (Order Execution) - Required

## Considerations
### Signal-to-Order Conversion
- Consider position sizing algorithms
- Handle fractional shares (if supported)
- Account for existing positions
- Consider transaction costs
- Handle signal conflicts

### Concurrent Strategy Management
- Ensure strategies don't interfere with each other
- Manage shared resources (data, connections)
- Handle strategy priority
- Prevent over-leveraging
- Portfolio-level risk management

### State Management
- Strategy state should persist across restarts
- Handle connection interruptions
- Recover from errors gracefully
- Maintain audit trail

### Performance
- Minimize latency (signal → execution)
- Efficient data streaming
- Optimize position calculations
- Cache frequently accessed data

## References
- Existing backtest strategy implementation
- Current strategy engine code
- Data pipeline documentation
