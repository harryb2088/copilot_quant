"""
Bloomberg-Style Portfolio Dashboard - Professional & Concise
Chart-first design with dividend information prominently displayed
"""

import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# Import custom components and utilities
from components.charts import plot_portfolio_performance_chart, plot_dividend_history
from utils.dividend_data import (
    get_dividend_info, 
    get_dividend_history, 
    get_portfolio_dividend_summary,
    get_next_dividend_calendar
)

# ============================================================================
# PAGE CONFIG
# ============================================================================
st.set_page_config(
    page_title="Portfolio Dashboard | Bloomberg Style",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================================================================
# CUSTOM CSS - Professional Dark Theme
# ============================================================================
st.markdown("""
<style>
    /* Main container styling */
    .main .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
        max-width: 100%;
    }
    
    /* Metric styling - Bold and prominent */
    [data-testid="stMetricValue"] {
        font-size: 2rem;
        font-weight: 700;
        color: #FAFAFA;
    }
    
    [data-testid="stMetricLabel"] {
        font-size: 0.95rem;
        font-weight: 600;
        color: #9CA3AF;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }
    
    [data-testid="stMetricDelta"] {
        font-size: 1rem;
        font-weight: 600;
    }
    
    /* Typography improvements */
    h1 {
        font-weight: 700;
        font-size: 2.5rem;
        color: #FAFAFA;
        margin-bottom: 0.5rem;
    }
    
    h2 {
        font-weight: 600;
        font-size: 1.5rem;
        color: #E5E7EB;
        margin-top: 2rem;
        margin-bottom: 1rem;
        border-bottom: 2px solid #3498DB;
        padding-bottom: 0.5rem;
    }
    
    h3 {
        font-weight: 600;
        font-size: 1.2rem;
        color: #D1D5DB;
        margin-top: 1.5rem;
    }
    
    /* Table styling */
    .dataframe {
        font-size: 0.9rem;
    }
    
    .dataframe thead th {
        background-color: #1E2127 !important;
        color: #9CA3AF !important;
        font-weight: 600 !important;
        text-transform: uppercase;
        font-size: 0.85rem;
        letter-spacing: 0.05em;
    }
    
    .dataframe tbody tr:hover {
        background-color: #2E3440 !important;
    }
    
    /* Card/Container styling */
    div[data-testid="stVerticalBlock"] > div {
        background-color: #1E2127;
        padding: 1rem;
        border-radius: 8px;
    }
    
    /* Expander styling */
    .streamlit-expanderHeader {
        font-weight: 600;
        font-size: 0.95rem;
        color: #9CA3AF;
    }
</style>
""", unsafe_allow_html=True)

# ============================================================================
# MOCK DATA SETUP
# ============================================================================

# Portfolio positions
positions_data = pd.DataFrame({
    'Symbol': ['AAPL', 'GOOGL', 'MSFT', 'AMZN', 'NVDA', 'META', 'TSLA', 'JPM'],
    'Quantity': [500, 200, 350, 150, 250, 180, 100, 400],
    'Current Price': [182.30, 141.80, 375.50, 151.20, 502.40, 365.20, 238.50, 155.80]
})

# Calculate position values and add dividend info
positions_data['Market Value'] = positions_data['Quantity'] * positions_data['Current Price']
positions_data['Dividend Yield'] = positions_data['Symbol'].apply(
    lambda x: get_dividend_info(x)['dividend_yield']
)

# Mock portfolio performance data
np.random.seed(42)
dates = pd.date_range(end=datetime.now(), periods=252, freq='D')
cumulative_returns = np.cumsum(np.random.normal(0.0008, 0.012, 252))
portfolio_values = 1000000 * (1 + cumulative_returns)

# Portfolio summary metrics
total_value = positions_data['Market Value'].sum()
cash_balance = 45280.00
total_assets = total_value + cash_balance
initial_investment = 900000
total_return = total_assets - initial_investment
total_return_pct = (total_return / initial_investment) * 100

# Dividend summary
div_summary = get_portfolio_dividend_summary(positions_data)

# Risk metrics (mock)
sharpe_ratio = 1.82
max_drawdown = -8.5
beta = 1.05
volatility = 15.2

# ============================================================================
# DASHBOARD HEADER
# ============================================================================

st.title("📊 Portfolio Dashboard")
st.markdown(f"**Last Updated:** {datetime.now().strftime('%B %d, %Y at %I:%M %p')}")

# ============================================================================
# MAIN CHART - Portfolio Performance (Top Priority)
# ============================================================================

st.markdown("---")
fig = plot_portfolio_performance_chart(dates, portfolio_values, title="Portfolio Value Over Time")
st.plotly_chart(fig, use_container_width=True)

# ============================================================================
# KEY METRICS SNAPSHOT - 6 Columns
# ============================================================================

st.markdown("## Key Metrics Snapshot")

col1, col2, col3, col4, col5, col6 = st.columns(6)

with col1:
    st.metric(
        label="Portfolio Value",
        value=f"${total_assets:,.0f}",
        delta=f"+${total_return:,.0f}"
    )

with col2:
    st.metric(
        label="Total Return",
        value=f"{total_return_pct:.2f}%",
        delta="YTD"
    )

with col3:
    st.metric(
        label="Cash",
        value=f"${cash_balance:,.0f}",
        delta=f"{(cash_balance/total_assets)*100:.1f}%"
    )

with col4:
    st.metric(
        label="Dividend Yield",
        value=f"{div_summary['portfolio_yield']*100:.2f}%",
        delta="Annual"
    )

with col5:
    st.metric(
        label="Annual Dividend",
        value=f"${div_summary['total_annual_income']:,.0f}",
        delta=f"${div_summary['monthly_income']:,.0f}/mo"
    )

with col6:
    st.metric(
        label="Sharpe Ratio",
        value=f"{sharpe_ratio:.2f}",
        delta="1Y"
    )

# ============================================================================
# DIVIDEND INFORMATION SECTION
# ============================================================================

st.markdown("## 💰 Dividend Information")

div_col1, div_col2 = st.columns([1.5, 1])

with div_col1:
    st.markdown("### Upcoming Dividend Calendar")
    
    # Get next dividend payments
    dividend_calendar = get_next_dividend_calendar(positions_data, days_ahead=90)
    
    if not dividend_calendar.empty:
        # Format the calendar for display
        dividend_calendar['Ex-Date'] = pd.to_datetime(dividend_calendar['ex_date']).dt.strftime('%Y-%m-%d')
        dividend_calendar['Payment'] = dividend_calendar['total_payment'].apply(lambda x: f"${x:,.2f}")
        dividend_calendar['Symbol'] = dividend_calendar['symbol'].str.upper()
        
        display_calendar = dividend_calendar[['Symbol', 'Ex-Date', 'Payment']].copy()
        display_calendar = display_calendar.sort_values('Ex-Date')
        
        st.dataframe(
            display_calendar,
            hide_index=True,
            use_container_width=True,
            height=250
        )
    else:
        st.info("No upcoming dividends in the next 90 days")

with div_col2:
    st.markdown("### Dividend Summary")
    
    # Summary metrics table
    div_metrics = pd.DataFrame({
        'Metric': [
            'Annual Income',
            'Quarterly Income',
            'Monthly Income',
            'Portfolio Yield',
            'Div Growth (Est.)'
        ],
        'Value': [
            f"${div_summary['total_annual_income']:,.2f}",
            f"${div_summary['quarterly_income']:,.2f}",
            f"${div_summary['monthly_income']:,.2f}",
            f"{div_summary['portfolio_yield']*100:.2f}%",
            "+8.5%"
        ]
    })
    
    st.dataframe(div_metrics, hide_index=True, use_container_width=True)
    
    # Mini dividend history chart for MSFT
    st.markdown("#### MSFT Dividend History")
    msft_div_history = get_dividend_history('MSFT', years=2)
    if not msft_div_history.empty:
        fig_div = plot_dividend_history(msft_div_history, symbol="MSFT")
        st.plotly_chart(fig_div, use_container_width=True)

# ============================================================================
# CURRENT POSITIONS TABLE
# ============================================================================

st.markdown("## 📈 Current Positions")

# Format positions table for display
positions_display = positions_data.copy()
positions_display['Current Price'] = positions_display['Current Price'].apply(lambda x: f"${x:,.2f}")
positions_display['Market Value'] = positions_display['Market Value'].apply(lambda x: f"${x:,.0f}")
positions_display['Dividend Yield'] = positions_display['Dividend Yield'].apply(lambda x: f"{x*100:.2f}%")
positions_display['Weight'] = ((positions_data['Market Value'] / total_value) * 100).apply(lambda x: f"{x:.1f}%")

st.dataframe(
    positions_display,
    hide_index=True,
    use_container_width=True,
    height=350
)

# Position summary stats
col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("Total Positions", len(positions_data))
with col2:
    st.metric("Largest Position", f"{(positions_data['Market Value'].max() / total_value * 100):.1f}%")
with col3:
    st.metric("Smallest Position", f"{(positions_data['Market Value'].min() / total_value * 100):.1f}%")
with col4:
    st.metric("Avg Position Size", f"${(total_value / len(positions_data)):,.0f}")

# ============================================================================
# RISK & PERFORMANCE ANALYTICS
# ============================================================================

st.markdown("## ⚠️ Risk & Performance Analytics")

risk_col1, risk_col2, risk_col3 = st.columns(3)

with risk_col1:
    st.markdown("### Risk Metrics")
    risk_metrics = pd.DataFrame({
        'Metric': ['Volatility (1Y)', 'Beta', 'Max Drawdown', 'VaR (95%)'],
        'Value': [f'{volatility:.1f}%', f'{beta:.2f}', f'{max_drawdown:.1f}%', '-2.8%']
    })
    st.dataframe(risk_metrics, hide_index=True, use_container_width=True)

with risk_col2:
    st.markdown("### Performance Metrics")
    perf_metrics = pd.DataFrame({
        'Metric': ['Sharpe Ratio', 'Sortino Ratio', 'Alpha', 'Calmar Ratio'],
        'Value': [f'{sharpe_ratio:.2f}', '2.15', '+3.2%', '1.95']
    })
    st.dataframe(perf_metrics, hide_index=True, use_container_width=True)

with risk_col3:
    st.markdown("### Time Period Returns")
    period_returns = pd.DataFrame({
        'Period': ['1 Day', '1 Week', '1 Month', '3 Months', '1 Year', 'YTD'],
        'Return': ['+0.8%', '+2.3%', '+5.1%', '+12.4%', '+24.8%', '+16.2%']
    })
    st.dataframe(period_returns, hide_index=True, use_container_width=True)

# ============================================================================
# RECENT TRADE ACTIVITY
# ============================================================================

st.markdown("## 🔄 Recent Trade Activity")

# Mock recent trades
recent_trades = pd.DataFrame({
    'Date': pd.date_range(end=datetime.now(), periods=5, freq='D').strftime('%Y-%m-%d'),
    'Symbol': ['NVDA', 'MSFT', 'AAPL', 'JPM', 'META'],
    'Action': ['BUY', 'SELL', 'BUY', 'BUY', 'SELL'],
    'Quantity': [50, 25, 100, 80, 30],
    'Price': [498.20, 378.50, 180.25, 154.80, 368.90],
    'Total': [24910.00, 9462.50, 18025.00, 12384.00, 11067.00]
})

recent_trades['Price'] = recent_trades['Price'].apply(lambda x: f"${x:.2f}")
recent_trades['Total'] = recent_trades['Total'].apply(lambda x: f"${x:,.2f}")

st.dataframe(recent_trades, hide_index=True, use_container_width=True)

# Trade statistics
trade_col1, trade_col2, trade_col3, trade_col4 = st.columns(4)

with trade_col1:
    st.metric("Trades (30D)", "28")
with trade_col2:
    st.metric("Avg Trade Size", "$15,420")
with trade_col3:
    st.metric("Win Rate", "64.3%")
with trade_col4:
    st.metric("Total Commissions", "$142.50")

# ============================================================================
# FOOTER - About This Dashboard
# ============================================================================

st.markdown("---")

with st.expander("ℹ️ About This Dashboard"):
    st.markdown("""
    ### Bloomberg-Style Portfolio Dashboard
    
    **Design Philosophy:**
    - **Chart-First**: Primary focus on visual portfolio performance at the top
    - **Data-Dense**: Maximum information in minimal space
    - **Professional Aesthetics**: Dark theme inspired by Bloomberg Terminal
    - **Dividend-Focused**: Prominent display of income generation metrics
    
    **Key Features:**
    - Real-time portfolio valuation and performance tracking
    - Comprehensive dividend income analysis and calendar
    - Risk-adjusted performance metrics (Sharpe, Sortino, etc.)
    - Position-level insights with dividend yields
    - Recent trading activity and statistics
    
    **Data Sources:**
    - Portfolio positions and valuations (mock data for demonstration)
    - Dividend information via `dividend_data` utility
    - Performance charts via `charts` component library
    
    **Technology Stack:**
    - Streamlit for interactive UI
    - Plotly for professional charting
    - Pandas for data manipulation
    - Custom Bloomberg-inspired dark theme
    
    *This dashboard provides a concise, professional view of your portfolio with emphasis on performance 
    visualization and dividend income tracking.*
    """)

st.markdown("---")
st.markdown(
    "<div style='text-align: center; color: #6B7280; font-size: 0.85rem;'>"
    "Portfolio Dashboard v2.0 | Data updates in real-time | Professional Analytics Platform"
    "</div>",
    unsafe_allow_html=True
)
