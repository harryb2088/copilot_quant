"""Table components for data display"""
import streamlit as st
import pandas as pd


def render_trade_log(trades_df):
    """
    Render styled trade log table
    
    Args:
        trades_df: DataFrame with trade data
    """
    if trades_df is None or trades_df.empty:
        st.info("No trades to display")
        return
    
    # Style the dataframe
    st.dataframe(
        trades_df,
        use_container_width=True,
        height=400,
        hide_index=True
    )


def render_positions(positions_df):
    """
    Render styled positions table with color coding
    
    Args:
        positions_df: DataFrame with position data
    """
    if positions_df is None or positions_df.empty:
        st.info("No active positions")
        return
    
    # Display the positions table
    st.dataframe(
        positions_df,
        use_container_width=True,
        hide_index=True
    )


def render_orders(orders_df):
    """
    Render active orders table
    
    Args:
        orders_df: DataFrame with order data
    """
    if orders_df is None or orders_df.empty:
        st.info("No active orders")
        return
    
    st.dataframe(
        orders_df,
        use_container_width=True,
        hide_index=True
    )


def render_backtest_list(backtests):
    """
    Render list of backtests as a table
    
    Args:
        backtests: List of backtest dictionaries
    """
    if not backtests:
        st.info("No backtests available")
        return
    
    df = pd.DataFrame(backtests)
    st.dataframe(
        df,
        use_container_width=True,
        hide_index=True
    )


def render_strategy_cards(strategies):
    """
    Render strategy information as cards
    
    Args:
        strategies: List of strategy dictionaries
    """
    if not strategies:
        st.info("No strategies available")
        return
    
    # Display strategies in a grid layout
    cols_per_row = 2
    for i in range(0, len(strategies), cols_per_row):
        cols = st.columns(cols_per_row)
        for j, col in enumerate(cols):
            if i + j < len(strategies):
                strategy = strategies[i + j]
                with col:
                    with st.container(border=True):
                        st.subheader(strategy['name'])
                        
                        # Status badge
                        status = strategy['status']
                        if status == 'Active':
                            st.success(f"Status: {status}")
                        elif status == 'Draft':
                            st.warning(f"Status: {status}")
                        else:
                            st.error(f"Status: {status}")
                        
                        st.write(f"**Type:** {strategy['type']}")
                        st.write(f"**Last Modified:** {strategy['last_modified']}")
                        st.caption(strategy.get('description', 'No description'))
                        
                        # Action buttons
                        col1, col2 = st.columns(2)
                        with col1:
                            if st.button("Edit", key=f"edit_{strategy['id']}"):
                                st.info(f"Edit functionality for {strategy['name']} - Coming soon!")
                        with col2:
                            if st.button("Run", key=f"run_{strategy['id']}"):
                                st.info(f"Run functionality for {strategy['name']} - Coming soon!")


def render_trades_pnl_table(trades_pnl_df):
    """
    Render trade P&L summary table with styling.
    
    Args:
        trades_pnl_df: DataFrame with trade P&L data including:
                      Entry Time, Exit Time, Entry Price, Exit Price,
                      Quantity, Side, Gross PnL, Cumulative PnL
    """
    if trades_pnl_df is None or trades_pnl_df.empty:
        st.info("No trade P&L data to display")
        return
    
    # Display the trade P&L table
    st.dataframe(
        trades_pnl_df,
        use_container_width=True,
        height=400,
        hide_index=True
    )
