"""
IBKR Orders Panel Component

Displays IBKR recent orders and order status.
"""

import logging

import pandas as pd
import streamlit as st

logger = logging.getLogger(__name__)


def render_ibkr_orders_panel(service, limit: int = 10) -> None:
    """
    Render IBKR recent orders panel.

    Args:
        service: IBKRBrokerService instance
        limit: Maximum number of orders to display
    """
    st.markdown("### 📋 Recent Orders")

    # Check if connected
    if not service.is_connected():
        st.info("Connect to IBKR to view orders")
        return

    # Get recent orders
    orders = service.get_recent_orders(limit=limit)

    if not orders:
        st.info("No recent orders")
        return

    # Convert to DataFrame for display
    df = pd.DataFrame(orders)

    # Format columns
    display_df = df.copy()

    # Rename columns for display
    column_mapping = {
        "order_id": "Order ID",
        "symbol": "Symbol",
        "action": "Action",
        "quantity": "Quantity",
        "order_type": "Type",
        "status": "Status",
        "filled": "Filled",
        "remaining": "Remaining",
        "avg_fill_price": "Avg Fill Price",
    }

    # Select and rename columns
    display_columns = [col for col in column_mapping.keys() if col in display_df.columns]
    display_df = display_df[display_columns]
    display_df = display_df.rename(columns=column_mapping)

    # Format numeric columns
    if "Quantity" in display_df.columns:
        display_df["Quantity"] = display_df["Quantity"].apply(lambda x: f"{x:.0f}")

    if "Filled" in display_df.columns:
        display_df["Filled"] = display_df["Filled"].apply(lambda x: f"{x:.0f}")

    if "Remaining" in display_df.columns:
        display_df["Remaining"] = display_df["Remaining"].apply(lambda x: f"{x:.0f}")

    if "Avg Fill Price" in display_df.columns:
        display_df["Avg Fill Price"] = display_df["Avg Fill Price"].apply(lambda x: f"${x:.2f}" if x > 0 else "—")

    # Add status indicator
    if "Status" in display_df.columns:

        def format_status(status):
            status = str(status).upper()
            if status in ["FILLED", "SUBMITTED"]:
                return f"✅ {status}"
            elif status in ["CANCELLED", "CANCELED"]:
                return f"❌ {status}"
            elif status in ["PENDINGSUBMIT", "PRESUBMITTED"]:
                return f"🟡 {status}"
            else:
                return f"⚪ {status}"

        display_df["Status"] = display_df["Status"].apply(format_status)

    # Display the table
    st.dataframe(display_df, use_container_width=True, hide_index=True)

    # Summary statistics
    total_orders = len(orders)
    filled_orders = sum(1 for o in orders if str(o.get("status", "")).upper() == "FILLED")
    pending_orders = sum(
        1 for o in orders if str(o.get("status", "")).upper() in ["SUBMITTED", "PENDINGSUBMIT", "PRESUBMITTED"]
    )

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("Total Orders", total_orders, help="Number of orders shown")

    with col2:
        st.metric("Filled", filled_orders, help="Number of filled orders")

    with col3:
        st.metric("Pending", pending_orders, help="Number of pending orders")

    st.markdown("---")


def render_orders_compact(service, limit: int = 3) -> int:
    """
    Render compact orders view (for sidebar or small displays).

    Args:
        service: IBKRBrokerService instance
        limit: Maximum number of orders to show

    Returns:
        Number of orders
    """
    if not service.is_connected():
        st.caption("Not connected")
        return 0

    orders = service.get_recent_orders(limit=limit)

    if not orders:
        st.caption("No recent orders")
        return 0

    # Show count and recent orders
    st.caption(f"**{len(orders)} Recent Order(s)**")

    for order in orders[:limit]:
        order_id = order.get("order_id", "?")
        symbol = order.get("symbol", "?")
        action = order.get("action", "?")
        quantity = order.get("quantity", 0)
        status = order.get("status", "?")

        status_icon = "✅" if status.upper() == "FILLED" else "🟡" if status.upper() == "SUBMITTED" else "⚪"

        st.caption(f"{status_icon} {order_id}: {action} {quantity:.0f} {symbol}")

    return len(orders)
