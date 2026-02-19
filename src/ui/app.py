"""
Copilot Quant Platform - Main Streamlit Application

Professional Bloomberg-style interface for algorithmic trading.
This is the entry point for the multi-page Streamlit application.
Run with: streamlit run src/ui/app.py
"""

import streamlit as st
from components.sidebar import render_sidebar
from components.trading_mode_toggle import render_mode_status_banner
from utils.auth import init_authentication
from utils.session import init_session_state

# Page configuration
st.set_page_config(page_title="Copilot Quant Platform", page_icon="🚀", layout="wide", initial_sidebar_state="expanded")

# Custom CSS for professional dark theme
st.markdown(
    """
<style>
    /* Metric styling - bold numbers */
    [data-testid="stMetricValue"] {
        font-size: 28px;
        font-weight: 700;
    }

    /* Headers */
    h1, h2, h3 {
        font-weight: 600;
        letter-spacing: -0.5px;
    }
</style>
""",
    unsafe_allow_html=True,
)

# Initialize authentication (must be called before any other st commands that display content)
name, authentication_status, username = init_authentication()

# Initialize session state
init_session_state()

# Render sidebar
render_sidebar()

# Main page content
st.title("🚀 Copilot Quant Platform")
st.markdown("**Professional Algorithmic Trading & Portfolio Analytics**")
st.markdown("---")

# Show current trading mode status
render_mode_status_banner()
st.markdown("---")

st.markdown("""
### Welcome to Your Professional Trading Platform

Copilot Quant delivers institutional-grade tools for developing, testing, and deploying
quantitative trading strategies with a Bloomberg Terminal-inspired interface.

#### 🎯 Platform Capabilities

**Strategy Development** - Build and refine custom trading strategies
**Backtesting Engine** - Validate strategies against historical market data
**Performance Analytics** - Comprehensive metrics and professional visualizations
**Paper Trading** - Risk-free testing with real market data
**Risk Management** - Built-in position sizing and risk controls

#### 🔒 Safety & Security

Operating in **PAPER TRADING ONLY** mode - zero real money at risk.
All trades are simulated using live market data for realistic testing.
""")

st.markdown("---")

# Quick stats dashboard with professional styling
st.markdown("### 📊 Platform Status")

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric(label="Total Strategies", value="4", delta="Active")

with col2:
    st.metric(label="Backtests", value="12", delta="+3 this week")

with col3:
    st.metric(label="Paper Trading", value="Ready", delta="Disconnected")

with col4:
    st.metric(label="Platform Version", value="v2.0", delta="Bloomberg UI")

st.markdown("---")

# Navigation - More compact and professional
st.markdown("### 🧭 Quick Navigation")

col1, col2, col3 = st.columns(3)

with col1:
    st.page_link("pages/1_📊_Portfolio_Dashboard.py", label="📊 Portfolio Dashboard", icon="📊")
    st.page_link("pages/2_📊_Strategies.py", label="📊 Strategies", icon="📊")

with col2:
    st.page_link("pages/3_🔬_Backtests.py", label="🔬 Backtests", icon="🔬")
    st.page_link("pages/4_📈_Results.py", label="📈 Results", icon="📈")

with col3:
    st.page_link("pages/5_🔴_Live_Trading.py", label="🔴 Live Trading", icon="🔴")
    st.page_link("pages/6_🛡️_Risk_Management.py", label="🛡️ Risk Management", icon="🛡️")

st.markdown("---")

# System information
with st.expander("ℹ️ System Information"):
    st.markdown("""
    **Platform**: Copilot Quant v2.0 - Bloomberg-Style Interface
    **Mode**: Paper Trading Only
    **Broker**: Interactive Brokers (Development)
    **Data Provider**: Mock Data / IBKR Integration
    **Theme**: Professional Dark (Financial Markets)

    **New in v2.0:**
    - Bloomberg Terminal-inspired dark theme
    - Chart-first dashboard layout
    - Dividend yield and calendar tracking
    - Enhanced professional metrics display
    - Improved typography and data density
    """)

# Footer
st.caption("Copilot Quant Platform © 2024 | Professional trading tools for internal use")
