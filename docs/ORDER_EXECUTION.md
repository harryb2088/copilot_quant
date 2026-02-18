# Order Execution Module Documentation

## Overview

The Order Execution Module provides comprehensive order management for Interactive Brokers (IBKR) integration. It handles market and limit orders, tracks order status, processes fills (complete and partial), handles errors with retry logic, and provides structured logging for all order events.

## Components

### 1. OrderExecutionHandler (`order_execution_handler.py`)

The core order execution component that manages order lifecycle, tracking, and callbacks.

#### Key Features

- **Order Status Tracking**: Tracks orders through their lifecycle (Pending, Submitted, PartiallyFilled, Filled, Cancelled, Error)
- **Order Deduplication**: Prevents duplicate order submissions within a time window
- **Fill Processing**: Handles complete and partial fills with price aggregation
- **Error Handling**: Manages errors with configurable exponential backoff retry
- **Event Callbacks**: Provides callbacks for fills, status changes, and errors

#### Usage Example

```python
from copilot_quant.brokers.interactive_brokers import IBKRBroker

# Initialize broker with order execution enabled
broker = IBKRBroker(
    paper_trading=True,
    enable_order_execution=True,
    enable_order_logging=True
)

# Connect to IBKR
broker.connect()

# Register callbacks for order events
def on_fill(order_record):
    print(f"Order {order_record.order_id} filled: {order_record.filled_quantity} shares")

broker.register_order_fill_callback(on_fill)

# Submit a market order
order_record = broker.execute_market_order(
    symbol="AAPL",
    quantity=100,
    side="buy"
)

print(f"Order submitted: {order_record.order_id}")
print(f"Status: {order_record.status.value}")

# Query order status
order_status = broker.get_order_status(order_record.order_id)
print(f"Filled: {order_status.filled_quantity}/{order_status.total_quantity}")
```

#### Order Status Lifecycle

```
PENDING → SUBMITTED → PARTIALLY_FILLED → FILLED
                  ↓
               CANCELLED
                  ↓
                ERROR (with retry)
```

### 2. OrderLogger (`order_logger.py`)

Structured logging component for all order-related events.

#### Features

- JSON-structured logs for easy parsing and analysis
- Separate log files per day
- Console and file logging support
- Event history retrieval
- Daily summary statistics

#### Log Event Types

- **SUBMISSION**: Order placed with broker
- **FILL**: Order filled (complete or partial)
- **STATUS_CHANGE**: Order status updated
- **CANCELLATION**: Order cancelled
- **ERROR**: Order encountered an error
- **RETRY**: Order retry scheduled

#### Usage Example

```python
from copilot_quant.brokers.order_logger import OrderLogger

# Initialize logger
logger = OrderLogger(
    log_to_file=True,
    log_dir="./logs/orders",
    log_to_console=True
)

# Logging happens automatically when integrated with IBKRBroker
# But you can also log manually:

logger.log_submission(order_record)
logger.log_fill(order_record, fill)
logger.log_error(order_record, "Connection lost")

# Retrieve order history
history = logger.get_order_history(order_id=1)
for log_entry in history:
    print(log_entry)

# Get daily summary
summary = logger.get_todays_summary()
print(f"Total orders: {summary['total_orders']}")
print(f"Filled orders: {summary['filled_orders']}")
print(f"Partial fills: {summary['partial_fills']}")
```

#### Log Format

```json
{
  "timestamp": "2026-02-18T10:30:45.123456",
  "event_type": "SUBMISSION",
  "order_id": 1,
  "symbol": "AAPL",
  "action": "BUY",
  "quantity": 100,
  "order_type": "MARKET",
  "status": "Submitted",
  "submission_time": "2026-02-18T10:30:45.123456"
}
```

### 3. IBKRBroker Integration (`interactive_brokers.py`)

The main broker class integrates the order execution handler and logger seamlessly.

#### New Methods

```python
# Order submission
execute_market_order(symbol, quantity, side) -> OrderRecord
execute_limit_order(symbol, quantity, limit_price, side) -> OrderRecord

# Order queries
get_order_status(order_id) -> OrderRecord
get_all_orders() -> List[OrderRecord]
get_active_orders() -> List[OrderRecord]
get_order_history(order_id) -> List[str]
get_todays_order_summary() -> Dict

# Callback registration
register_order_fill_callback(callback)
register_order_status_callback(callback)
register_order_error_callback(callback)
```

## Fill Notification Patterns

### Complete Fill

When an order is completely filled:

1. `execDetailsEvent` triggered by ib_insync
2. `OrderExecutionHandler.handle_fill()` processes the fill
3. Fill added to order record, status updated to FILLED
4. Fill callbacks triggered
5. Order logged to file

### Partial Fill

When an order is partially filled:

1. Multiple `execDetailsEvent` triggers for each partial fill
2. Each fill processed and aggregated
3. Average fill price calculated: `total_value / filled_quantity`
4. Status updated to PARTIALLY_FILLED
5. Callbacks triggered after each partial fill

### Example: Handling Partial Fills

```python
def on_fill(order_record):
    if order_record.status == OrderStatus.PARTIALLY_FILLED:
        print(f"Partial fill: {order_record.filled_quantity}/{order_record.total_quantity}")
        print(f"Remaining: {order_record.remaining_quantity}")
        print(f"Avg price: ${order_record.avg_fill_price:.2f}")
    elif order_record.status == OrderStatus.FILLED:
        print(f"Order complete!")
        print(f"Final avg price: ${order_record.avg_fill_price:.2f}")
        print(f"Total fills: {len(order_record.fills)}")

broker.register_order_fill_callback(on_fill)
```

## Error Handling and Recovery

### Error Handling Flow

1. Error event received from IBKR
2. `OrderExecutionHandler.handle_error()` processes error
3. Order status set to ERROR
4. Error callbacks triggered
5. Retry scheduled if retry count < max_retries

### Exponential Backoff

Retry delays follow exponential backoff:
- Retry 1: `initial_delay * (backoff_factor ^ 0)` = 1.0 seconds
- Retry 2: `initial_delay * (backoff_factor ^ 1)` = 2.0 seconds
- Retry 3: `initial_delay * (backoff_factor ^ 2)` = 4.0 seconds

### Configuration

```python
handler = OrderExecutionHandler(
    max_retries=3,              # Maximum retry attempts
    initial_retry_delay=1.0,    # Initial delay in seconds
    retry_backoff_factor=2.0    # Exponential multiplier
)
```

### Error Callback Example

```python
def on_error(order_record, error_message):
    print(f"Order {order_record.order_id} error: {error_message}")
    print(f"Retry count: {order_record.retry_count}/{handler.max_retries}")
    
    if order_record.retry_count >= handler.max_retries:
        print("Max retries reached, order failed permanently")
        # Implement custom recovery logic here
        # e.g., notify user, log to database, etc.

broker.register_order_error_callback(on_error)
```

## Retry Mechanism

### When Retries Occur

- Network errors
- Temporary IBKR API errors
- Rejected orders (configurable)

### Retry Prevention

Orders are NOT retried for:
- User cancellations
- Insufficient funds errors
- Invalid contract errors

### Manual Retry

```python
# Get failed order
order = broker.get_order_status(order_id)

if order.status == OrderStatus.ERROR:
    # Resubmit manually
    new_order = broker.execute_market_order(
        symbol=order.symbol,
        quantity=order.remaining_quantity,
        side=order.action.lower()
    )
```

## Duplicate Prevention

### How It Works

1. Each order generates a unique key: `symbol_action_quantity_timestamp`
2. Key checked against recently submitted orders
3. Duplicate rejected if key exists in tracking set
4. Keys automatically cleaned up after 60 seconds

### Example

```python
# First submission succeeds
order1 = broker.execute_market_order("AAPL", 100, "buy")  # ✓ Success

# Immediate duplicate rejected
order2 = broker.execute_market_order("AAPL", 100, "buy")  # ✗ Rejected

# After 1 minute, same order allowed
time.sleep(61)
order3 = broker.execute_market_order("AAPL", 100, "buy")  # ✓ Success
```

## Common Use Cases

### 1. Simple Market Order with Status Tracking

```python
broker = IBKRBroker(paper_trading=True)
broker.connect()

# Submit order
order = broker.execute_market_order("AAPL", 100, "buy")

# Poll for status
import time
while order.status not in [OrderStatus.FILLED, OrderStatus.CANCELLED, OrderStatus.ERROR]:
    time.sleep(1)
    order = broker.get_order_status(order.order_id)
    print(f"Status: {order.status.value}, Filled: {order.filled_quantity}")

print(f"Final status: {order.status.value}")
print(f"Avg fill price: ${order.avg_fill_price:.2f}")
```

### 2. Limit Order with Callback

```python
def on_fill(order_record):
    print(f"FILLED: {order_record.filled_quantity} @ ${order_record.avg_fill_price:.2f}")

broker.register_order_fill_callback(on_fill)

order = broker.execute_limit_order(
    symbol="GOOGL",
    quantity=50,
    limit_price=140.00,
    side="sell"
)

# Callbacks will be triggered automatically when filled
```

### 3. Batch Orders with Error Handling

```python
def submit_with_retry(broker, symbol, quantity, side, max_attempts=3):
    for attempt in range(max_attempts):
        order = broker.execute_market_order(symbol, quantity, side)
        if order:
            return order
        time.sleep(2 ** attempt)  # Exponential backoff
    return None

symbols = ["AAPL", "GOOGL", "MSFT"]
orders = []

for symbol in symbols:
    order = submit_with_retry(broker, symbol, 100, "buy")
    if order:
        orders.append(order)
        print(f"✓ {symbol}: Order {order.order_id} submitted")
    else:
        print(f"✗ {symbol}: Failed after retries")

# Monitor all orders
active_orders = broker.get_active_orders()
print(f"Active orders: {len(active_orders)}")
```

### 4. Order History Analysis

```python
# Get today's summary
summary = broker.get_todays_order_summary()

print(f"Orders Today: {summary['total_orders']}")
print(f"Filled: {summary['filled_orders']}")
print(f"Cancelled: {summary['cancelled_orders']}")
print(f"Errors: {summary['error_orders']}")
print(f"Partial Fills: {summary['partial_fills']}")
print(f"Complete Fills: {summary['complete_fills']}")

# Get specific order history
history = broker.get_order_history(order_id=1)
for log_entry in history:
    print(log_entry)
```

## Best Practices

### 1. Always Register Callbacks Before Submitting Orders

```python
# Good
broker.register_order_fill_callback(on_fill)
order = broker.execute_market_order("AAPL", 100, "buy")

# Bad - might miss early fills
order = broker.execute_market_order("AAPL", 100, "buy")
broker.register_order_fill_callback(on_fill)  # Too late!
```

### 2. Check Connection Before Placing Orders

```python
if not broker.is_connected():
    broker.connect()

if broker.is_connected():
    order = broker.execute_market_order("AAPL", 100, "buy")
else:
    print("Failed to connect to broker")
```

### 3. Handle All Error Cases

```python
def on_error(order_record, error_message):
    # Log error
    logger.error(f"Order {order_record.order_id} failed: {error_message}")
    
    # Notify user (email, SMS, UI notification, etc.)
    notify_user(f"Order failed: {error_message}")
    
    # Record in database for audit trail
    db.record_error(order_record, error_message)
    
    # Take corrective action if needed
    if "insufficient funds" in error_message.lower():
        # Handle funding issue
        pass
```

### 4. Monitor Order Status

```python
# Use callbacks for real-time monitoring
def on_status_change(order_record):
    print(f"Order {order_record.order_id}: {order_record.status.value}")
    
    # Update UI, database, etc.
    update_ui(order_record)

broker.register_order_status_callback(on_status_change)
```

### 5. Clean Disconnection

```python
try:
    broker.connect()
    
    # Place orders
    order = broker.execute_market_order("AAPL", 100, "buy")
    
    # Wait for completion
    # ...
    
finally:
    broker.disconnect()
```

## Troubleshooting

### Order Not Being Tracked

**Problem**: Order submitted but not in `get_all_orders()`

**Solution**: Ensure order execution handler is enabled:
```python
broker = IBKRBroker(enable_order_execution=True)
```

### Callbacks Not Firing

**Problem**: Fill callbacks not being called

**Solutions**:
1. Check callbacks registered before order submission
2. Verify connection is active
3. Check event callbacks are registered (automatic when enabled)

### Logs Not Writing

**Problem**: Order logger not creating files

**Solutions**:
1. Check log directory permissions
2. Ensure `log_to_file=True` when initializing logger
3. Check disk space

### Duplicate Orders Being Created

**Problem**: Multiple identical orders despite deduplication

**Solutions**:
1. Orders with different timestamps (>60s apart) are allowed
2. Check if `quantity` or `symbol` is slightly different
3. Review deduplication logic if needed

## Advanced Topics

### Custom Retry Logic

```python
class CustomOrderHandler(OrderExecutionHandler):
    def _should_retry(self, error_code, error_message):
        # Don't retry on specific errors
        no_retry_codes = [201, 202, 203]  # Example error codes
        return error_code not in no_retry_codes
    
    def handle_error(self, order_id, error_code, error_message):
        if self._should_retry(error_code, error_message):
            return super().handle_error(order_id, error_code, error_message)
        else:
            # Mark as permanent failure
            order_record = self.get_order(order_id)
            order_record.update_status(OrderStatus.ERROR, error_message)
            return False
```

### Integration with Strategy Execution

```python
class TradingStrategy:
    def __init__(self, broker):
        self.broker = broker
        self.broker.register_order_fill_callback(self.on_fill)
    
    def on_fill(self, order_record):
        # Update strategy state
        self.update_position(order_record)
        
        # Execute next step
        if self.should_rebalance():
            self.rebalance()
    
    def execute_trade(self, symbol, quantity):
        order = self.broker.execute_market_order(symbol, quantity, "buy")
        self.pending_orders[order.order_id] = order
```

## Summary

The Order Execution Module provides a robust, production-ready solution for managing orders in IBKR. Key benefits:

- **Reliability**: Automatic retry with exponential backoff
- **Transparency**: Comprehensive logging of all order events
- **Flexibility**: Event callbacks for custom handling
- **Safety**: Duplicate prevention and error handling
- **Observability**: Real-time status tracking and history

For questions or issues, refer to the test files:
- `tests/test_brokers/test_order_execution_handler.py`
- `tests/test_brokers/test_order_logger.py`
