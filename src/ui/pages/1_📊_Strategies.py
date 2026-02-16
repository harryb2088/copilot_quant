"""
Strategies Page - View and manage trading strategies
"""

import streamlit as st
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from components.sidebar import render_sidebar
from components.tables import render_strategy_cards
from utils.session import init_session_state
from utils.mock_data import generate_mock_strategies

# Page configuration
st.set_page_config(
    page_title="Strategies - Copilot Quant",
    page_icon="📊",
    layout="wide"
)

# Initialize session state
init_session_state()

# Render sidebar
render_sidebar()

# Main content
st.title("📊 Trading Strategies")
st.markdown("---")

# Header section with actions
col1, col2 = st.columns([3, 1])

with col1:
    st.markdown("""
    Manage your trading strategies, create new ones, and monitor their performance.
    """)

with col2:
    if st.button("➕ Create New Strategy", type="primary", use_container_width=True):
        st.success("✅ Create Strategy feature coming soon!")
        st.info("This will open the strategy builder interface where you can define your trading logic.")

st.markdown("---")

# Filter and search section
col1, col2, col3 = st.columns([2, 1, 1])

with col1:
    search_query = st.text_input("🔍 Search strategies", placeholder="Enter strategy name or type...")

with col2:
    status_filter = st.selectbox("Status", ["All", "Active", "Draft", "Inactive"])

with col3:
    type_filter = st.selectbox("Type", ["All", "Mean Reversion", "Momentum", "Statistical Arbitrage", "Volatility"])

st.markdown("---")

# Get mock strategies
strategies = generate_mock_strategies()

# Apply filters
if status_filter != "All":
    strategies = [s for s in strategies if s['status'] == status_filter]

if type_filter != "All":
    strategies = [s for s in strategies if s['type'] == type_filter]

if search_query:
    strategies = [s for s in strategies if search_query.lower() in s['name'].lower() or 
                  search_query.lower() in s['type'].lower()]

# Display strategies count
st.markdown(f"### Showing {len(strategies)} strategies")

# Display strategies as cards
if strategies:
    render_strategy_cards(strategies)
else:
    st.info("No strategies match your filters. Try adjusting the filters or create a new strategy.")

st.markdown("---")

# Strategy templates section
st.markdown("### 📚 Strategy Templates")

st.markdown("""
Get started quickly with pre-built strategy templates. Each template can be customized to fit your needs.
""")

template_col1, template_col2, template_col3 = st.columns(3)

with template_col1:
    with st.container(border=True):
        st.markdown("**🔄 Mean Reversion**")
        st.caption("Buy oversold assets, sell overbought")
        if st.button("Use Template", key="template_mr", use_container_width=True):
            st.info("Mean Reversion template selected!")

with template_col2:
    with st.container(border=True):
        st.markdown("**📈 Trend Following**")
        st.caption("Ride momentum and follow trends")
        if st.button("Use Template", key="template_tf", use_container_width=True):
            st.info("Trend Following template selected!")

with template_col3:
    with st.container(border=True):
        st.markdown("**⚖️ Pairs Trading**")
        st.caption("Statistical arbitrage on correlated assets")
        if st.button("Use Template", key="template_pt", use_container_width=True):
            st.info("Pairs Trading template selected!")

st.markdown("---")

# Help section
with st.expander("ℹ️ About Trading Strategies"):
    st.markdown("""
    ### What is a Trading Strategy?
    
    A trading strategy is a set of rules that define when to buy and sell assets. Strategies can be based on:
    
    - **Technical Indicators**: Moving averages, RSI, MACD, etc.
    - **Statistical Models**: Mean reversion, cointegration, etc.
    - **Machine Learning**: Predictive models and pattern recognition
    - **Fundamental Data**: Earnings, valuations, economic indicators
    
    ### Strategy Components
    
    1. **Entry Rules**: When to open a position
    2. **Exit Rules**: When to close a position
    3. **Position Sizing**: How much capital to allocate
    4. **Risk Management**: Stop-loss and take-profit levels
    
    ### Best Practices
    
    - Always backtest before deploying
    - Use proper risk management
    - Monitor performance regularly
    - Keep strategies simple and robust
    - Avoid over-optimization (curve fitting)
    """)

# Footer
st.caption("💡 Tip: Click 'Run' on any strategy to create a new backtest")
