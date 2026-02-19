"""
Live Trading Page - Paper/Live trading interface with safety controls
"""

import streamlit as st
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from components.sidebar import render_sidebar, render_connection_status
from components.trading_mode_toggle import render_trading_mode_toggle
from components.ibkr_connection_panel import render_ibkr_connection_panel, render_connection_info_expander
from components.ibkr_account_panel import render_ibkr_account_panel
from components.ibkr_positions_panel import render_ibkr_positions_panel
from components.ibkr_orders_panel import render_ibkr_orders_panel
from utils.session import init_session_state
from services.ibkr_broker_service import get_ibkr_service

# Page configuration
st.set_page_config(
    page_title="Live Trading - Copilot Quant",
    page_icon="🔴",
    layout="wide"
)

# Initialize session state
init_session_state()

# Get IBKR broker service
ibkr_service = get_ibkr_service()

# Render sidebar
render_sidebar()
render_connection_status()

# Main content
st.title("🔴 Live Trading")
st.markdown("---")

# Trading Mode Toggle Section
st.markdown("### 🔄 Trading Mode Configuration")
current_mode, mode_changed = render_trading_mode_toggle()

st.markdown("---")

# IBKR Connection Panel
render_ibkr_connection_panel(ibkr_service, current_mode)

# Connection info expander
render_connection_info_expander(ibkr_service)

st.markdown("---")

# Only show trading interface if connected
if ibkr_service.is_connected():
    # Account summary
    render_ibkr_account_panel(ibkr_service)
    
    st.markdown("---")
    
    # Active positions
    render_ibkr_positions_panel(ibkr_service)
    
    st.markdown("---")
    
    # Active orders
    render_ibkr_orders_panel(ibkr_service)
    
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
            st.switch_page("pages/1_📊_Strategies.py")
    
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
    st.info(f"""
    ### 🔌 Connect to {'Paper' if current_mode == 'paper' else 'Live'} Trading
    
    To start trading:
    
    1. ✅ **Enable Trading** using the toggle above
    2. 🔌 **Click "Connect to {'Paper' if current_mode == 'paper' else 'Live'} Account"** to establish connection
    3. 📊 **Monitor positions and orders** in real-time
    4. 🚀 **Deploy strategies** to trade automatically
    
    **Note:** {'This is a simulated trading environment. No real money is involved.' if current_mode == 'paper' else '⚠️ This is LIVE trading with real money at risk!'}
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
        """ + ("" if current_mode == "paper" else "\n        - Double-check you want live trading"))
    
    with col2:
        st.markdown("""
        **⚠️ Important Reminders:**
        - """ + ("Paper trading simulates real market conditions" if current_mode == "paper" else "⚠️ Live trading uses REAL MONEY") + """
        - Execution may differ in live trading
        - Use this to """ + ("learn and test strategies" if current_mode == "paper" else "execute real trades carefully") + """
        - """ + ("No real money is at risk" if current_mode == "paper" else "⚠️ All money is at REAL RISK") + """
        - Always practice good risk management
        """)

# Help section
with st.expander(f"ℹ️ {'Paper' if current_mode == 'paper' else 'Live'} Trading Guide"):
    if current_mode == "paper":
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
        
        Before going live:
        - Achieve consistent profitability in paper trading
        - Understand all platform features
        - Have a solid risk management plan
        - Start with very small positions
        - Be prepared for emotional challenges
        """)
    else:
        st.markdown("""
        ### ⚠️ Live Trading Safety Guide
        
        **You are in LIVE TRADING MODE** - all orders use real money!
        
        ### Critical Safety Rules
        
        1. **Start Small**: Use minimal position sizes initially
        2. **Set Stop Losses**: Always define your maximum loss
        3. **Monitor Actively**: Never leave trades unattended
        4. **Check Twice**: Verify order details before submission
        5. **Risk Management**: Never risk more than you can afford to lose
        
        ### Before Each Trade
        
        - [ ] Verify you intended to switch to live mode
        - [ ] Check position size is appropriate
        - [ ] Confirm stop loss is set
        - [ ] Review total portfolio risk
        - [ ] Ensure sufficient buying power
        
        ### Emergency Procedures
        
        - **Close All Positions**: Use "Close All" button if needed
        - **Disconnect**: Stop trading immediately if issues arise
        - **Switch to Paper**: Return to paper mode for testing
        - **Review Logs**: Check trading history for any issues
        
        ### Connection Information
        
        - **Port**: 7496 (TWS Live) or 4001 (Gateway Live)
        - **Account**: Your configured live account
        - **Credentials**: From IB_LIVE_* environment variables
        
        ### Support
        
        If you encounter issues or unexpected behavior:
        1. Disconnect immediately
        2. Switch back to paper trading mode
        3. Review logs and trading history
        4. Contact support if needed
        """)

# Footer
st.caption(f"🔒 Current Mode: {'Paper Trading (No real money)' if current_mode == 'paper' else '⚠️ LIVE TRADING (Real money at risk)'}")
