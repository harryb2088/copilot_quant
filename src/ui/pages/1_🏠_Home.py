"""
Home Page - Main dashboard and overview
"""

import streamlit as st
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from components.sidebar import render_sidebar
from utils.session import init_session_state

# Page configuration
st.set_page_config(
    page_title="Home - Copilot Quant",
    page_icon="🏠",
    layout="wide"
)

# Initialize session state
init_session_state()

# Render sidebar
render_sidebar()

# Main content
st.title("🏠 Home")
st.markdown("---")

st.markdown("""
## Welcome to Copilot Quant Platform

Your comprehensive algorithmic trading platform for strategy development, 
backtesting, and paper trading.
""")

# Quick stats dashboard
st.markdown("### 📊 Quick Stats")

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric(
        label="Total Strategies",
        value="4",
        delta="2 active"
    )

with col2:
    st.metric(
        label="Active Backtests",
        value="1",
        delta="+1 running",
        delta_color="normal"
    )

with col3:
    st.metric(
        label="Paper Trading Status",
        value="Inactive",
        delta="Disconnected",
        delta_color="off"
    )

with col4:
    st.metric(
        label="Total P&L (Paper)",
        value="$408",
        delta="+2.1%"
    )

st.markdown("---")

# Getting started guide
st.markdown("### 🚀 Getting Started")

tab1, tab2, tab3 = st.tabs(["📚 Quick Start", "⚡ Features", "🔒 Safety"])

with tab1:
    st.markdown("""
    #### Quick Start Guide
    
    1. **Create a Strategy** 📊
       - Navigate to the Strategies page
       - Click "Create New Strategy" or explore existing templates
       - Define your trading logic and parameters
    
    2. **Run a Backtest** 🔬
       - Go to the Backtests page
       - Select a strategy and configure parameters
       - Run the backtest on historical data
    
    3. **Analyze Results** 📈
       - View performance metrics and charts
       - Review trade logs and statistics
       - Optimize strategy parameters
    
    4. **Paper Trading** 🔴
       - Deploy to paper trading environment
       - Monitor live performance
       - Test with real market data (no real money)
    """)

with tab2:
    st.markdown("""
    #### Platform Features
    
    **Strategy Development**
    - Custom strategy builder
    - Pre-built strategy templates
    - Parameter optimization
    - Risk management tools
    
    **Backtesting Engine**
    - Historical data simulation
    - Realistic order execution
    - Transaction cost modeling
    - Slippage simulation
    
    **Analytics & Reporting**
    - Comprehensive performance metrics
    - Interactive charts and visualizations
    - Trade-by-trade analysis
    - Risk metrics and ratios
    
    **Paper Trading**
    - Real-time market data
    - Live order execution (simulated)
    - Position monitoring
    - P&L tracking
    """)

with tab3:
    st.markdown("""
    #### Safety & Risk Management
    
    ⚠️ **IMPORTANT: Paper Trading Only**
    
    This platform is currently configured for **PAPER TRADING ONLY**.
    
    - ✅ No real money at risk
    - ✅ Safe testing environment
    - ✅ Real market data
    - ✅ Realistic simulation
    
    **Safety Features**
    - Mandatory paper trading mode
    - Position size limits
    - Risk management controls
    - Automatic stop-loss
    - Maximum drawdown protection
    
    **Note**: Before any live trading (future feature), you will need to:
    - Complete additional safety checks
    - Verify account configuration
    - Acknowledge risk disclaimers
    - Enable explicit permissions
    """)

st.markdown("---")

# Quick actions
st.markdown("### ⚡ Quick Actions")

col1, col2, col3, col4 = st.columns(4)

with col1:
    if st.button("📊 View Strategies", use_container_width=True):
        st.switch_page("pages/2_📊_Strategies.py")

with col2:
    if st.button("🔬 Run Backtest", use_container_width=True):
        st.switch_page("pages/3_🔬_Backtests.py")

with col3:
    if st.button("📈 View Results", use_container_width=True):
        st.switch_page("pages/4_📈_Results.py")

with col4:
    if st.button("🔴 Paper Trading", use_container_width=True):
        st.switch_page("pages/5_🔴_Live_Trading.py")

st.markdown("---")

# Recent activity (placeholder)
st.markdown("### 📝 Recent Activity")

with st.container(border=True):
    st.markdown("""
    - 🔬 Backtest completed: "Mean Reversion Alpha" (+18.5% return)
    - 📊 Strategy updated: "Momentum Breakout"
    - 🔴 Paper trading session: 3 trades executed today
    - 📈 New performance report generated
    """)

# Footer
st.caption("Copilot Quant Platform © 2024 | Paper Trading Only")
