"""
Live Trading Page - Paper trading interface with safety controls
"""

import streamlit as st
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from components.sidebar import render_sidebar, render_connection_status
from components.tables import render_positions, render_orders
from utils.session import init_session_state
from utils.mock_data import generate_mock_positions

# Page configuration
st.set_page_config(
    page_title="Live Trading - Copilot Quant",
    page_icon="🔴",
    layout="wide"
)

# Initialize session state
init_session_state()

# Render sidebar
render_sidebar()
render_connection_status()

# Main content
st.title("🔴 Live Trading")
st.markdown("---")

# PROMINENT WARNING BANNER
st.error("""
### ⚠️ PAPER TRADING ONLY - NO REAL MONEY ⚠️

This platform is configured for **PAPER TRADING ONLY**. All trades are simulated using live market data.
NO REAL MONEY IS AT RISK.

**Important:**
- Orders are executed in a simulated environment
- Positions are tracked but not real
- P&L is calculated but not actual money
- This is for testing and learning purposes only
""")

st.markdown("---")

# Connection status section
st.markdown("### 🔌 Broker Connection Status")

col1, col2, col3 = st.columns(3)

with col1:
    st.markdown("**Broker**")
    st.info("Interactive Brokers")

with col2:
    st.markdown("**Status**")
    if st.session_state.get('broker_connected', False):
        st.success("🟢 Connected")
    else:
        st.error("🔴 Disconnected")

with col3:
    st.markdown("**Mode**")
    st.warning("📝 Paper Trading (Locked)")

st.markdown("---")

# Safety toggle and connection
st.markdown("### 🔒 Safety Controls")

col1, col2 = st.columns(2)

with col1:
    paper_trading_toggle = st.toggle(
        "Enable Paper Trading",
        value=st.session_state.get('paper_trading_enabled', False),
        help="Must be enabled to connect to paper trading account",
        key="paper_toggle"
    )
    
    if paper_trading_toggle != st.session_state.get('paper_trading_enabled', False):
        st.session_state.paper_trading_enabled = paper_trading_toggle
        if paper_trading_toggle:
            st.success("✅ Paper trading enabled")
        else:
            st.warning("⚠️ Paper trading disabled")
            st.session_state.broker_connected = False

with col2:
    if st.session_state.get('paper_trading_enabled', False):
        if not st.session_state.get('broker_connected', False):
            if st.button("🔌 Connect to Paper Account", type="primary", use_container_width=True):
                with st.spinner("Connecting to paper trading account..."):
                    import time
                    time.sleep(2)  # Simulate connection
                    st.session_state.broker_connected = True
                    st.rerun()
        else:
            if st.button("🔌 Disconnect", type="secondary", use_container_width=True):
                st.session_state.broker_connected = False
                st.rerun()
    else:
        st.button("🔌 Connect to Paper Account", disabled=True, use_container_width=True)
        st.caption("Enable paper trading first")

st.markdown("---")

# Only show trading interface if connected
if st.session_state.get('broker_connected', False):
    # Account summary
    st.markdown("### 💰 Account Summary")
    
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        st.metric("Account Value", "$100,408")
    
    with col2:
        st.metric("Cash", "$96,500")
    
    with col3:
        st.metric("Buying Power", "$193,000")
    
    with col4:
        st.metric("Day P&L", "+$408", delta="+0.41%")
    
    with col5:
        st.metric("Total P&L", "+$408", delta="+0.41%")
    
    st.markdown("---")
    
    # Active positions
    st.markdown("### 📊 Active Positions")
    
    positions_df = generate_mock_positions()
    
    if not positions_df.empty:
        render_positions(positions_df)
        
        # Position actions
        st.markdown("#### Position Actions")
        cols = st.columns(len(positions_df))
        for i, (col, idx) in enumerate(zip(cols, positions_df.index)):
            with col:
                symbol = positions_df.loc[idx, 'Symbol']
                if st.button(f"Close {symbol}", key=f"close_{symbol}", use_container_width=True):
                    st.success(f"✅ Close order submitted for {symbol}")
                    st.info("Order execution simulation - Position would be closed in real paper trading")
    else:
        st.info("No active positions")
    
    st.markdown("---")
    
    # Active orders
    st.markdown("### 📋 Active Orders")
    
    # Mock empty orders table
    render_orders(None)
    
    st.markdown("---")
    
    # Strategy deployment
    st.markdown("### 🚀 Deploy Strategy")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown("""
        Deploy a strategy to run automatically in paper trading mode.
        The strategy will monitor the market and execute trades based on its rules.
        """)
    
    with col2:
        if st.button("📊 Select Strategy to Deploy", type="primary", use_container_width=True):
            st.switch_page("pages/2_📊_Strategies.py")
    
    # Active strategies section
    with st.expander("🤖 Active Strategies"):
        st.info("No strategies currently deployed")
        st.markdown("""
        **To deploy a strategy:**
        1. Go to Strategies page
        2. Select a strategy
        3. Click "Deploy to Paper Trading"
        4. Configure deployment parameters
        5. Start the strategy
        """)
    
    st.markdown("---")
    
    # Risk management
    st.markdown("### ⚠️ Risk Management")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        with st.container(border=True):
            st.markdown("**Max Position Size**")
            max_position = st.slider("% of Portfolio", 1, 50, 10, key="max_pos")
            st.caption(f"Max ${100000 * max_position / 100:,.0f} per position")
    
    with col2:
        with st.container(border=True):
            st.markdown("**Max Daily Loss**")
            max_loss = st.slider("% of Portfolio", 1, 20, 5, key="max_loss")
            st.caption(f"Stop if loss exceeds ${100000 * max_loss / 100:,.0f}")
    
    with col3:
        with st.container(border=True):
            st.markdown("**Max Open Positions**")
            max_positions = st.slider("Number of Positions", 1, 20, 10, key="max_positions")
            st.caption("Maximum concurrent positions")
    
    if st.button("💾 Save Risk Settings", use_container_width=True):
        st.success("✅ Risk management settings saved!")
    
    st.markdown("---")
    
    # Trading log
    st.markdown("### 📝 Today's Trading Activity")
    
    with st.container(border=True):
        st.markdown("""
        **Recent Activity:**
        - 09:35 AM - Bought 150 AAPL @ $175.50
        - 10:20 AM - Bought 80 GOOGL @ $138.20
        - 11:45 AM - Bought 200 MSFT @ $380.00
        
        **Summary:**
        - Total Trades: 3
        - Total Volume: 430 shares
        - Avg Execution: 2.3 seconds
        """)

else:
    # Not connected - show connection instructions
    st.info("""
    ### 🔌 Connect to Paper Trading
    
    To start paper trading:
    
    1. ✅ **Enable Paper Trading** using the toggle above
    2. 🔌 **Click "Connect to Paper Account"** to establish connection
    3. 📊 **Monitor positions and orders** in real-time
    4. 🚀 **Deploy strategies** to trade automatically
    
    **Note:** This is a simulated trading environment. No real money is involved.
    """)
    
    st.markdown("---")
    
    st.markdown("### 📚 Before You Start")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        **✅ Recommended Steps:**
        - Review your strategy backtests
        - Understand the risks involved
        - Set appropriate position sizes
        - Configure risk management rules
        - Start with small positions
        """)
    
    with col2:
        st.markdown("""
        **⚠️ Important Reminders:**
        - Paper trading simulates real market conditions
        - Execution may differ in live trading
        - Use this to learn and test strategies
        - No real money is at risk
        - Always practice good risk management
        """)

# Help section
with st.expander("ℹ️ Paper Trading Guide"):
    st.markdown("""
    ### What is Paper Trading?
    
    Paper trading is simulated trading using real market data but without real money.
    It allows you to:
    
    - Test strategies in real market conditions
    - Practice trading without financial risk
    - Learn platform functionality
    - Build confidence before live trading
    
    ### How It Works
    
    1. **Real Data**: Uses live market prices and order books
    2. **Simulated Execution**: Orders are simulated but not sent to market
    3. **Realistic Fills**: Simulates order execution with market prices
    4. **Position Tracking**: Tracks your positions as if they were real
    5. **P&L Calculation**: Calculates profits and losses in real-time
    
    ### Limitations of Paper Trading
    
    - No real market impact (slippage may differ)
    - Order fills may be more optimistic
    - No emotional pressure of real money
    - Liquidity assumptions may not hold
    - Execution speed may differ
    
    ### Best Practices
    
    - Treat it like real trading
    - Use realistic position sizes
    - Follow your risk management rules
    - Keep a trading journal
    - Review your performance regularly
    
    ### Transitioning to Live Trading
    
    Before going live (future feature):
    - Achieve consistent profitability in paper trading
    - Understand all platform features
    - Have a solid risk management plan
    - Start with very small positions
    - Be prepared for emotional challenges
    """)

# Footer
st.caption("🔒 Remember: Paper trading only - No real money at risk")
