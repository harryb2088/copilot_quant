# Issue: Logging, Reconciliation, and Database Audit Trail

**Epic**: Live Trading & Interactive Brokers (IBKR) Integration  
**Priority**: Critical  
**Status**: Not Started  
**Created**: 2026-02-18

## Overview
Implement comprehensive logging, reconciliation, and audit trail system to track all trading activities, ensure data integrity, and support compliance and analysis.

## Requirements

### 1. Comprehensive Logging
- [ ] Connection events logging
- [ ] Order lifecycle logging
- [ ] Execution and fill logging
- [ ] Position and balance changes
- [ ] Error and warning logging
- [ ] Performance metrics logging
- [ ] User action logging
- [ ] System event logging

### 2. Database Audit Trail
- [ ] Store all orders in database
- [ ] Store all executions/fills
- [ ] Store position snapshots
- [ ] Store account snapshots
- [ ] Store strategy signals
- [ ] Store configuration changes
- [ ] Store reconciliation results
- [ ] Immutable audit records

### 3. Reconciliation System
- [ ] Daily position reconciliation
- [ ] Balance reconciliation
- [ ] Order status reconciliation
- [ ] PnL reconciliation
- [ ] Detect and report discrepancies
- [ ] Automated correction for minor issues
- [ ] Manual review workflow for major issues

### 4. Reporting
- [ ] Daily trading summary
- [ ] Monthly performance report
- [ ] Execution quality report
- [ ] Reconciliation report
- [ ] Tax reporting data
- [ ] Compliance reports
- [ ] Custom report builder

### 5. Data Retention
- [ ] Log retention policy (e.g., 7 years)
- [ ] Log rotation and archival
- [ ] Database backup strategy
- [ ] Data compression for old records
- [ ] Secure data deletion
- [ ] Export to external storage

## Implementation Tasks

### Logging System
```python
class TradingLogger:
    """
    Centralized logging for all trading activities
    """
    - log_connection_event(event: ConnectionEvent) -> None
    - log_order(order: Order) -> None
    - log_execution(execution: Execution) -> None
    - log_position_change(position: Position) -> None
    - log_balance_change(balance: AccountBalance) -> None
    - log_error(error: Exception, context: Dict) -> None
    - log_metric(name: str, value: float, tags: Dict) -> None
    - get_logs(filters: LogFilters) -> List[LogEntry]
```

### Audit Trail Manager
```python
class AuditTrailManager:
    """
    Manages immutable audit trail in database
    """
    - record_order(order: Order) -> None
    - record_execution(execution: Execution) -> None
    - record_position_snapshot(positions: List[Position]) -> None
    - record_account_snapshot(account: AccountSummary) -> None
    - record_signal(signal: Signal) -> None
    - record_config_change(change: ConfigChange) -> None
    - query_audit_trail(filters: AuditFilters) -> List[AuditRecord]
```

### Reconciliation Engine
```python
class ReconciliationEngine:
    """
    Reconciles broker data with internal records
    """
    - reconcile_positions() -> ReconciliationResult
    - reconcile_balances() -> ReconciliationResult
    - reconcile_orders() -> ReconciliationResult
    - reconcile_pnl() -> ReconciliationResult
    - schedule_reconciliation(frequency: str) -> None
    - generate_reconciliation_report() -> Report
```

### Report Generator
```python
class ReportGenerator:
    """
    Generates various trading and compliance reports
    """
    - generate_daily_summary(date: datetime.date) -> Report
    - generate_monthly_performance(month: int, year: int) -> Report
    - generate_execution_quality(start: datetime, end: datetime) -> Report
    - generate_tax_report(year: int) -> Report
    - export_report(report: Report, format: str) -> str
```

### Data Models
```python
@dataclass
class LogEntry:
    timestamp: datetime
    level: LogLevel
    category: LogCategory
    message: str
    context: Dict[str, Any]
    user_id: Optional[str]
    session_id: Optional[str]

@dataclass
class AuditRecord:
    id: str
    timestamp: datetime
    event_type: AuditEventType
    entity_type: EntityType
    entity_id: str
    data: Dict[str, Any]
    hash: str  # For integrity verification

@dataclass
class ReconciliationResult:
    timestamp: datetime
    entity_type: str
    total_records: int
    matched_records: int
    discrepancies: List[Discrepancy]
    status: ReconciliationStatus
    
@dataclass
class Discrepancy:
    field: str
    broker_value: Any
    internal_value: Any
    difference: Any
    severity: DiscrepancySeverity
    
class LogLevel(Enum):
    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"
    
class LogCategory(Enum):
    CONNECTION = "connection"
    ORDER = "order"
    EXECUTION = "execution"
    POSITION = "position"
    BALANCE = "balance"
    ERROR = "error"
    SYSTEM = "system"

class AuditEventType(Enum):
    ORDER_PLACED = "order_placed"
    ORDER_FILLED = "order_filled"
    ORDER_CANCELLED = "order_cancelled"
    POSITION_OPENED = "position_opened"
    POSITION_CLOSED = "position_closed"
    BALANCE_UPDATED = "balance_updated"
    CONFIG_CHANGED = "config_changed"
```

### Database Schema
```sql
-- Audit trail (immutable)
CREATE TABLE audit_trail (
    id UUID PRIMARY KEY,
    timestamp TIMESTAMP NOT NULL,
    event_type VARCHAR(50) NOT NULL,
    entity_type VARCHAR(50),
    entity_id VARCHAR(100),
    data JSONB,
    hash VARCHAR(64),  -- SHA-256 hash for integrity
    created_at TIMESTAMP DEFAULT NOW(),
    INDEX idx_timestamp (timestamp),
    INDEX idx_event_type (event_type),
    INDEX idx_entity (entity_type, entity_id)
);

-- Trading logs
CREATE TABLE trading_logs (
    id BIGSERIAL PRIMARY KEY,
    timestamp TIMESTAMP NOT NULL,
    level VARCHAR(20),
    category VARCHAR(50),
    message TEXT,
    context JSONB,
    user_id VARCHAR(50),
    session_id VARCHAR(100),
    INDEX idx_timestamp (timestamp),
    INDEX idx_level (level),
    INDEX idx_category (category)
);

-- Reconciliation results
CREATE TABLE reconciliation_results (
    id BIGSERIAL PRIMARY KEY,
    timestamp TIMESTAMP NOT NULL,
    entity_type VARCHAR(50),
    total_records INT,
    matched_records INT,
    discrepancy_count INT,
    status VARCHAR(20),
    details JSONB,
    INDEX idx_timestamp (timestamp),
    INDEX idx_status (status)
);

-- Daily summaries
CREATE TABLE daily_summaries (
    id BIGSERIAL PRIMARY KEY,
    date DATE NOT NULL UNIQUE,
    total_trades INT,
    total_volume BIGINT,
    gross_pnl DECIMAL(15,2),
    net_pnl DECIMAL(15,2),
    commission DECIMAL(10,2),
    win_rate DECIMAL(5,2),
    avg_win DECIMAL(15,2),
    avg_loss DECIMAL(15,2),
    largest_win DECIMAL(15,2),
    largest_loss DECIMAL(15,2),
    sharpe_ratio DECIMAL(10,4),
    created_at TIMESTAMP DEFAULT NOW()
);
```

## Logging Configuration
```yaml
logging:
  level: INFO
  format: "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
  
  handlers:
    console:
      enabled: true
      level: INFO
      
    file:
      enabled: true
      level: DEBUG
      path: /var/log/copilot_quant/trading.log
      max_bytes: 10485760  # 10MB
      backup_count: 10
      
    database:
      enabled: true
      level: INFO
      batch_size: 100
      
    syslog:
      enabled: false
      host: localhost
      port: 514
      
  categories:
    connection: INFO
    order: INFO
    execution: INFO
    position: DEBUG
    error: ERROR
```

## Acceptance Criteria
- [ ] All trading events are logged
- [ ] Logs stored in database and files
- [ ] Audit trail is immutable and verifiable
- [ ] Daily reconciliation runs automatically
- [ ] Discrepancies are detected and reported
- [ ] Reports can be generated for any date range
- [ ] Log retention policy is enforced
- [ ] Logging performance doesn't impact trading
- [ ] Unit tests for logging system
- [ ] Integration tests for reconciliation

## Testing Requirements
- [ ] Unit tests for logging system
- [ ] Unit tests for audit trail
- [ ] Unit tests for reconciliation engine
- [ ] Unit tests for report generator
- [ ] Integration tests with database
- [ ] Performance tests for high-volume logging
- [ ] Tests for log rotation
- [ ] Tests for reconciliation scenarios

## Compliance Considerations
- **Regulatory Requirements**: May need to comply with financial regulations (e.g., SEC, FINRA)
- **Data Retention**: Typically 7 years for financial records
- **Audit Trail**: Must be immutable and verifiable
- **Privacy**: PII should be handled according to regulations (GDPR, etc.)
- **Security**: Logs may contain sensitive information, encrypt at rest

## Performance Considerations
- **Async Logging**: Use async logging to avoid blocking trading operations
- **Batch Inserts**: Batch database inserts for performance
- **Log Rotation**: Automatic rotation to prevent disk filling
- **Indexing**: Proper database indexing for fast queries
- **Partitioning**: Partition large tables by date
- **Archival**: Move old logs to cheaper storage

## Related Files
- `copilot_quant/logging/trading_logger.py` - New module (to create)
- `copilot_quant/audit/audit_trail.py` - New module (to create)
- `copilot_quant/audit/reconciliation.py` - New module (to create)
- `copilot_quant/reporting/report_generator.py` - New module (to create)
- `config/logging.yaml` - Logging configuration (to create)
- `tests/test_audit/` - Tests (to create)

## Dependencies
- sqlalchemy (for database)
- pandas (for reporting)
- hashlib (for audit trail hashing)
- python-logging (built-in)
- Issue #04 (Account Sync) - Required
- Issue #05 (Order Execution) - Required

## Reconciliation Schedule
- **Real-time**: After each fill
- **Hourly**: Position and balance reconciliation
- **Daily**: Full reconciliation at market close
- **Weekly**: Deep reconciliation with historical validation
- **Monthly**: Comprehensive report generation

## References
- Python logging: https://docs.python.org/3/library/logging.html
- Financial audit trail best practices
- Compliance documentation for algorithmic trading
