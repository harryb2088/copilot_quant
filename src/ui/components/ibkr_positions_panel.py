"""
IBKR Positions Panel Component

Displays IBKR positions with P&L information.
"""

import streamlit as st
import pandas as pd
import logging
from typing import List, Dict, Any

logger = logging.getLogger(__name__)


def render_ibkr_positions_panel(service) -> None:
    """
    Render IBKR positions panel.
    
    Args:
        service: IBKRBrokerService instance
    """
    st.markdown("### 📊 Active Positions")
    
    # Check if connected
    if not service.is_connected():
        st.info("Connect to IBKR to view positions")
        return
    
    # Get positions
    positions = service.get_positions()
    
    if not positions:
        st.info("No active positions")
        return
    
    # Convert to DataFrame for display
    df = pd.DataFrame(positions)
    
    # Format columns
    display_df = df.copy()
    
    # Rename columns for display
    column_mapping = {
        'symbol': 'Symbol',
        'quantity': 'Shares',
        'avg_cost': 'Avg Cost',
        'market_price': 'Market Price',
        'market_value': 'Market Value',
        'unrealized_pnl': 'Unrealized P&L',
        'pnl_percentage': 'P&L %'
    }
    
    # Select and rename columns
    display_columns = [col for col in column_mapping.keys() if col in display_df.columns]
    display_df = display_df[display_columns]
    display_df = display_df.rename(columns=column_mapping)
    
    # Format numeric columns
    if 'Shares' in display_df.columns:
        display_df['Shares'] = display_df['Shares'].apply(lambda x: f"{x:.0f}")
    
    if 'Avg Cost' in display_df.columns:
        display_df['Avg Cost'] = display_df['Avg Cost'].apply(lambda x: f"${x:.2f}")
    
    if 'Market Price' in display_df.columns:
        display_df['Market Price'] = display_df['Market Price'].apply(lambda x: f"${x:.2f}")
    
    if 'Market Value' in display_df.columns:
        display_df['Market Value'] = display_df['Market Value'].apply(lambda x: f"${x:,.2f}")
    
    if 'Unrealized P&L' in display_df.columns:
        display_df['Unrealized P&L'] = display_df['Unrealized P&L'].apply(
            lambda x: f"${x:+,.2f}" if x >= 0 else f"-${abs(x):,.2f}"
        )
    
    if 'P&L %' in display_df.columns:
        display_df['P&L %'] = display_df['P&L %'].apply(lambda x: f"{x:+.2f}%")
    
    # Display the table
    st.dataframe(
        display_df,
        use_container_width=True,
        hide_index=True
    )
    
    # Summary statistics
    total_market_value = sum(pos.get('market_value', 0) for pos in positions)
    total_unrealized_pnl = sum(pos.get('unrealized_pnl', 0) for pos in positions)
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric(
            "Total Positions",
            len(positions),
            help="Number of open positions"
        )
    
    with col2:
        st.metric(
            "Total Market Value",
            f"${total_market_value:,.2f}",
            help="Combined value of all positions"
        )
    
    with col3:
        pnl_pct = (total_unrealized_pnl / total_market_value * 100) if total_market_value > 0 else 0
        st.metric(
            "Total Unrealized P&L",
            f"${total_unrealized_pnl:+,.2f}",
            delta=f"{pnl_pct:+.2f}%",
            help="Combined unrealized P&L"
        )
    
    st.markdown("---")


def render_positions_compact(service) -> int:
    """
    Render compact positions view (for sidebar or small displays).
    
    Args:
        service: IBKRBrokerService instance
        
    Returns:
        Number of positions
    """
    if not service.is_connected():
        st.caption("Not connected")
        return 0
    
    positions = service.get_positions()
    
    if not positions:
        st.caption("No positions")
        return 0
    
    # Show count and top positions
    st.caption(f"**{len(positions)} Position(s)**")
    
    for pos in positions[:3]:  # Show top 3
        symbol = pos.get('symbol', '?')
        quantity = pos.get('quantity', 0)
        pnl = pos.get('unrealized_pnl', 0)
        pnl_str = f"${pnl:+,.0f}" if pnl >= 0 else f"-${abs(pnl):,.0f}"
        st.caption(f"{symbol}: {quantity:.0f} shares ({pnl_str})")
    
    if len(positions) > 3:
        st.caption(f"... and {len(positions) - 3} more")
    
    return len(positions)
