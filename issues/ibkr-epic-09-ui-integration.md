# Issue: UI Integration - Connection Status, Controls, Account Display

**Epic**: Live Trading & Interactive Brokers (IBKR) Integration  
**Priority**: High  
**Status**: Not Started  
**Created**: 2026-02-18

## Overview
Create comprehensive UI components for IBKR integration including connection status display, trading controls, account dashboard, and real-time position monitoring.

## Requirements

### 1. Connection Status Dashboard
- [ ] Real-time connection status indicator
- [ ] Broker connection health metrics
- [ ] Connection history and uptime
- [ ] Reconnection controls
- [ ] Error messages and diagnostics
- [ ] Trading mode indicator (Paper/Live)

### 2. Account Dashboard
- [ ] Account balance display (real-time)
- [ ] Buying power indicator
- [ ] Margin utilization gauge
- [ ] Daily P&L tracker
- [ ] Total portfolio value
- [ ] Account summary metrics

### 3. Position Monitor
- [ ] Real-time position list
- [ ] Position-level P&L (realized/unrealized)
- [ ] Market value and cost basis
- [ ] Position percentage of portfolio
- [ ] Quick close position buttons
- [ ] Position details modal

### 4. Order Management UI
- [ ] Active orders display
- [ ] Order history
- [ ] Order placement form
- [ ] Order modification interface
- [ ] Quick cancel buttons
- [ ] Order status real-time updates
- [ ] Order confirmation dialogs

### 5. Trading Controls
- [ ] Connect/Disconnect broker buttons
- [ ] Start/Stop strategy controls
- [ ] Emergency stop/Cancel all orders
- [ ] Trading mode switcher (with confirmation)
- [ ] Risk limit displays and controls
- [ ] Manual order entry

### 6. Real-time Updates
- [ ] WebSocket or SSE for live updates
- [ ] Position updates (< 1 second latency)
- [ ] Balance updates
- [ ] Order status updates
- [ ] Fill notifications
- [ ] Alert notifications

## Implementation Tasks

### Streamlit Components
```python
# copilot_quant/ui/components/broker_status.py
def render_broker_status(broker: IBKRBroker) -> None:
    """Render broker connection status component"""
    
# copilot_quant/ui/components/account_dashboard.py
def render_account_dashboard(account_manager: IBKRAccountManager) -> None:
    """Render account dashboard with balance and metrics"""
    
# copilot_quant/ui/components/position_monitor.py
def render_position_monitor(position_manager: IBKRPositionManager) -> None:
    """Render real-time position monitor"""
    
# copilot_quant/ui/components/order_panel.py
def render_order_panel(order_manager: IBKROrderManager) -> None:
    """Render order management panel"""
    
# copilot_quant/ui/components/trading_controls.py
def render_trading_controls(broker: IBKRBroker) -> None:
    """Render trading control buttons"""
```

### Page Structure
```python
# copilot_quant/ui/pages/live_trading.py
def live_trading_page():
    """
    Main live trading page
    """
    st.title("Live Trading Dashboard")
    
    # Connection status at top
    render_broker_status(broker)
    
    # Trading mode indicator (prominent)
    render_trading_mode_banner()
    
    # Main content in columns
    col1, col2 = st.columns([2, 1])
    
    with col1:
        # Account dashboard
        render_account_dashboard(account_manager)
        
        # Position monitor
        render_position_monitor(position_manager)
        
        # Order history
        render_order_panel(order_manager)
    
    with col2:
        # Trading controls
        render_trading_controls(broker)
        
        # Risk metrics
        render_risk_metrics()
        
        # Strategy status
        render_strategy_status()
```

### UI Mockup Structure
```
┌─────────────────────────────────────────────────────────────┐
│ 🔴 LIVE TRADING MODE - REAL MONEY AT RISK 🔴               │
├─────────────────────────────────────────────────────────────┤
│ Connection: ✅ Connected | Account: U123456 | Uptime: 2h 45m│
├──────────────────────────────────┬──────────────────────────┤
│ ACCOUNT SUMMARY                  │ TRADING CONTROLS         │
│ ┌──────────────────────────────┐ │ ┌──────────────────────┐ │
│ │ Net Liquidation: $125,430.50 │ │ │ [Disconnect Broker]  │ │
│ │ Cash: $45,230.00             │ │ │ [Stop All Strategies]│ │
│ │ Buying Power: $200,000.00    │ │ │ [Cancel All Orders]  │ │
│ │ Daily P&L: +$1,234.50 ↑      │ │ │ [Emergency Stop]     │ │
│ └──────────────────────────────┘ │ └──────────────────────┘ │
│                                  │                          │
│ POSITIONS                        │ RISK METRICS             │
│ ┌──────────────────────────────┐ │ ┌──────────────────────┐ │
│ │Symbol │Qty│Price │P&L │Close││ │ │Max Position: 80%     │ │
│ │AAPL   │100│$150  │+$500│ [X]││ │ │Daily Limit: 40%      │ │
│ │TSLA   │50 │$200  │-$250│ [X]││ │ │Loss Limit: Safe ✅   │ │
│ │SPY    │200│$420  │+$800│ [X]││ │ └──────────────────────┘ │
│ └──────────────────────────────┘ │                          │
│                                  │ STRATEGY STATUS          │
│ ACTIVE ORDERS                    │ ┌──────────────────────┐ │
│ ┌──────────────────────────────┐ │ │Pairs Trading: 🟢 ON  │ │
│ │Order │Symbol│Side│Status│Cncl││ │ │Mean Reversion: ⚫ OFF│ │
│ │12345 │MSFT  │BUY │FILLED│    ││ │ │Momentum: 🟢 ON       │ │
│ │12346 │GOOG  │SELL│PENDING│[X]││ │ └──────────────────────┘ │
│ └──────────────────────────────┘ │                          │
└──────────────────────────────────┴──────────────────────────┘
```

### Component Details

#### Connection Status Component
```python
def render_connection_status():
    status = broker.get_connection_status()
    
    if status.connected:
        st.success(f"✅ Connected to {status.broker_name}")
        col1, col2, col3 = st.columns(3)
        col1.metric("Account", status.account_id)
        col2.metric("Uptime", status.uptime)
        col3.metric("Latency", f"{status.latency_ms}ms")
    else:
        st.error("❌ Not Connected")
        if st.button("Reconnect"):
            broker.connect()
```

#### Account Dashboard Component
```python
def render_account_dashboard():
    account = account_manager.get_account_summary()
    
    col1, col2, col3, col4 = st.columns(4)
    col1.metric(
        "Net Liquidation", 
        f"${account.net_liquidation:,.2f}",
        delta=f"${account.daily_change:,.2f}"
    )
    col2.metric("Cash", f"${account.cash:,.2f}")
    col3.metric("Buying Power", f"${account.buying_power:,.2f}")
    col4.metric(
        "Daily P&L", 
        f"${account.daily_pnl:,.2f}",
        delta=f"{account.daily_pnl_pct:.2f}%"
    )
```

#### Position Monitor Component
```python
def render_position_monitor():
    positions = position_manager.get_positions()
    
    if positions:
        df = pd.DataFrame([
            {
                'Symbol': p.symbol,
                'Quantity': p.quantity,
                'Price': f"${p.market_price:.2f}",
                'Value': f"${p.market_value:,.2f}",
                'P&L': f"${p.unrealized_pnl:,.2f}",
                'P&L %': f"{p.pnl_pct:.2f}%",
                'Close': '❌'
            }
            for p in positions
        ])
        
        st.dataframe(
            df,
            use_container_width=True,
            hide_index=True
        )
        
        # Handle close button clicks
        for idx, position in enumerate(positions):
            if st.button(f"Close {position.symbol}", key=f"close_{idx}"):
                close_position(position)
    else:
        st.info("No open positions")
```

## Acceptance Criteria
- [ ] Connection status visible and updates in real-time
- [ ] Account balance displays correctly and updates
- [ ] Position monitor shows all positions with live P&L
- [ ] Orders can be placed through UI
- [ ] Active orders can be cancelled through UI
- [ ] Emergency stop button works instantly
- [ ] Trading mode clearly indicated (Paper/Live)
- [ ] All UI components are responsive
- [ ] Real-time updates work without page refresh
- [ ] UI works on desktop and tablet

## Testing Requirements
- [ ] Unit tests for UI components
- [ ] Integration tests with mock broker
- [ ] UI rendering tests
- [ ] Real-time update tests
- [ ] Responsiveness tests
- [ ] Accessibility tests
- [ ] Cross-browser tests

## UI/UX Considerations
### Color Scheme
- **Paper Mode**: Green theme, calm
- **Live Mode**: Red/orange theme, alerting
- **Positive P&L**: Green
- **Negative P&L**: Red
- **Neutral**: Gray/Blue

### Accessibility
- [ ] Sufficient color contrast
- [ ] Screen reader support
- [ ] Keyboard navigation
- [ ] Clear error messages
- [ ] Loading states for async operations

### Responsiveness
- [ ] Works on desktop (1920x1080)
- [ ] Works on laptop (1366x768)
- [ ] Works on tablet (1024x768)
- [ ] Mobile view (optional, view-only)

### Performance
- [ ] Page loads in < 2 seconds
- [ ] Updates don't cause page flicker
- [ ] Efficient re-rendering
- [ ] Lazy loading for historical data

## Related Files
- `src/ui/pages/live_trading.py` - New page (to create)
- `src/ui/components/broker_status.py` - New component (to create)
- `src/ui/components/account_dashboard.py` - New component (to create)
- `src/ui/components/position_monitor.py` - New component (to create)
- `src/ui/components/order_panel.py` - New component (to create)
- `src/ui/components/trading_controls.py` - New component (to create)
- `src/ui/app.py` - Main app (update)
- `tests/test_ui/test_live_trading.py` - Tests (to create)

## Dependencies
- streamlit
- pandas
- plotly (for charts)
- Issue #02 (Connection Management) - Required
- Issue #04 (Account Sync) - Required
- Issue #05 (Order Execution) - Required

## Real-time Update Strategy
### Option 1: Streamlit Auto-rerun
- Use `st.experimental_rerun()` with interval
- Simple but may be inefficient

### Option 2: Session State + Callbacks
- Update session state from background thread
- Trigger rerun on data change
- More efficient

### Option 3: WebSocket (Advanced)
- Custom JavaScript component
- True real-time updates
- More complex implementation

**Recommendation**: Start with Option 2, consider Option 3 for production

## Security Considerations
- [ ] Confirm dialogs for dangerous actions
- [ ] Trading mode clearly visible
- [ ] Live mode requires password confirmation
- [ ] Session timeout for inactivity
- [ ] Audit trail for all UI actions
- [ ] Rate limiting on order submissions

## References
- Streamlit documentation: https://docs.streamlit.io/
- Existing UI components in `src/ui/`
- Trading dashboard design best practices
