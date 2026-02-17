"""
Portfolio Dashboard - Institutional Portfolio Metrics and Analytics

This page provides comprehensive portfolio monitoring with key metrics including:
- Cash levels and allocation
- Returns (daily, monthly, annualized, cumulative)
- Exposure (gross/net, by asset class/strategy)
- Positions (holdings, market values, sector/asset/region breakdown)
- Trade summary and analysis
- Risk metrics (volatility, Sharpe, drawdown, VaR, beta)
- Liquidity metrics (turnover, cash-to-equity)
- PnL & Attribution (by asset, sector, strategy)
- Leverage tracking
"""

import sys
from pathlib import Path
from datetime import datetime, timedelta

import pandas as pd
import streamlit as st
import numpy as np

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from components.sidebar import render_sidebar
from components.charts import (
    plot_equity_curve,
    plot_drawdown
)
from utils.session import init_session_state

# Page configuration
st.set_page_config(
    page_title="Portfolio Dashboard - Copilot Quant",
    page_icon="📊",
    layout="wide"
)

# Initialize session state
init_session_state()

# Render sidebar
render_sidebar()

# Main content
st.title("📊 Institutional Portfolio Dashboard")
st.markdown("---")

st.markdown("""
**Comprehensive portfolio monitoring with institutional-grade metrics and analytics.**

This dashboard provides real-time insights into your portfolio's performance, risk, and exposure.
""")

st.markdown("---")

# ============================================================================
# SECTION 1: KEY PERFORMANCE INDICATORS
# ============================================================================
st.markdown("### 🎯 Key Performance Indicators")

col1, col2, col3, col4, col5, col6 = st.columns(6)

# Mock data for demonstration
portfolio_value = 1250000.00
initial_capital = 1000000.00
cash_balance = 312500.00
total_return = (portfolio_value - initial_capital) / initial_capital
sharpe_ratio = 1.85
max_drawdown = -0.087

with col1:
    st.metric(
        label="Portfolio Value",
        value=f"${portfolio_value:,.0f}",
        delta=f"+${portfolio_value - initial_capital:,.0f}"
    )

with col2:
    st.metric(
        label="Total Return",
        value=f"{total_return:.2%}",
        delta=f"+{total_return:.2%}"
    )

with col3:
    st.metric(
        label="Cash Balance",
        value=f"${cash_balance:,.0f}",
        delta=f"{cash_balance/portfolio_value:.1%} of portfolio"
    )

with col4:
    st.metric(
        label="Sharpe Ratio",
        value=f"{sharpe_ratio:.2f}",
        delta="Excellent" if sharpe_ratio > 1.5 else "Good"
    )

with col5:
    st.metric(
        label="Max Drawdown",
        value=f"{max_drawdown:.2%}",
        delta=f"{max_drawdown:.2%}",
        delta_color="inverse"
    )

with col6:
    net_exposure = 0.75
    st.metric(
        label="Net Exposure",
        value=f"{net_exposure:.1%}",
        delta="Within limits"
    )

st.markdown("---")

# ============================================================================
# SECTION 2: CASH & CAPITAL ALLOCATION
# ============================================================================
st.markdown("### 💵 Cash & Capital Allocation")

col1, col2 = st.columns([2, 1])

with col1:
    # Cash history chart
    st.markdown("#### Cash Balance History")
    
    # Generate mock cash history
    dates = pd.date_range(end=datetime.now(), periods=90, freq='D')
    np.random.seed(42)
    cash_history = 300000 + np.cumsum(np.random.normal(0, 5000, len(dates)))
    
    import plotly.graph_objects as go
    
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=dates,
        y=cash_history,
        mode='lines',
        name='Cash Balance',
        line=dict(color='#2ca02c', width=2),
        fill='tozeroy',
        fillcolor='rgba(44, 160, 44, 0.1)'
    ))
    
    fig.update_layout(
        xaxis_title='Date',
        yaxis_title='Cash Balance ($)',
        hovermode='x unified',
        template='plotly_white',
        height=300
    )
    
    st.plotly_chart(fig, use_container_width=True)

with col2:
    st.markdown("#### Capital Allocation")
    
    allocation = {
        'Cash': cash_balance,
        'Equities': 750000,
        'Fixed Income': 187500
    }
    
    allocation_df = pd.DataFrame({
        'Category': list(allocation.keys()),
        'Amount': list(allocation.values())
    })
    allocation_df['Percentage'] = (allocation_df['Amount'] / portfolio_value * 100).round(1)
    
    st.dataframe(
        allocation_df.style.format({
            'Amount': '${:,.0f}',
            'Percentage': '{:.1f}%'
        }),
        hide_index=True,
        use_container_width=True
    )
    
    # Pie chart
    fig_pie = go.Figure(data=[go.Pie(
        labels=allocation_df['Category'],
        values=allocation_df['Amount'],
        hole=0.4,
        marker=dict(colors=['#2ca02c', '#1f77b4', '#ff7f0e'])
    )])
    
    fig_pie.update_layout(
        height=250,
        showlegend=True,
        margin=dict(l=20, r=20, t=20, b=20)
    )
    
    st.plotly_chart(fig_pie, use_container_width=True)

st.markdown("---")

# ============================================================================
# SECTION 3: EXPOSURE & LEVERAGE
# ============================================================================
st.markdown("### 📈 Exposure & Leverage Analysis")

col1, col2, col3 = st.columns(3)

with col1:
    st.markdown("#### Exposure Metrics")
    
    gross_exposure = 0.95
    net_exposure = 0.75
    long_exposure = 0.85
    short_exposure = 0.10
    
    exposure_metrics = pd.DataFrame({
        'Metric': ['Gross Exposure', 'Net Exposure', 'Long Exposure', 'Short Exposure'],
        'Value': [gross_exposure, net_exposure, long_exposure, short_exposure],
        'Limit': [1.0, 1.0, 1.0, 0.3]
    })
    
    exposure_metrics['Status'] = exposure_metrics.apply(
        lambda x: '✅' if x['Value'] <= x['Limit'] else '⚠️',
        axis=1
    )
    
    st.dataframe(
        exposure_metrics.style.format({
            'Value': '{:.1%}',
            'Limit': '{:.1%}'
        }),
        hide_index=True,
        use_container_width=True
    )

with col2:
    st.markdown("#### Leverage Analysis")
    
    leverage_ratio = 1.15
    margin_used = 0.08
    
    st.metric("Leverage Ratio", f"{leverage_ratio:.2f}x", delta="Within limits")
    st.metric("Margin Used", f"{margin_used:.1%}", delta="Low")
    
    # Leverage history
    dates_lev = pd.date_range(end=datetime.now(), periods=30, freq='D')
    leverage_history = 1.0 + np.cumsum(np.random.normal(0, 0.01, len(dates_lev)))
    leverage_history = np.clip(leverage_history, 1.0, 1.5)
    
    fig_lev = go.Figure()
    fig_lev.add_trace(go.Scatter(
        x=dates_lev,
        y=leverage_history,
        mode='lines',
        name='Leverage',
        line=dict(color='#ff7f0e', width=2)
    ))
    
    fig_lev.add_hline(y=1.0, line_dash="dash", line_color="gray", opacity=0.5)
    
    fig_lev.update_layout(
        title='Leverage History (30 days)',
        xaxis_title='Date',
        yaxis_title='Leverage Ratio',
        template='plotly_white',
        height=200,
        margin=dict(l=20, r=20, t=40, b=20)
    )
    
    st.plotly_chart(fig_lev, use_container_width=True)

with col3:
    st.markdown("#### Exposure by Sector")
    
    sector_exposure = pd.DataFrame({
        'Sector': ['Technology', 'Healthcare', 'Financials', 'Consumer', 'Energy'],
        'Exposure': [0.35, 0.20, 0.15, 0.15, 0.10]
    })
    
    fig_sector = go.Figure(data=[go.Bar(
        x=sector_exposure['Sector'],
        y=sector_exposure['Exposure'],
        marker=dict(color='#1f77b4')
    )])
    
    fig_sector.update_layout(
        title='Sector Exposure',
        xaxis_title='Sector',
        yaxis_title='Exposure %',
        template='plotly_white',
        height=280,
        margin=dict(l=20, r=20, t=40, b=20)
    )
    
    st.plotly_chart(fig_sector, use_container_width=True)

st.markdown("---")

# ============================================================================
# SECTION 4: CURRENT POSITIONS
# ============================================================================
st.markdown("### 📋 Current Positions")

positions_data = pd.DataFrame({
    'Symbol': ['AAPL', 'GOOGL', 'MSFT', 'AMZN', 'NVDA', 'META', 'TSLA', 'JPM'],
    'Quantity': [500, 200, 350, 150, 250, 180, 100, 400],
    'Entry Price': [175.50, 138.20, 380.00, 145.80, 485.30, 358.90, 245.60, 152.30],
    'Current Price': [182.30, 141.80, 375.50, 151.20, 502.40, 365.20, 238.50, 155.80],
    'Market Value': [91150, 28360, 131425, 22680, 125600, 65736, 23850, 62320],
    'Unrealized P&L': [3400, 720, -1575, 810, 4275, 1134, -710, 1400],
    'Weight': [0.073, 0.023, 0.105, 0.018, 0.100, 0.053, 0.019, 0.050]
})

positions_data['P&L %'] = (positions_data['Unrealized P&L'] / 
                           (positions_data['Entry Price'] * positions_data['Quantity']) * 100)

col1, col2 = st.columns([3, 1])

with col1:
    st.dataframe(
        positions_data.style.format({
            'Entry Price': '${:.2f}',
            'Current Price': '${:.2f}',
            'Market Value': '${:,.0f}',
            'Unrealized P&L': '${:+,.0f}',
            'Weight': '{:.1%}',
            'P&L %': '{:+.2f}%'
        }).background_gradient(
            subset=['Unrealized P&L'],
            cmap='RdYlGn',
            vmin=-2000,
            vmax=5000
        ),
        hide_index=True,
        use_container_width=True,
        height=320
    )

with col2:
    st.markdown("#### Position Summary")
    
    total_positions = len(positions_data)
    total_market_value = positions_data['Market Value'].sum()
    total_unrealized_pnl = positions_data['Unrealized P&L'].sum()
    avg_position_size = total_market_value / total_positions
    
    st.metric("Total Positions", total_positions)
    st.metric("Market Value", f"${total_market_value:,.0f}")
    st.metric("Unrealized P&L", f"${total_unrealized_pnl:+,.0f}", 
             delta=f"{total_unrealized_pnl/total_market_value*100:+.2f}%")
    st.metric("Avg Position Size", f"${avg_position_size:,.0f}")

# Export button
if st.button("📥 Export Positions to CSV", key="export_positions"):
    csv = positions_data.to_csv(index=False)
    st.download_button(
        label="Download CSV",
        data=csv,
        file_name=f"positions_{datetime.now().strftime('%Y%m%d')}.csv",
        mime="text/csv"
    )

st.markdown("---")

# ============================================================================
# SECTION 5: RISK METRICS
# ============================================================================
st.markdown("### 🛡️ Risk Metrics")

col1, col2, col3 = st.columns(3)

with col1:
    st.markdown("#### Return & Risk Statistics")
    
    risk_metrics = pd.DataFrame({
        'Metric': [
            'Annualized Return',
            'Annualized Volatility',
            'Sharpe Ratio',
            'Sortino Ratio',
            'Calmar Ratio',
            'Max Drawdown',
            'Current Drawdown'
        ],
        'Value': ['25.0%', '18.5%', '1.85', '2.42', '2.87', '-8.7%', '-2.3%']
    })
    
    st.dataframe(risk_metrics, hide_index=True, use_container_width=True)

with col2:
    st.markdown("#### Advanced Risk Measures")
    
    advanced_metrics = pd.DataFrame({
        'Metric': [
            'Value at Risk (95%)',
            'Conditional VaR',
            'Beta to SPY',
            'Correlation to SPY',
            'Information Ratio',
            'Tracking Error',
            'Downside Deviation'
        ],
        'Value': ['-$23,500', '-$31,200', '1.12', '0.78', '0.85', '8.2%', '12.3%']
    })
    
    st.dataframe(advanced_metrics, hide_index=True, use_container_width=True)

with col3:
    st.markdown("#### Liquidity Metrics")
    
    liquidity_metrics = pd.DataFrame({
        'Metric': [
            'Portfolio Turnover',
            'Avg Holding Period',
            'Cash to Equity',
            'Avg Daily Volume',
            'Position Concentration',
            'Largest Position',
            'Top 5 Concentration'
        ],
        'Value': ['45%', '87 days', '25.0%', '$125K', '10.5%', 'MSFT', '40.5%']
    })
    
    st.dataframe(liquidity_metrics, hide_index=True, use_container_width=True)

st.markdown("---")

# ============================================================================
# SECTION 6: PERFORMANCE RETURNS
# ============================================================================
st.markdown("### 📊 Returns Analysis")

tab1, tab2, tab3 = st.tabs(["Cumulative Returns", "Monthly Returns", "Return Distribution"])

with tab1:
    # Generate cumulative returns
    dates_ret = pd.date_range(start='2023-01-01', end=datetime.now(), freq='D')
    np.random.seed(42)
    daily_returns = np.random.normal(0.0008, 0.015, len(dates_ret))
    cumulative_returns = (1 + pd.Series(daily_returns)).cumprod() - 1
    
    fig_cum = go.Figure()
    fig_cum.add_trace(go.Scatter(
        x=dates_ret,
        y=cumulative_returns * 100,
        mode='lines',
        name='Cumulative Return',
        line=dict(color='#1f77b4', width=2),
        fill='tozeroy',
        fillcolor='rgba(31, 119, 180, 0.1)'
    ))
    
    fig_cum.update_layout(
        title='Cumulative Returns',
        xaxis_title='Date',
        yaxis_title='Return (%)',
        hovermode='x unified',
        template='plotly_white',
        height=400
    )
    
    st.plotly_chart(fig_cum, use_container_width=True)

with tab2:
    # Monthly returns table
    st.markdown("#### Monthly Returns (%)")
    
    months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 
              'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
    years = ['2023', '2024']
    
    np.random.seed(42)
    monthly_returns = np.random.uniform(-3, 5, (len(years), len(months)))
    
    monthly_df = pd.DataFrame(monthly_returns, columns=months, index=years)
    
    st.dataframe(
        monthly_df.style.format('{:.2f}').background_gradient(
            cmap='RdYlGn',
            axis=None,
            vmin=-5,
            vmax=8
        ),
        use_container_width=True
    )

with tab3:
    # Return distribution histogram
    fig_hist = go.Figure()
    fig_hist.add_trace(go.Histogram(
        x=daily_returns * 100,
        nbinsx=50,
        name='Daily Returns',
        marker_color='#2ca02c'
    ))
    
    fig_hist.update_layout(
        title='Daily Returns Distribution',
        xaxis_title='Return (%)',
        yaxis_title='Frequency',
        template='plotly_white',
        height=400
    )
    
    st.plotly_chart(fig_hist, use_container_width=True)

st.markdown("---")

# ============================================================================
# SECTION 7: TRADE ACTIVITY
# ============================================================================
st.markdown("### 📝 Recent Trade Activity")

col1, col2 = st.columns([3, 1])

with col1:
    # Recent trades table
    recent_trades = pd.DataFrame({
        'Date': pd.date_range(end=datetime.now(), periods=10, freq='D')[::-1],
        'Symbol': ['AAPL', 'GOOGL', 'MSFT', 'NVDA', 'META', 'AMZN', 'TSLA', 'JPM', 'AAPL', 'GOOGL'],
        'Side': ['BUY', 'SELL', 'BUY', 'BUY', 'SELL', 'BUY', 'SELL', 'BUY', 'SELL', 'BUY'],
        'Quantity': [100, 50, 75, 50, 60, 40, 25, 100, 50, 30],
        'Price': [182.30, 141.80, 375.50, 502.40, 365.20, 151.20, 238.50, 155.80, 181.50, 140.90],
        'Commission': [5.00, 2.50, 3.75, 2.50, 3.00, 2.00, 1.25, 5.00, 2.50, 1.50]
    })
    
    recent_trades['Total'] = recent_trades['Quantity'] * recent_trades['Price']
    
    st.dataframe(
        recent_trades.style.format({
            'Date': lambda x: x.strftime('%Y-%m-%d'),
            'Price': '${:.2f}',
            'Commission': '${:.2f}',
            'Total': '${:,.2f}'
        }),
        hide_index=True,
        use_container_width=True,
        height=350
    )

with col2:
    st.markdown("#### Trade Statistics")
    
    st.metric("Total Trades (30d)", "47")
    st.metric("Avg Trade Size", "$28,450")
    st.metric("Total Commission", "$182.50")
    st.metric("Turnover Rate", "45%")

# Export button
if st.button("📥 Export Trades to CSV", key="export_trades"):
    csv = recent_trades.to_csv(index=False)
    st.download_button(
        label="Download CSV",
        data=csv,
        file_name=f"trades_{datetime.now().strftime('%Y%m%d')}.csv",
        mime="text/csv"
    )

st.markdown("---")

# ============================================================================
# SECTION 8: PNL ATTRIBUTION
# ============================================================================
st.markdown("### 💰 P&L Attribution")

col1, col2 = st.columns(2)

with col1:
    st.markdown("#### Attribution by Asset")
    
    attribution_data = pd.DataFrame({
        'Symbol': ['AAPL', 'NVDA', 'MSFT', 'META', 'JPM', 'AMZN', 'GOOGL', 'TSLA'],
        'P&L': [3400, 4275, -1575, 1134, 1400, 810, 720, -710],
        'Contribution': [0.34, 0.43, -0.16, 0.11, 0.14, 0.08, 0.07, -0.07]
    })
    
    attribution_data = attribution_data.sort_values('P&L', ascending=False)
    
    fig_attr = go.Figure()
    
    colors = ['#2ca02c' if x > 0 else '#d62728' for x in attribution_data['P&L']]
    
    fig_attr.add_trace(go.Bar(
        x=attribution_data['Symbol'],
        y=attribution_data['P&L'],
        marker=dict(color=colors),
        text=attribution_data['P&L'],
        texttemplate='$%{text:,.0f}',
        textposition='outside'
    ))
    
    fig_attr.update_layout(
        title='P&L by Asset',
        xaxis_title='Symbol',
        yaxis_title='P&L ($)',
        template='plotly_white',
        height=350
    )
    
    st.plotly_chart(fig_attr, use_container_width=True)

with col2:
    st.markdown("#### Attribution by Sector")
    
    sector_pnl = pd.DataFrame({
        'Sector': ['Technology', 'Financials', 'Healthcare', 'Consumer', 'Energy'],
        'P&L': [5850, 1400, 1200, 650, -300],
        'Contribution': [0.65, 0.16, 0.13, 0.07, -0.03]
    })
    
    sector_pnl = sector_pnl.sort_values('P&L', ascending=False)
    
    fig_sector_pnl = go.Figure()
    
    colors_sector = ['#2ca02c' if x > 0 else '#d62728' for x in sector_pnl['P&L']]
    
    fig_sector_pnl.add_trace(go.Bar(
        x=sector_pnl['Sector'],
        y=sector_pnl['P&L'],
        marker=dict(color=colors_sector),
        text=sector_pnl['P&L'],
        texttemplate='$%{text:,.0f}',
        textposition='outside'
    ))
    
    fig_sector_pnl.update_layout(
        title='P&L by Sector',
        xaxis_title='Sector',
        yaxis_title='P&L ($)',
        template='plotly_white',
        height=350
    )
    
    st.plotly_chart(fig_sector_pnl, use_container_width=True)

st.markdown("---")

# ============================================================================
# FOOTER
# ============================================================================
st.markdown("### ℹ️ Dashboard Information")

with st.expander("📖 About This Dashboard"):
    st.markdown("""
    This institutional portfolio dashboard provides comprehensive monitoring of your trading portfolio
    with metrics used by professional hedge funds and asset managers.
    
    **Key Features:**
    - **Real-time Monitoring**: Portfolio value, returns, and exposure tracking
    - **Risk Management**: Advanced risk metrics including VaR, Sharpe ratio, and drawdown analysis
    - **Position Analysis**: Detailed position tracking with sector and asset allocation
    - **Performance Attribution**: Understand which assets and sectors drive returns
    - **Trade Analytics**: Comprehensive trade log and execution analysis
    - **Export Capability**: Download positions and trades for further analysis
    
    **Metrics Explained:**
    - **Sharpe Ratio**: Risk-adjusted return measure (>1.5 is excellent)
    - **Max Drawdown**: Largest peak-to-trough decline in portfolio value
    - **Net Exposure**: Long exposure minus short exposure
    - **Leverage Ratio**: Total exposure divided by portfolio value
    - **VaR**: Maximum expected loss at 95% confidence level
    - **Turnover**: Percentage of portfolio traded over a period
    
    **Data Source**: This dashboard uses mock data for demonstration. In production, it will
    connect to live backtest results and trading data.
    """)

st.markdown("---")
st.caption("Portfolio Dashboard v1.0 | Data updated: " + datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
