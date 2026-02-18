# Issue: Order Execution Module (Market/Limit Orders, Status Tracking)

**Epic**: Live Trading & Interactive Brokers (IBKR) Integration  
**Priority**: High  
**Status**: In Progress  
**Created**: 2026-02-18

## Overview
Implement comprehensive order execution system supporting multiple order types, real-time order status tracking, and order lifecycle management.

## Requirements

### 1. Order Types
- [x] Market orders (basic implementation exists)
- [x] Limit orders (basic implementation exists)
- [ ] Stop orders
- [ ] Stop-limit orders
- [ ] Trailing stop orders
- [ ] Bracket orders (entry + stop-loss + take-profit)
- [ ] Conditional orders
- [ ] Algorithmic orders (TWAP, VWAP)

### 2. Order Placement
- [x] Basic order submission
- [ ] Order validation (quantity, price, account checks)
- [ ] Pre-trade risk checks
- [ ] Order routing preferences
- [ ] Time-in-force options (DAY, GTC, IOC, FOK)
- [ ] Order modification (price, quantity)
- [ ] Order cancellation with confirmation

### 3. Order Status Tracking
- [ ] Real-time order status updates
- [ ] Fill notifications
- [ ] Partial fill handling
- [ ] Order rejection handling
- [ ] Order expiry tracking
- [ ] Order history and audit trail

### 4. Execution Analytics
- [ ] Fill price vs order price analysis
- [ ] Slippage tracking
- [ ] Execution time metrics
- [ ] Fill rate analysis
- [ ] Commission and fee tracking
- [ ] Execution quality reports

### 5. Order Management
- [ ] Active order monitoring
- [ ] Order book management
- [ ] Order replacement strategies
- [ ] Order aggregation (combine multiple orders)
- [ ] Smart order routing
- [ ] Order prioritization

## Implementation Tasks

### Order Manager
```python
class IBKROrderManager:
    """
    Manages order execution and lifecycle
    """
    - place_market_order(symbol: str, quantity: int, side: str) -> Order
    - place_limit_order(symbol: str, quantity: int, price: float, side: str) -> Order
    - place_stop_order(symbol: str, quantity: int, stop_price: float, side: str) -> Order
    - place_bracket_order(entry: OrderParams, stop_loss: float, take_profit: float) -> BracketOrder
    - modify_order(order_id: int, modifications: OrderModification) -> bool
    - cancel_order(order_id: int) -> bool
    - get_order_status(order_id: int) -> OrderStatus
    - get_open_orders() -> List[Order]
    - register_fill_callback(callback: Callable)
```

### Order Validator
```python
class OrderValidator:
    """
    Validates orders before submission
    """
    - validate_order(order: Order) -> ValidationResult
    - check_buying_power(order: Order) -> bool
    - check_position_limits(order: Order) -> bool
    - check_price_reasonability(order: Order) -> bool
    - check_market_hours(order: Order) -> bool
```

### Execution Tracker
```python
class ExecutionTracker:
    """
    Tracks order executions and fills
    """
    - track_execution(execution: Execution) -> None
    - get_fills(order_id: int) -> List[Fill]
    - calculate_avg_fill_price(order_id: int) -> float
    - calculate_slippage(order_id: int) -> float
    - get_execution_stats(start_date: datetime, end_date: datetime) -> ExecutionStats
```

### Data Models
```python
@dataclass
class Order:
    order_id: int
    symbol: str
    order_type: OrderType  # MARKET, LIMIT, STOP, etc.
    side: OrderSide  # BUY, SELL
    quantity: int
    limit_price: Optional[float]
    stop_price: Optional[float]
    time_in_force: TimeInForce
    status: OrderStatus
    filled_quantity: int
    remaining_quantity: int
    avg_fill_price: Optional[float]
    created_at: datetime
    updated_at: datetime

@dataclass
class Fill:
    execution_id: str
    order_id: int
    symbol: str
    side: OrderSide
    quantity: int
    price: float
    commission: float
    timestamp: datetime

@dataclass
class ExecutionStats:
    total_orders: int
    filled_orders: int
    cancelled_orders: int
    rejected_orders: int
    avg_fill_time: float
    avg_slippage: float
    total_commission: float

class OrderStatus(Enum):
    PENDING_SUBMIT = "PendingSubmit"
    PENDING_CANCEL = "PendingCancel"
    PRE_SUBMITTED = "PreSubmitted"
    SUBMITTED = "Submitted"
    FILLED = "Filled"
    CANCELLED = "Cancelled"
    INACTIVE = "Inactive"
    REJECTED = "Rejected"
```

### Database Schema
```sql
-- Orders table
CREATE TABLE orders (
    order_id BIGINT PRIMARY KEY,
    account_id VARCHAR(50),
    symbol VARCHAR(20),
    order_type VARCHAR(20),
    side VARCHAR(10),
    quantity INTEGER,
    limit_price DECIMAL(15,4),
    stop_price DECIMAL(15,4),
    time_in_force VARCHAR(10),
    status VARCHAR(20),
    filled_quantity INTEGER,
    avg_fill_price DECIMAL(15,4),
    commission DECIMAL(10,2),
    created_at TIMESTAMP,
    updated_at TIMESTAMP,
    cancelled_at TIMESTAMP,
    filled_at TIMESTAMP
);

-- Executions table
CREATE TABLE executions (
    execution_id VARCHAR(50) PRIMARY KEY,
    order_id BIGINT,
    symbol VARCHAR(20),
    side VARCHAR(10),
    quantity INTEGER,
    price DECIMAL(15,4),
    commission DECIMAL(10,2),
    timestamp TIMESTAMP,
    FOREIGN KEY (order_id) REFERENCES orders(order_id)
);
```

## Acceptance Criteria
- [ ] All major order types can be placed
- [ ] Orders validated before submission
- [ ] Real-time order status updates working
- [ ] Fill notifications delivered immediately
- [ ] Order history stored in database
- [ ] Slippage and execution metrics calculated
- [ ] Order modification and cancellation working
- [ ] Comprehensive error handling
- [ ] Unit tests for all order types
- [ ] Integration tests with mock broker

## Testing Requirements
- [ ] Unit tests for order manager
- [ ] Unit tests for order validator
- [ ] Unit tests for execution tracker
- [ ] Integration tests with mock IB API
- [ ] Order lifecycle tests (submit -> fill -> complete)
- [ ] Order modification tests
- [ ] Order cancellation tests
- [ ] Edge case tests (rejections, partial fills, etc.)

## Safety Considerations
- **Pre-trade validation**: Prevent invalid orders from reaching broker
- **Position limits**: Enforce maximum position sizes
- **Daily limits**: Limit total daily trading volume
- **Price checks**: Prevent fat-finger errors (e.g., price 100x market)
- **Duplicate prevention**: Avoid accidental duplicate orders
- **Cancel-all functionality**: Emergency order cancellation

## Related Files
- `copilot_quant/brokers/interactive_brokers.py` - Current implementation
- `copilot_quant/brokers/order_manager.py` - New module (to create)
- `copilot_quant/brokers/order_validator.py` - New module (to create)
- `copilot_quant/brokers/execution_tracker.py` - New module (to create)
- `tests/test_brokers/test_order_execution.py` - Tests (to create)

## Dependencies
- ib_insync>=0.9.86
- Issue #02 (Connection Management) - Required
- Issue #04 (Account Sync) - Required for balance checks

## Notes
- Current basic implementation in `IBKRBroker.execute_market_order()` and `execute_limit_order()`
- Need to expand to support all order types
- Real-time callbacks critical for order status tracking
- Database storage essential for audit trail
- Consider implementing order queue for rate limiting

## IB Order Status Flow
```
PendingSubmit -> PreSubmitted -> Submitted -> (PartiallyFilled) -> Filled
                                            \-> Cancelled
                                            \-> Rejected
```

## References
- [IB Order Types](https://interactivebrokers.github.io/tws-api/orders.html)
- [ib_insync order examples](https://ib-insync.readthedocs.io/api.html#module-ib_insync.order)
