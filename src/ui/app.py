"""
Copilot Quant Platform - Main Streamlit Application

This is the entry point for the multi-page Streamlit application.
Run with: streamlit run src/ui/app.py
"""

import streamlit as st
from components.sidebar import render_sidebar
from utils.session import init_session_state

# Page configuration
st.set_page_config(
    page_title="Copilot Quant Platform",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize session state
init_session_state()

# Render sidebar
render_sidebar()

# Main page content
st.title("🚀 Copilot Quant Platform")
st.markdown("---")

st.markdown("""
## Welcome to Your Algorithmic Trading Platform

Copilot Quant is a comprehensive platform for developing, testing, and deploying 
quantitative trading strategies.

### 🎯 Quick Start Guide

1. **📊 Strategies** - Create and manage your trading strategies
2. **🔬 Backtests** - Test strategies against historical data
3. **📈 Results** - Analyze backtest performance and metrics
4. **🔴 Live Trading** - Deploy strategies in paper trading mode

### ⚡ Platform Features

- **Strategy Development**: Build custom trading strategies with ease
- **Backtesting Engine**: Test strategies on historical market data
- **Performance Analytics**: Comprehensive metrics and visualizations
- **Paper Trading**: Safe testing environment with real market data
- **Risk Management**: Built-in position sizing and risk controls

### 🔒 Safety First

This platform currently operates in **PAPER TRADING ONLY** mode. No real money 
will be at risk. All trades are simulated using live market data.

### 📊 Current Status

""")

# Quick stats dashboard
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric(
        label="Total Strategies",
        value="4",
        delta="0 this week"
    )

with col2:
    st.metric(
        label="Active Backtests",
        value="1",
        delta="+1 running"
    )

with col3:
    st.metric(
        label="Paper Trading",
        value="Inactive",
        delta="Disconnected"
    )

with col4:
    st.metric(
        label="Platform Version",
        value="v0.1.0",
        delta="alpha"
    )

st.markdown("---")

# Navigation buttons
st.markdown("### 🧭 Navigate to:")

col1, col2, col3 = st.columns(3)

with col1:
    st.page_link("pages/2_📊_Strategies.py", label="📊 View Strategies", icon="📊")
    st.page_link("pages/3_🔬_Backtests.py", label="🔬 Run Backtests", icon="🔬")

with col2:
    st.page_link("pages/4_📈_Results.py", label="📈 View Results", icon="📈")
    st.page_link("pages/5_🔴_Live_Trading.py", label="🔴 Live Trading", icon="🔴")

with col3:
    st.info("**Getting Started**\n\n"
            "1. Check out available strategies\n"
            "2. Run a backtest\n"
            "3. Review the results\n"
            "4. Deploy to paper trading")

st.markdown("---")

# System information
with st.expander("ℹ️ System Information"):
    st.markdown("""
    **Platform**: Copilot Quant v0.1.0-alpha  
    **Mode**: Paper Trading Only  
    **Broker**: Interactive Brokers (Not Connected)  
    **Data Provider**: Mock Data (Development)  
    
    **Note**: This is a development version. Backend integration is in progress.
    """)

# Footer
st.caption("Copilot Quant Platform © 2024 | For educational and paper trading purposes only")
