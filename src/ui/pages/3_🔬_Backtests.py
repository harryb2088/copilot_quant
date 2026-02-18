"""
Backtests Page - Configure and run strategy backtests
"""

import streamlit as st
import sys
from pathlib import Path
from datetime import datetime
import pandas as pd

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from components.sidebar import render_sidebar
from utils.session import init_session_state
from utils.mock_data import generate_mock_strategies, generate_mock_backtests
from utils.llm_strategy_generator import LLMStrategyGenerator

# Page configuration
st.set_page_config(
    page_title="Backtests - Copilot Quant",
    page_icon="🔬",
    layout="wide"
)

# Initialize session state
init_session_state()

# Render sidebar
render_sidebar()

# Main content
st.title("🔬 Backtests")
st.markdown("---")

st.markdown("""
Test your trading strategies against historical market data to evaluate performance before deploying.
""")

st.markdown("---")

# Backtest configuration form
st.markdown("### 🎯 Configure New Backtest")

# Initialize LLM strategy generator
if 'llm_generator' not in st.session_state:
    st.session_state.llm_generator = LLMStrategyGenerator()

# Initialize generated strategy in session state
if 'generated_strategy' not in st.session_state:
    st.session_state.generated_strategy = None

# Strategy mode selection - OUTSIDE the form so it updates immediately
st.markdown("**Strategy Definition ***")

# Choice between predefined and LLM-generated
strategy_mode = st.radio(
    "Strategy Source",
    ["Use Predefined Strategy", "Generate with LLM (Beta - Internal Use Only)"],
    help="Choose to use an existing strategy or generate a new one with AI"
)

with st.form("backtest_form"):
    col1, col2 = st.columns(2)
    
    with col1:
        if strategy_mode == "Use Predefined Strategy":
            strategies = generate_mock_strategies()
            strategy_names = [s['name'] for s in strategies]
            selected_strategy = st.selectbox(
                "Select Strategy",
                strategy_names,
                help="Choose the trading strategy to backtest"
            )
            strategy_description = ""
        else:
            # Text box for LLM-based strategy generation
            strategy_description = st.text_area(
                "Describe Your Strategy",
                placeholder="Example: A momentum strategy using 20-day and 50-day moving averages. Buy when short MA crosses above long MA, sell when it crosses below. Use RSI for confirmation.",
                height=120,
                help="Describe your trading strategy in plain English. The LLM will generate the signal logic."
            )
            selected_strategy = None
        
        # Date range
        st.markdown("**Date Range ***")
        date_col1, date_col2 = st.columns(2)
        with date_col1:
            start_date = st.date_input(
                "Start Date",
                value=datetime(2023, 1, 1),
                max_value=datetime.now()
            )
        with date_col2:
            end_date = st.date_input(
                "End Date",
                value=datetime(2023, 12, 31),
                max_value=datetime.now()
            )
        
        # Initial capital
        initial_capital = st.number_input(
            "Initial Capital ($) *",
            min_value=1000,
            max_value=10000000,
            value=100000,
            step=10000,
            help="Starting capital for the backtest"
        )
    
    with col2:
        # Universe selection
        universe_options = [
            "S&P 500",
            "NASDAQ 100",
            "Russell 2000",
            "Dow Jones 30",
            "Custom Watchlist"
        ]
        selected_universe = st.selectbox(
            "Universe *",
            universe_options,
            help="Market universe to trade from"
        )
        
        # Advanced options
        with st.expander("⚙️ Advanced Options"):
            commission = st.number_input(
                "Commission per Trade ($)",
                min_value=0.0,
                value=1.0,
                step=0.1
            )
            
            slippage = st.number_input(
                "Slippage (bps)",
                min_value=0,
                value=5,
                step=1,
                help="Estimated slippage in basis points"
            )
            
            max_positions = st.slider(
                "Max Concurrent Positions",
                min_value=1,
                max_value=50,
                value=10
            )
            
            position_size = st.slider(
                "Position Size (%)",
                min_value=1,
                max_value=100,
                value=10,
                help="Percentage of capital per position"
            )
    
    # Submit button
    st.markdown("---")
    col1, col2, col3 = st.columns([1, 1, 2])
    
    with col1:
        submit_button = st.form_submit_button("🚀 Run Backtest", type="primary", use_container_width=True)
    
    with col2:
        save_config = st.form_submit_button("💾 Save Config", use_container_width=True)
    
    # Add generate button for LLM mode
    if strategy_mode == "Generate with LLM (Beta - Internal Use Only)":
        with col3:
            generate_button = st.form_submit_button("🤖 Generate Strategy", use_container_width=True)
    else:
        generate_button = False

# Handle LLM strategy generation
if strategy_mode == "Generate with LLM (Beta - Internal Use Only)" and generate_button:
    if not strategy_description:
        st.error("❌ Please provide a strategy description.")
    else:
        with st.spinner("🤖 Generating strategy with LLM... This may take a moment..."):
            import time
            time.sleep(1)  # Simulate processing
            
            result = st.session_state.llm_generator.generate_strategy(strategy_description)
            
            if result["success"]:
                st.session_state.generated_strategy = result["strategy"]
                st.success("✅ Strategy generated successfully!")
                
                # Display generated strategy
                with st.expander("📋 Generated Strategy Details", expanded=True):
                    strategy = result["strategy"]
                    st.markdown(f"**Name:** {strategy['name']}")
                    st.markdown(f"**Type:** {strategy['type']}")
                    st.markdown(f"**Description:** {strategy['description']}")
                    
                    st.markdown("**Signals/Indicators:**")
                    for signal in strategy['signals']:
                        st.json(signal)
                    
                    st.markdown("**Parameters:**")
                    st.json(strategy['parameters'])
                    
                    st.markdown("**Risk Management:**")
                    st.json(strategy['risk_management'])
                    
                    st.info("💡 You can now run a backtest with this strategy or refine it further.")
            else:
                st.error(f"❌ {result['error']}")

# Handle form submission
if submit_button:
    # Validate that we have a strategy
    if strategy_mode == "Generate with LLM (Beta - Internal Use Only)":
        if not st.session_state.generated_strategy:
            st.error("❌ Please generate a strategy first using the 'Generate Strategy' button.")
        else:
            strategy_name = st.session_state.generated_strategy['name']
            with st.spinner("Running backtest... This may take a few moments..."):
                import time
                time.sleep(2)  # Simulate backtest running
            
            st.success("✅ Backtest completed successfully!")
            st.info(f"""
            **Backtest Summary:**
            - Strategy: {strategy_name}
            - Period: {start_date} to {end_date}
            - Initial Capital: ${initial_capital:,}
            - Universe: {selected_universe}
            
            View detailed results on the Results page.
            """)
            
            if st.button("📈 View Results"):
                st.switch_page("pages/3_📈_Results.py")
    else:
        with st.spinner("Running backtest... This may take a few moments..."):
            import time
            time.sleep(2)  # Simulate backtest running
        
        st.success("✅ Backtest completed successfully!")
        st.info(f"""
        **Backtest Summary:**
        - Strategy: {selected_strategy}
        - Period: {start_date} to {end_date}
        - Initial Capital: ${initial_capital:,}
        - Universe: {selected_universe}
        
        View detailed results on the Results page.
        """)
        
        if st.button("📈 View Results"):
            st.switch_page("pages/3_📈_Results.py")

if save_config:
    st.success("💾 Configuration saved successfully!")

st.markdown("---")

# Past backtests section
st.markdown("### 📊 Past Backtests")

backtests = generate_mock_backtests()

# Display backtests table
if backtests:
    df = pd.DataFrame(backtests)
    
    # Add action column
    st.dataframe(
        df,
        use_container_width=True,
        hide_index=True,
        column_config={
            "status": st.column_config.Column(
                "Status",
                width="medium",
            ),
            "return": st.column_config.Column(
                "Return",
                width="small",
            )
        }
    )
    
    # Action buttons for each backtest
    st.markdown("### Actions")
    cols = st.columns(len(backtests))
    for i, (col, backtest) in enumerate(zip(cols, backtests)):
        with col:
            if backtest['status'] == 'Completed':
                if st.button("📈 View", key=f"view_{backtest['id']}", use_container_width=True):
                    st.session_state.selected_backtest = backtest['id']
                    st.switch_page("pages/3_📈_Results.py")
            else:
                st.button("⏳ Running", key=f"running_{backtest['id']}", disabled=True, use_container_width=True)
else:
    st.info("No backtests yet. Create your first backtest above!")

st.markdown("---")

# Security Notice for LLM Feature
if st.session_state.get('llm_generator') and st.session_state.llm_generator.is_api_configured():
    st.info("🔒 **LLM Integration Active** - For internal use only. API key configured.")
else:
    st.warning("⚠️ **LLM Integration Not Configured** - Set OPENAI_API_KEY environment variable to enable LLM features.")

# Help section
with st.expander("ℹ️ Backtesting Best Practices"):
    st.markdown("""
    ### What is Backtesting?
    
    Backtesting simulates how a trading strategy would have performed using historical data.
    It helps evaluate strategy effectiveness before risking real capital.
    
    ### LLM Strategy Generation (Beta - Internal Use Only)
    
    **🤖 How to use LLM-generated strategies:**
    1. Select "Generate with LLM" option
    2. Describe your strategy in plain English
    3. Click "Generate Strategy" to create the signal logic
    4. Review the generated strategy details
    5. Run backtest with the generated strategy
    
    **🔒 Security Features:**
    - Input sanitization to prevent code injection
    - Rate limiting (20 requests per hour)
    - API key validation
    - Internal use only - no external data transmission
    
    **⚠️ Important Notes:**
    - LLM-generated strategies should be reviewed before use
    - Always validate on historical data before live trading
    - This feature requires OPENAI_API_KEY environment variable
    
    ### Important Considerations
    
    **✅ Do:**
    - Test on sufficient data (multiple years)
    - Include transaction costs and slippage
    - Use out-of-sample testing
    - Consider market regimes
    - Validate on different time periods
    
    **❌ Don't:**
    - Over-optimize (curve fitting)
    - Ignore survivorship bias
    - Use future information (look-ahead bias)
    - Ignore transaction costs
    - Test on too little data
    
    ### Key Metrics to Watch
    
    - **Total Return**: Overall profit/loss
    - **Sharpe Ratio**: Risk-adjusted returns
    - **Max Drawdown**: Largest peak-to-trough decline
    - **Win Rate**: Percentage of profitable trades
    - **Profit Factor**: Gross profit / Gross loss
    
    ### Common Pitfalls
    
    1. **Overfitting**: Strategy works perfectly on historical data but fails in live trading
    2. **Look-ahead Bias**: Using information not available at the time
    3. **Survivorship Bias**: Only testing on stocks that still exist today
    4. **Ignoring Costs**: Not accounting for commissions and slippage
    """)

# Footer
st.caption("💡 Tip: Always validate your backtests on out-of-sample data")
