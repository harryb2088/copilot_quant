"""
Risk Management Page - Configure and monitor risk controls
"""

import sys
from datetime import datetime, timedelta
from pathlib import Path

import pandas as pd
import streamlit as st

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from components.sidebar import render_sidebar
from utils.session import init_session_state

from risk.settings import RiskSettings

# Page configuration
st.set_page_config(page_title="Risk Management - Copilot Quant", page_icon="🛡️", layout="wide")

# Initialize session state
init_session_state()

# Initialize risk settings in session state if not present
if "risk_settings" not in st.session_state:
    st.session_state.risk_settings = RiskSettings.get_conservative_profile()

# Render sidebar
render_sidebar()

# Main content
st.title("🛡️ Risk Management")
st.markdown("---")

# Header with description
st.markdown("""
**Configure risk parameters to protect your capital and manage portfolio exposure.**

All settings are designed with conservative defaults that prioritize capital preservation.
Adjust parameters carefully based on your risk tolerance and trading strategy.
""")

st.markdown("---")

# Current Risk Status Dashboard
st.markdown("### 📊 Current Risk Status")

col1, col2, col3, col4 = st.columns(4)

with col1:
    # Mock current drawdown
    current_drawdown = 0.03  # 3%
    max_drawdown = st.session_state.risk_settings.max_portfolio_drawdown

    drawdown_pct = (current_drawdown / max_drawdown) * 100
    if drawdown_pct < 50:
        delta_color = "normal"
        status = "✅ Safe"
    elif drawdown_pct < 80:
        delta_color = "inverse"
        status = "⚠️ Warning"
    else:
        delta_color = "inverse"
        status = "🚨 Danger"

    st.metric(
        label="Portfolio Drawdown",
        value=f"{current_drawdown:.1%}",
        delta=f"Limit: {max_drawdown:.1%}",
        delta_color=delta_color,
    )
    st.caption(status)

with col2:
    # Mock cash position
    current_cash = 0.25  # 25%
    min_cash = st.session_state.risk_settings.min_cash_buffer

    if current_cash >= min_cash:
        status = "✅ Safe"
    else:
        status = "🚨 Below Min"

    st.metric(label="Cash Buffer", value=f"{current_cash:.1%}", delta=f"Min: {min_cash:.1%}")
    st.caption(status)

with col3:
    # Mock largest position
    largest_position = 0.08  # 8%
    max_position = st.session_state.risk_settings.max_position_size

    if largest_position <= max_position:
        status = "✅ Within Limit"
    else:
        status = "🚨 Exceeds Limit"

    st.metric(label="Largest Position", value=f"{largest_position:.1%}", delta=f"Max: {max_position:.1%}")
    st.caption(status)

with col4:
    # Mock number of positions
    num_positions = 5
    max_positions = st.session_state.risk_settings.max_positions

    if num_positions < max_positions:
        status = "✅ Available"
    else:
        status = "⚠️ At Limit"

    st.metric(label="Active Positions", value=num_positions, delta=f"Max: {max_positions}")
    st.caption(status)

st.markdown("---")

# Risk Settings Configuration
st.markdown("### ⚙️ Risk Settings")

# Preset profiles
st.markdown("#### 📋 Quick Profiles")
col1, col2, col3, col4 = st.columns(4)

with col1:
    if st.button("🛡️ Conservative", use_container_width=True, type="primary"):
        st.session_state.risk_settings = RiskSettings.get_conservative_profile()
        st.success("✅ Conservative profile loaded")
        st.rerun()

with col2:
    if st.button("⚖️ Balanced", use_container_width=True):
        st.session_state.risk_settings = RiskSettings.get_balanced_profile()
        st.success("✅ Balanced profile loaded")
        st.rerun()

with col3:
    if st.button("🚀 Aggressive", use_container_width=True):
        st.session_state.risk_settings = RiskSettings.get_aggressive_profile()
        st.success("✅ Aggressive profile loaded")
        st.rerun()

with col4:
    if st.button("🔄 Reset to Default", use_container_width=True):
        st.session_state.risk_settings = RiskSettings()
        st.success("✅ Reset to conservative defaults")
        st.rerun()

st.markdown("---")

# Detailed Settings
settings = st.session_state.risk_settings

# Portfolio-Level Controls
st.markdown("#### 📊 Portfolio-Level Controls")

col1, col2 = st.columns(2)

with col1:
    max_portfolio_drawdown = st.slider(
        "Maximum Portfolio Drawdown",
        min_value=0.05,
        max_value=0.30,
        value=settings.max_portfolio_drawdown,
        step=0.01,
        format="%.1f%%",
        help="Maximum allowed portfolio drawdown before halting new trades",
    )

    min_cash_buffer = st.slider(
        "Minimum Cash Buffer",
        min_value=0.0,
        max_value=0.50,
        value=settings.min_cash_buffer,
        step=0.01,
        format="%.1f%%",
        help="Minimum cash as percentage of portfolio",
    )

    enable_circuit_breaker = st.checkbox(
        "Enable Circuit Breaker",
        value=settings.enable_circuit_breaker,
        help="Automatically halt trading if drawdown threshold is reached",
    )

with col2:
    circuit_breaker_threshold = st.slider(
        "Circuit Breaker Threshold",
        min_value=0.05,
        max_value=max_portfolio_drawdown,
        value=min(settings.circuit_breaker_threshold, max_portfolio_drawdown),
        step=0.01,
        format="%.1f%%",
        help="Drawdown level that triggers circuit breaker (must be ≤ max drawdown)",
        disabled=not enable_circuit_breaker,
    )

    max_cash_buffer = st.slider(
        "Maximum Cash Buffer",
        min_value=min_cash_buffer,
        max_value=1.0,
        value=max(settings.max_cash_buffer, min_cash_buffer),
        step=0.01,
        format="%.1f%%",
        help="Maximum cash as percentage of portfolio",
    )

st.markdown("---")

# Position-Level Controls
st.markdown("#### 📈 Position-Level Controls")

col1, col2 = st.columns(2)

with col1:
    max_position_size = st.slider(
        "Maximum Position Size",
        min_value=0.01,
        max_value=0.30,
        value=settings.max_position_size,
        step=0.01,
        format="%.1f%%",
        help="Maximum size of any single position as % of portfolio",
    )

    position_stop_loss = st.slider(
        "Position Stop Loss",
        min_value=0.01,
        max_value=0.20,
        value=settings.position_stop_loss,
        step=0.01,
        format="%.1f%%",
        help="Automatic stop loss for individual positions",
    )

with col2:
    max_positions = st.number_input(
        "Maximum Concurrent Positions",
        min_value=1,
        max_value=50,
        value=settings.max_positions,
        step=1,
        help="Maximum number of positions to hold at once",
    )

    max_correlation = st.slider(
        "Maximum Position Correlation",
        min_value=0.50,
        max_value=0.95,
        value=settings.max_correlation,
        step=0.05,
        format="%.2f",
        help="Maximum correlation allowed between positions",
    )

st.markdown("---")

# Volatility Targeting
st.markdown("#### 📉 Volatility Targeting")

col1, col2 = st.columns(2)

with col1:
    enable_volatility_targeting = st.checkbox(
        "Enable Volatility Targeting",
        value=settings.enable_volatility_targeting,
        help="Automatically adjust position sizes based on volatility",
    )

with col2:
    target_portfolio_volatility = st.slider(
        "Target Portfolio Volatility",
        min_value=0.05,
        max_value=0.40,
        value=settings.target_portfolio_volatility,
        step=0.01,
        format="%.1f%%",
        help="Target annual portfolio volatility (standard deviation)",
        disabled=not enable_volatility_targeting,
    )

st.markdown("---")

# Save/Apply buttons
col1, col2, col3, col4 = st.columns(4)

with col1:
    if st.button("💾 Save Settings", type="primary", use_container_width=True):
        try:
            # Update settings with current values
            new_settings = RiskSettings(
                max_portfolio_drawdown=max_portfolio_drawdown,
                min_cash_buffer=min_cash_buffer,
                max_cash_buffer=max_cash_buffer,
                enable_circuit_breaker=enable_circuit_breaker,
                circuit_breaker_threshold=circuit_breaker_threshold,
                max_position_size=max_position_size,
                position_stop_loss=position_stop_loss,
                max_positions=max_positions,
                max_correlation=max_correlation,
                enable_volatility_targeting=enable_volatility_targeting,
                target_portfolio_volatility=target_portfolio_volatility,
            )

            # Save to session state
            st.session_state.risk_settings = new_settings

            # Save to file
            settings_dir = Path(__file__).parent.parent.parent / "data"
            settings_dir.mkdir(exist_ok=True)
            settings_file = settings_dir / "risk_settings.json"
            new_settings.save(settings_file)

            st.success(f"✅ Settings saved successfully to {settings_file}")
        except ValueError as e:
            st.error(f"❌ Invalid settings: {e}")

with col2:
    if st.button("📥 Load Saved Settings", use_container_width=True):
        try:
            settings_file = Path(__file__).parent.parent.parent / "data" / "risk_settings.json"
            if settings_file.exists():
                loaded_settings = RiskSettings.load(settings_file)
                st.session_state.risk_settings = loaded_settings
                st.success("✅ Settings loaded successfully")
                st.rerun()
            else:
                st.warning("⚠️ No saved settings file found")
        except Exception as e:
            st.error(f"❌ Error loading settings: {e}")

with col3:
    if st.button("📤 Export Settings", use_container_width=True):
        settings_json = st.session_state.risk_settings.to_dict()
        st.download_button(
            label="Download JSON", data=str(settings_json), file_name="risk_settings.json", mime="application/json"
        )

with col4:
    pass  # Reserved for future use

st.markdown("---")

# Risk Breach Log
st.markdown("### 📜 Risk Breach History")

st.markdown("""
Monitor historical risk breaches and circuit breaker activations.
This log helps you understand when and why risk limits were triggered.
""")

# Mock breach log data
breach_log_data = [
    {
        "Timestamp": datetime.now() - timedelta(days=5),
        "Type": "Position Stop Loss",
        "Symbol": "AAPL",
        "Value": "6.2%",
        "Limit": "5.0%",
        "Action": "Position Closed",
    },
    {
        "Timestamp": datetime.now() - timedelta(days=12),
        "Type": "Max Position Size",
        "Symbol": "TSLA",
        "Value": "11.5%",
        "Limit": "10.0%",
        "Action": "Trade Rejected",
    },
    {
        "Timestamp": datetime.now() - timedelta(days=28),
        "Type": "Min Cash Buffer",
        "Symbol": "Portfolio",
        "Value": "18.0%",
        "Limit": "20.0%",
        "Action": "Trade Rejected",
    },
]

if breach_log_data:
    df_breaches = pd.DataFrame(breach_log_data)
    st.dataframe(df_breaches, use_container_width=True, hide_index=True)
else:
    st.info("✅ No risk breaches recorded")

st.markdown("---")

# Educational Information
with st.expander("ℹ️ Understanding Risk Management"):
    st.markdown("""
    ### Why Risk Management Matters

    Risk management is the foundation of successful trading. Even the best strategy can
    fail without proper risk controls. These parameters help you:

    - **Preserve Capital**: Limit losses during drawdowns
    - **Manage Exposure**: Prevent over-concentration in single positions
    - **Control Volatility**: Keep portfolio volatility within acceptable ranges
    - **Prevent Disasters**: Circuit breaker stops trading during extreme conditions

    ### Key Parameters Explained

    **Portfolio Drawdown**: Maximum allowed decline from peak value. Conservative traders
    use 10-15%, aggressive traders might accept 20-25%.

    **Cash Buffer**: Maintains liquidity for opportunities and emergencies. Higher buffers
    reduce risk but may lower returns.

    **Position Size**: Prevents over-concentration. Rule of thumb: never risk more than
    5-10% on a single position.

    **Stop Loss**: Automatic exit when position moves against you. Protects from
    catastrophic losses.

    **Circuit Breaker**: Emergency stop when drawdown reaches critical levels. Prevents
    emotional decision-making during market stress.

    **Volatility Targeting**: Reduces position sizes when volatility is high, increases
    when low. Creates more stable returns.

    ### Best Practices

    1. Start with conservative settings
    2. Adjust gradually based on experience
    3. Review settings quarterly
    4. Backtest changes before applying
    5. Never disable circuit breaker in live trading
    6. Keep cash buffer at minimum 15-20%
    7. Monitor breach log regularly
    """)

# Profile Comparison
with st.expander("📊 Profile Comparison"):
    st.markdown("### Risk Profile Comparison")

    profiles_data = {
        "Parameter": [
            "Max Portfolio Drawdown",
            "Max Position Size",
            "Min Cash Buffer",
            "Position Stop Loss",
            "Max Positions",
            "Circuit Breaker Threshold",
            "Target Volatility",
        ],
        "Conservative": ["12%", "10%", "20%", "5%", "10", "10%", "15%"],
        "Balanced": ["15%", "15%", "15%", "7%", "15", "12%", "18%"],
        "Aggressive": ["20%", "20%", "10%", "10%", "20", "15%", "25%"],
    }

    df_profiles = pd.DataFrame(profiles_data)
    st.dataframe(df_profiles, use_container_width=True, hide_index=True)

    st.markdown("""
    **Choose a profile based on your:**
    - Risk tolerance
    - Trading experience
    - Portfolio size
    - Time horizon
    - Market conditions
    """)

# Footer
st.caption("🛡️ Risk Management - Protecting your capital is priority #1")
