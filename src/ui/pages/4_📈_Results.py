"""
Results Page - View backtest results and performance metrics
"""

import streamlit as st
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from components.sidebar import render_sidebar
from components.charts import plot_equity_curve, plot_drawdown, plot_monthly_returns_heatmap, plot_price_with_signals
from components.tables import render_trade_log, render_trades_pnl_table
from utils.session import init_session_state
from utils.mock_data import generate_mock_backtest_results, generate_mock_trades, generate_mock_backtests, generate_price_data_with_signals, generate_trades_pnl_table

# Page configuration
st.set_page_config(
    page_title="Results - Copilot Quant",
    page_icon="📈",
    layout="wide"
)

# Initialize session state
init_session_state()

# Render sidebar
render_sidebar()

# Main content
st.title("📈 Backtest Results")
st.markdown("---")

# Backtest selector
backtests = generate_mock_backtests()
completed_backtests = [bt for bt in backtests if bt['status'] == 'Completed']

if completed_backtests:
    backtest_options = [f"{bt['id']} - {bt['strategy']} ({bt['date_range']})" 
                        for bt in completed_backtests]
    
    selected_backtest = st.selectbox(
        "Select Backtest to View",
        backtest_options,
        help="Choose a completed backtest to view results"
    )
    
    st.markdown("---")
    
    # Generate mock results
    equity_data, metrics = generate_mock_backtest_results()
    
    # Performance metrics section
    st.markdown("### 📊 Performance Metrics")
    
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        st.metric(
            label="Total Return",
            value=metrics['total_return'],
            delta=metrics['total_return']
        )
    
    with col2:
        st.metric(
            label="Sharpe Ratio",
            value=metrics['sharpe_ratio'],
            delta="Good" if float(metrics['sharpe_ratio']) > 1.5 else "Fair"
        )
    
    with col3:
        st.metric(
            label="Max Drawdown",
            value=metrics['max_drawdown'],
            delta=metrics['max_drawdown'],
            delta_color="inverse"
        )
    
    with col4:
        st.metric(
            label="Win Rate",
            value=metrics['win_rate'],
            delta="Profitable"
        )
    
    with col5:
        st.metric(
            label="Total Trades",
            value=metrics['total_trades'],
            delta=f"{metrics['total_trades']} executed"
        )
    
    # Additional metrics in expander
    with st.expander("📊 Additional Metrics"):
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Average Trade", metrics['avg_trade'])
            st.metric("Profit Factor", metrics['profit_factor'])
        
        with col2:
            st.metric("Best Trade", "$1,245.50")
            st.metric("Worst Trade", "-$892.30")
        
        with col3:
            st.metric("Avg Win", "$456.20")
            st.metric("Avg Loss", "-$234.10")
    
    st.markdown("---")
    
    # Charts section
    st.markdown("### 📈 Performance Charts")
    
    tab1, tab2, tab3, tab4 = st.tabs(["Equity Curve", "Drawdown", "Monthly Returns", "Trade Signals"])
    
    with tab1:
        st.plotly_chart(plot_equity_curve(equity_data), use_container_width=True)
        
        st.markdown("""
        The equity curve shows the growth of your portfolio over time. A smooth, 
        upward-trending curve indicates consistent performance.
        """)
    
    with tab2:
        st.plotly_chart(plot_drawdown(equity_data), use_container_width=True)
        
        st.markdown("""
        Drawdown measures the decline from a historical peak. Lower drawdowns 
        indicate better risk management and more stable returns.
        """)
    
    with tab3:
        st.plotly_chart(plot_monthly_returns_heatmap(equity_data), use_container_width=True)
        
        st.markdown("""
        Monthly returns heatmap shows the distribution of returns across different 
        months and years, helping identify seasonal patterns.
        """)
    
    with tab4:
        # Generate price data with signals
        price_data, signals_data = generate_price_data_with_signals()
        st.plotly_chart(plot_price_with_signals(price_data, signals_data), use_container_width=True)
        
        st.markdown("""
        This chart shows the share price over time with buy (green ▲) and sell (red ▼) 
        signals marked at their execution points. These signals represent entry and exit 
        points identified by the trading strategy during the backtest period.
        """)
    
    st.markdown("---")
    
    # Trade P&L Summary section
    st.markdown("### 💰 Trade P&L Summary")
    
    col1, col2 = st.columns([3, 1])
    
    with col1:
        st.markdown("Profit & Loss breakdown for each completed trade (matched buy/sell pairs).")
    
    with col2:
        if st.button("📥 Download P&L Report", type="secondary", use_container_width=True):
            st.success("✅ Download started!")
            st.info("P&L report download functionality coming soon. Will export to CSV format.")
    
    # Generate and display trade P&L table
    trades_pnl_df = generate_trades_pnl_table()
    render_trades_pnl_table(trades_pnl_df)
    
    st.markdown("---")
    
    # Trade log section
    st.markdown("### 📝 Trade Log")
    
    col1, col2 = st.columns([3, 1])
    
    with col1:
        st.markdown("Detailed list of all trades executed during the backtest period.")
    
    with col2:
        if st.button("📥 Download Trade Log", type="secondary", use_container_width=True):
            st.success("✅ Download started!")
            st.info("Trade log download functionality coming soon. Will export to CSV format.")
    
    # Generate and display trade log
    trades_df = generate_mock_trades()
    render_trade_log(trades_df)
    
    st.markdown("---")
    
    # Risk metrics section
    st.markdown("### ⚠️ Risk Analysis")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        with st.container(border=True):
            st.markdown("**Volatility**")
            st.metric("Annual Volatility", "18.5%")
            st.caption("Measure of return variability")
    
    with col2:
        with st.container(border=True):
            st.markdown("**Value at Risk (VaR)**")
            st.metric("95% VaR", "-$2,450")
            st.caption("Expected loss at 95% confidence")
    
    with col3:
        with st.container(border=True):
            st.markdown("**Beta**")
            st.metric("Market Beta", "0.85")
            st.caption("Correlation with market")
    
    st.markdown("---")
    
    # Action buttons
    st.markdown("### ⚡ Actions")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        if st.button("🔬 Run New Backtest", use_container_width=True):
            st.switch_page("pages/2_🔬_Backtests.py")
    
    with col2:
        if st.button("📊 Compare Strategies", use_container_width=True):
            st.info("Strategy comparison feature coming soon!")
    
    with col3:
        if st.button("🔴 Deploy to Paper Trading", use_container_width=True):
            st.switch_page("pages/4_🔴_Live_Trading.py")
    
    with col4:
        if st.button("📄 Generate Report", use_container_width=True):
            st.success("Report generation started!")
            st.info("PDF report functionality coming soon.")
    
    st.markdown("---")
    
    # Notes section
    with st.expander("📝 Add Notes"):
        notes = st.text_area(
            "Backtest Notes",
            placeholder="Add your observations, insights, or next steps here...",
            height=100
        )
        if st.button("💾 Save Notes"):
            st.success("Notes saved successfully!")

else:
    st.info("""
    No completed backtests available yet.
    
    **To view results:**
    1. Go to the Backtests page
    2. Configure and run a backtest
    3. Return here to view the results
    """)
    
    if st.button("🔬 Go to Backtests"):
        st.switch_page("pages/2_🔬_Backtests.py")

# Help section
with st.expander("ℹ️ Understanding Your Results"):
    st.markdown("""
    ### Key Performance Indicators
    
    **Total Return**
    - Overall profit/loss percentage
    - Higher is better, but consider risk-adjusted metrics too
    
    **Sharpe Ratio**
    - Risk-adjusted return metric
    - > 1.0 is good, > 2.0 is excellent
    - Measures excess return per unit of risk
    
    **Max Drawdown**
    - Largest peak-to-trough decline
    - Lower is better
    - Important for risk management
    
    **Win Rate**
    - Percentage of profitable trades
    - Not the only important metric
    - Should be balanced with profit factor
    
    **Profit Factor**
    - Gross profits / Gross losses
    - > 1.0 means profitable strategy
    - > 1.5 is good, > 2.0 is excellent
    
    ### Interpreting Results
    
    - Look for consistency across different market conditions
    - High returns with high drawdowns may indicate excessive risk
    - Sharpe ratio helps compare strategies with different risk profiles
    - Consider transaction costs and slippage in real trading
    """)

# Footer
st.caption("💡 Tip: Always validate results on out-of-sample data before deploying to live trading")
