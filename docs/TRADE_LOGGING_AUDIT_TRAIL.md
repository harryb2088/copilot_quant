# Trade Logging and Audit Trail Documentation

## Overview

The trade logging and audit trail system provides comprehensive tracking and reconciliation of all trading activity with Interactive Brokers (IBKR). This system is designed for compliance, backtesting analysis, and trade verification.

## Architecture

The system consists of four main components:

1. **OrderLogger** - Structured logging of order events to files
2. **TradeDatabase** - SQLAlchemy-based database storage for audit trail
3. **TradeReconciliation** - Comparison of local logs with IBKR account history
4. **AuditTrail** - Unified interface combining all components

## Components

### 1. Order Logger

The `OrderLogger` provides structured JSON logging for all order-related events:

```python
from copilot_quant.brokers import OrderLogger

# Initialize logger
logger = OrderLogger(
    log_to_file=True,
    log_dir="./logs/orders",
    log_to_console=True
)

# Log events (automatically done by broker)
logger.log_submission(order_record)
logger.log_fill(order_record, fill)
logger.log_status_change(order_record, old_status, new_status)
logger.log_cancellation(order_record, reason)
logger.log_error(order_record, error_message)

# Query logs
history = logger.get_order_history(order_id)
summary = logger.get_todays_summary()
```

**Log Format:**
- One JSON entry per line for easy parsing
- Each entry includes timestamp, event_type, and event data
- Logs stored in `./logs/orders/orders_YYYYMMDD.log`

**Events Logged:**
- `SUBMISSION` - Order submitted to broker
- `FILL` - Order filled (complete or partial)
- `STATUS_CHANGE` - Order status update
- `CANCELLATION` - Order cancelled
- `ERROR` - Order error occurred
- `RETRY` - Order retry attempt

### 2. Trade Database

The `TradeDatabase` provides persistent storage using SQLAlchemy:

```python
from copilot_quant.brokers import TradeDatabase

# Initialize database
db = TradeDatabase("sqlite:///trade_audit.db")

# Store data (automatically done by AuditTrail)
db.store_order(order_record)
db.store_fill(fill, order_id)
db.store_reconciliation_report(report)

# Query data
orders = db.get_orders_by_date(date.today())
fills = db.get_fills_by_order(order_id)
reports = db.get_reconciliation_reports(start_date, end_date)
audit_data = db.get_audit_trail(start_date, end_date)
```

**Database Schema:**

**orders** table:
- `id` - Primary key (auto-increment)
- `order_id` - IBKR order ID
- `symbol` - Stock symbol
- `action` - BUY or SELL
- `total_quantity` - Total order quantity
- `order_type` - MARKET, LIMIT, etc.
- `limit_price` - Limit price (if applicable)
- `status` - Current order status
- `filled_quantity` - Quantity filled so far
- `remaining_quantity` - Quantity remaining
- `avg_fill_price` - Average fill price
- `error_message` - Error details (if any)
- `submission_time` - When order was submitted
- `last_update_time` - Last status update time
- `retry_count` - Number of retry attempts

**fills** table:
- `id` - Primary key (auto-increment)
- `fill_id` - Unique fill identifier (UUID)
- `order_id` - Associated order ID
- `order_db_id` - Foreign key to orders table
- `symbol` - Stock symbol
- `quantity` - Shares filled
- `price` - Fill price
- `commission` - Commission charged
- `timestamp` - Fill timestamp

**reconciliation_reports** table:
- `id` - Primary key (auto-increment)
- `reconciliation_date` - Date reconciled
- `timestamp` - Report generation time
- `total_ibkr_fills` - Number of IBKR fills
- `total_local_fills` - Number of local fills
- `matched_orders` - Number of matched orders
- `total_discrepancies` - Number of discrepancies found
- `summary_json` - Full summary as JSON

**discrepancies** table:
- `id` - Primary key (auto-increment)
- `report_id` - Foreign key to reconciliation_reports
- `type` - Discrepancy type
- `order_id` - Affected order ID
- `symbol` - Stock symbol
- `description` - Human-readable description
- `ibkr_fill_json` - IBKR fill data as JSON
- `local_fill_json` - Local fill data as JSON

### 3. Trade Reconciliation

The `TradeReconciliation` module compares local logs with IBKR fills:

```python
from copilot_quant.brokers import TradeReconciliation

# Initialize reconciler
reconciler = TradeReconciliation(
    broker,
    price_tolerance=0.01,      # $0.01 price tolerance
    commission_tolerance=0.01  # $0.01 commission tolerance
)

# Reconcile trades
report = reconciler.reconcile_today()
report = reconciler.reconcile(target_date)
reports = reconciler.reconcile_date_range(start_date, end_date)

# Check for issues
if report.has_discrepancies():
    print(f"Found {len(report.discrepancies)} discrepancies")
    for disc in report.discrepancies:
        print(f"  {disc.type.value}: {disc.description}")

# Get summary
summary = report.summary()
print(f"Matched: {summary['matched_orders']}")
print(f"Discrepancies: {summary['total_discrepancies']}")
```

**Reconciliation Algorithm:**

1. **Fetch Data:**
   - Retrieve all IBKR fills for the target date using `ib.fills()`
   - Retrieve all local fills from OrderExecutionHandler

2. **Normalize Data:**
   - Convert IBKR fills to `IBKRFill` objects
   - Convert local fills to `LocalFill` objects
   - Both contain: order_id, symbol, side, quantity, price, commission, timestamp

3. **Match by Order ID:**
   - Group fills by order_id from both sources
   - Compare fills for each order

4. **Detect Discrepancies:**
   - **MISSING_LOCAL:** Fill exists in IBKR but not locally
   - **MISSING_IBKR:** Fill exists locally but not in IBKR
   - **QUANTITY_MISMATCH:** Different total quantities
   - **PRICE_MISMATCH:** Price difference exceeds tolerance
   - **COMMISSION_MISMATCH:** Commission difference exceeds tolerance

5. **Generate Report:**
   - List of all discrepancies with details
   - Summary statistics
   - Matched order IDs

**Discrepancy Types:**
- `MISSING_LOCAL` - Trade in IBKR but not in local logs
- `MISSING_IBKR` - Trade in local logs but not in IBKR
- `QUANTITY_MISMATCH` - Different quantities
- `PRICE_MISMATCH` - Different prices (beyond tolerance)
- `COMMISSION_MISMATCH` - Different commissions (beyond tolerance)

### 4. Audit Trail (Unified Interface)

The `AuditTrail` provides a high-level interface:

```python
from copilot_quant.brokers import AuditTrail

# Initialize audit trail
audit = AuditTrail(
    broker,
    database_url="sqlite:///trade_audit.db",
    auto_reconcile=False
)

# Enable automatic capture
audit.enable()

# Now all orders and fills are automatically logged and stored

# Reconcile
report = audit.reconcile_today()
report = audit.reconcile_date(target_date)
reports = audit.reconcile_range(start_date, end_date)

# Query
orders = audit.get_orders_by_date(date.today())
fills = audit.get_fills_by_date(date.today())
history = audit.get_order_history(order_id)

# Generate compliance reports
json_report = audit.generate_compliance_report(
    start_date, end_date, format='json'
)
text_report = audit.generate_compliance_report(
    start_date, end_date, format='text'
)

# Export to file
audit.export_audit_trail(
    start_date, end_date, 
    output_file="audit_report.json"
)

# Check compliance
status = audit.check_compliance(
    start_date, end_date,
    max_discrepancies=0  # Zero-tolerance policy
)
if not status['compliant']:
    print("Compliance check failed!")
```

## Complete Usage Example

```python
from datetime import date
from copilot_quant.brokers import IBKRBroker, AuditTrail

# 1. Initialize broker with logging enabled
broker = IBKRBroker(
    paper_trading=True,
    enable_order_execution=True,
    enable_order_logging=True
)

# 2. Connect to IBKR
if not broker.connect():
    raise RuntimeError("Failed to connect to IBKR")

# 3. Initialize audit trail
audit = AuditTrail(broker, database_url="sqlite:///my_audit.db")
audit.enable()  # Start automatic capture

# 4. Execute some trades
order1 = broker.execute_market_order("AAPL", 100, "buy")
order2 = broker.execute_limit_order("GOOGL", 50, 2800.0, "buy")

# ... trades execute and fills occur automatically ...

# 5. End of day reconciliation
report = audit.reconcile_today()

print(f"Reconciliation Summary:")
print(f"  IBKR Fills: {len(report.ibkr_fills)}")
print(f"  Local Fills: {len(report.local_fills)}")
print(f"  Matched Orders: {len(report.matched_order_ids)}")
print(f"  Discrepancies: {len(report.discrepancies)}")

if report.has_discrepancies():
    print("\nDiscrepancies found:")
    for disc in report.discrepancies:
        print(f"  - {disc.type.value}: {disc.description}")

# 6. Generate compliance report
audit.export_audit_trail(
    date.today(), 
    date.today(),
    output_file="daily_audit.json"
)

# 7. Check compliance
status = audit.check_compliance(
    date.today(), 
    date.today(),
    max_discrepancies=0
)
print(f"\nCompliance Status: {'PASS' if status['compliant'] else 'FAIL'}")

# 8. Disconnect
broker.disconnect()
```

## Integration with Existing Code

The audit trail integrates automatically with the existing `IBKRBroker`:

```python
# Broker already has OrderLogger and OrderExecutionHandler
broker = IBKRBroker(
    enable_order_execution=True,  # Enables OrderExecutionHandler
    enable_order_logging=True      # Enables OrderLogger
)
broker.connect()

# Just add AuditTrail on top
audit = AuditTrail(broker)
audit.enable()

# Everything else works as before
# Orders and fills are automatically captured
```

## Compliance and Regulatory Use

The audit trail is designed for regulatory compliance:

1. **Complete History:** All orders and fills are logged with timestamps
2. **Immutable Logs:** Database provides permanent record
3. **Reconciliation:** Daily verification against broker records
4. **Discrepancy Detection:** Automatic identification of mismatches
5. **Export Capability:** Generate reports in JSON or text format
6. **Query Interface:** Flexible querying for analysis

**Best Practices:**
- Enable audit trail at startup
- Run daily reconciliation
- Set strict tolerances (price_tolerance=0.01, commission_tolerance=0.01)
- Export weekly/monthly compliance reports
- Investigate all discrepancies immediately
- Keep database backups

## Performance Considerations

- **File Logs:** Minimal overhead, one write per event
- **Database:** Uses connection pooling for efficiency
- **Reconciliation:** Run during off-hours or after market close
- **Storage:** ~1KB per order, ~500 bytes per fill
- **SQLite:** Suitable for small to medium volumes
- **PostgreSQL/MySQL:** Recommended for high-volume production

## Troubleshooting

### No fills captured
- Check that `enable_order_execution=True` when creating broker
- Ensure `audit.enable()` was called
- Verify broker is connected before executing orders

### Reconciliation shows MISSING_LOCAL
- Order was executed outside of this system
- OrderExecutionHandler was not enabled
- System was restarted and lost in-memory state
- **Solution:** Use database-backed order tracking

### Reconciliation shows MISSING_IBKR
- Order was logged but not actually submitted to IBKR
- IBKR rejected the order
- Order is still pending
- **Solution:** Check order status and error messages

### Database errors
- Check database URL is correct
- Ensure write permissions for SQLite file
- For PostgreSQL/MySQL, verify credentials
- **Solution:** Check database connectivity

## Database Migration

To migrate to a different database:

```python
# Export from old database
old_db = TradeDatabase("sqlite:///old_audit.db")
audit_data = old_db.get_audit_trail(start_date, end_date)

# Import to new database
new_db = TradeDatabase("postgresql://user:pass@localhost/audit")

# Recreate orders and fills
for order_data in audit_data['orders']:
    # Convert dict back to OrderRecord and store
    # (Implementation would need custom conversion logic)
    pass
```

## API Reference

See individual module docstrings for detailed API documentation:

- `copilot_quant.brokers.order_logger.OrderLogger`
- `copilot_quant.brokers.trade_database.TradeDatabase`
- `copilot_quant.brokers.trade_reconciliation.TradeReconciliation`
- `copilot_quant.brokers.audit_trail.AuditTrail`
