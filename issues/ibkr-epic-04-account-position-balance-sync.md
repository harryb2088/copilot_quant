# Issue: Account, Position, and Balance Syncing

**Epic**: Live Trading & Interactive Brokers (IBKR) Integration  
**Priority**: High  
**Status**: In Progress  
**Created**: 2026-02-18

## Overview
Implement comprehensive account synchronization including real-time balance tracking, position monitoring, and account state management across the platform.

## Requirements

### 1. Account Information
- [x] Basic account balance retrieval (NetLiquidation, TotalCashValue, BuyingPower)
- [ ] Comprehensive account summary (all account values)
- [ ] Multiple account support
- [ ] Account type detection (paper vs live)
- [ ] Margin requirements and calculations
- [ ] Account restrictions and warnings

### 2. Position Tracking
- [x] Basic position retrieval (symbol, position, avg_cost)
- [ ] Real-time position updates
- [ ] Position P&L (realized and unrealized)
- [ ] Position Greeks (for options)
- [ ] Position-level risk metrics
- [ ] Historical position tracking

### 3. Balance Monitoring
- [ ] Real-time balance updates
- [ ] Cash balance tracking
- [ ] Margin utilization monitoring
- [ ] Buying power calculations
- [ ] Daily P&L tracking
- [ ] Performance attribution

### 4. Portfolio Analytics
- [ ] Portfolio-level risk metrics
- [ ] Exposure analysis (sector, asset class)
- [ ] Concentration risk monitoring
- [ ] Beta and correlation analysis
- [ ] VAR (Value at Risk) calculations
- [ ] Performance metrics (Sharpe, Sortino, etc.)

### 5. Database Synchronization
- [ ] Store account snapshots in database
- [ ] Store position history
- [ ] Store balance history
- [ ] Reconciliation with local state
- [ ] Audit trail for all changes
- [ ] Historical reporting

## Implementation Tasks

### Account Manager
```python
class IBKRAccountManager:
    """
    Manages account information and synchronization
    """
    - get_account_summary() -> AccountSummary
    - get_account_values() -> Dict[str, AccountValue]
    - get_margin_info() -> MarginInfo
    - register_account_callback(callback: Callable)
    - sync_account_state() -> bool
```

### Position Manager
```python
class IBKRPositionManager:
    """
    Manages position tracking and updates
    """
    - get_positions() -> List[Position]
    - get_position(symbol: str) -> Optional[Position]
    - get_position_pnl(symbol: str) -> PnL
    - register_position_callback(callback: Callable)
    - sync_positions() -> bool
```

### Portfolio Manager
```python
class IBKRPortfolioManager:
    """
    Manages portfolio-level analytics and risk
    """
    - get_portfolio_summary() -> PortfolioSummary
    - get_portfolio_risk() -> RiskMetrics
    - get_exposure_breakdown() -> Dict[str, float]
    - calculate_var() -> float
    - get_performance_metrics() -> PerformanceMetrics
```

### Data Models
```python
@dataclass
class AccountSummary:
    account_id: str
    net_liquidation: float
    total_cash_value: float
    buying_power: float
    margin_available: float
    margin_used: float
    unrealized_pnl: float
    realized_pnl: float
    timestamp: datetime

@dataclass
class Position:
    symbol: str
    quantity: float
    avg_cost: float
    market_price: float
    market_value: float
    unrealized_pnl: float
    realized_pnl: float
    timestamp: datetime
    
@dataclass
class PnL:
    realized: float
    unrealized: float
    total: float
    daily: float
```

### Database Schema
```sql
-- Account snapshots
CREATE TABLE account_snapshots (
    id SERIAL PRIMARY KEY,
    account_id VARCHAR(50),
    timestamp TIMESTAMP,
    net_liquidation DECIMAL(15,2),
    total_cash DECIMAL(15,2),
    buying_power DECIMAL(15,2),
    unrealized_pnl DECIMAL(15,2),
    realized_pnl DECIMAL(15,2),
    -- additional fields...
);

-- Position snapshots
CREATE TABLE position_snapshots (
    id SERIAL PRIMARY KEY,
    account_id VARCHAR(50),
    symbol VARCHAR(20),
    timestamp TIMESTAMP,
    quantity DECIMAL(15,4),
    avg_cost DECIMAL(15,4),
    market_price DECIMAL(15,4),
    market_value DECIMAL(15,2),
    unrealized_pnl DECIMAL(15,2),
    -- additional fields...
);
```

## Acceptance Criteria
- [ ] Account balances sync automatically on connection
- [ ] Position updates delivered in real-time
- [ ] All account data stored in database
- [ ] Reconciliation between IB and local state successful
- [ ] Portfolio analytics calculated correctly
- [ ] Performance metrics match IB reports
- [ ] All sync operations are logged
- [ ] Unit tests for all managers
- [ ] Integration tests with mock account data

## Testing Requirements
- [ ] Unit tests for account manager
- [ ] Unit tests for position manager
- [ ] Unit tests for portfolio manager
- [ ] Integration tests with mock IB data
- [ ] Reconciliation tests
- [ ] Database integration tests
- [ ] Performance tests for large portfolios

## Related Files
- `copilot_quant/brokers/interactive_brokers.py` - Current implementation
- `copilot_quant/brokers/account_manager.py` - New module (to create)
- `copilot_quant/brokers/position_manager.py` - New module (to create)
- `copilot_quant/brokers/portfolio_manager.py` - New module (to create)
- `tests/test_brokers/test_account_sync.py` - Tests (to create)

## Dependencies
- ib_insync>=0.9.86
- pandas
- sqlalchemy (for database)
- Issue #02 (Connection Management) - Required

## Notes
- Current basic implementation in `IBKRBroker.get_account_balance()` and `get_positions()`
- Need real-time callbacks for account and position updates
- Reconciliation logic critical for detecting discrepancies
- Consider implementing snapshot scheduling (e.g., every 5 minutes)
- Historical data important for performance tracking and reporting

## Reconciliation Strategy
1. Sync on connection
2. Real-time updates via callbacks
3. Periodic full sync (every 15 minutes)
4. Flag discrepancies for review
5. Automatic correction for minor differences
6. Alert for major discrepancies

## References
- [IB Account Management API](https://interactivebrokers.github.io/tws-api/account_values.html)
- [ib_insync portfolio examples](https://ib-insync.readthedocs.io/api.html#module-ib_insync.contract)
