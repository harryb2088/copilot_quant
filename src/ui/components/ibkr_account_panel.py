"""
IBKR Account Panel Component

Displays IBKR account balance and summary information.
"""

import streamlit as st
import logging
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)


def render_ibkr_account_panel(service) -> None:
    """
    Render IBKR account summary panel.
    
    Args:
        service: IBKRBrokerService instance
    """
    st.markdown("### 💰 Account Summary")
    
    # Check if connected
    if not service.is_connected():
        st.info("Connect to IBKR to view account information")
        return
    
    # Get account summary
    account = service.get_account_summary()
    
    if account is None:
        st.warning("Unable to retrieve account information")
        if service.last_error:
            st.error(f"Error: {service.last_error}")
        return
    
    # Display account metrics
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        net_liq = account.get('net_liquidation', 0)
        st.metric(
            "Account Value",
            f"${net_liq:,.2f}",
            help="Total account value (cash + positions)"
        )
    
    with col2:
        cash = account.get('total_cash_value', 0)
        st.metric(
            "Cash",
            f"${cash:,.2f}",
            help="Available cash balance"
        )
    
    with col3:
        buying_power = account.get('buying_power', 0)
        st.metric(
            "Buying Power",
            f"${buying_power:,.2f}",
            help="Available buying power"
        )
    
    with col4:
        unrealized_pnl = account.get('unrealized_pnl', 0)
        pnl_pct = (unrealized_pnl / net_liq * 100) if net_liq > 0 else 0
        st.metric(
            "Unrealized P&L",
            f"${unrealized_pnl:,.2f}",
            delta=f"{pnl_pct:+.2f}%",
            help="Unrealized profit/loss on open positions"
        )
    
    with col5:
        realized_pnl = account.get('realized_pnl', 0)
        st.metric(
            "Realized P&L",
            f"${realized_pnl:,.2f}",
            help="Realized profit/loss from closed positions"
        )
    
    # Additional info in expander
    with st.expander("📊 Detailed Account Information"):
        st.markdown("**Account Details:**")
        st.write(f"- Account ID: `{account.get('account_id', 'N/A')}`")
        st.write(f"- Gross Position Value: `${account.get('gross_position_value', 0):,.2f}`")
        st.write(f"- Net Liquidation: `${net_liq:,.2f}`")
        st.write(f"- Total Cash: `${cash:,.2f}`")
        st.write(f"- Buying Power: `${buying_power:,.2f}`")
        st.write(f"- Unrealized P&L: `${unrealized_pnl:,.2f}`")
        st.write(f"- Realized P&L: `${realized_pnl:,.2f}`")
        
        timestamp = account.get('timestamp')
        if timestamp:
            st.write(f"- Last Updated: `{timestamp}`")
    
    st.markdown("---")


def render_account_metrics_compact(service) -> Optional[Dict[str, Any]]:
    """
    Render compact account metrics (for sidebar or small displays).
    
    Args:
        service: IBKRBrokerService instance
        
    Returns:
        Account summary dict if available, None otherwise
    """
    if not service.is_connected():
        st.caption("Not connected to IBKR")
        return None
    
    account = service.get_account_summary()
    
    if account is None:
        st.caption("Account data unavailable")
        return None
    
    net_liq = account.get('net_liquidation', 0)
    unrealized_pnl = account.get('unrealized_pnl', 0)
    
    st.metric(
        "Account Value",
        f"${net_liq:,.0f}",
        delta=f"${unrealized_pnl:+,.0f}"
    )
    
    return account
