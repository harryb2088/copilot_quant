"""
Trading Mode Toggle UI Component

Provides a safe UI component for switching between paper and live trading modes
with warnings, confirmations, and status display.
"""

import logging
from datetime import datetime

import streamlit as st

logger = logging.getLogger(__name__)


def render_trading_mode_toggle(session_key: str = "trading_mode", default_mode: str = "paper") -> tuple[str, bool]:
    """
    Render trading mode toggle with confirmation dialogs and warnings.

    Args:
        session_key: Session state key for storing mode
        default_mode: Default trading mode ("paper" or "live")

    Returns:
        Tuple of (current_mode, mode_changed)
    """
    # Initialize session state
    if session_key not in st.session_state:
        st.session_state[session_key] = default_mode
        st.session_state[f"{session_key}_history"] = [{"timestamp": datetime.now().isoformat(), "mode": default_mode}]

    current_mode = st.session_state[session_key]
    mode_changed = False

    # Display current mode banner
    if current_mode == "paper":
        st.success("✅ **PAPER TRADING MODE** - No real money at risk", icon="📝")
    else:
        st.error("⚠️ **LIVE TRADING MODE** - Real money is at risk!", icon="🔴")

    st.markdown("---")

    # Mode selection with radio buttons
    st.markdown("### Trading Mode Selection")

    col1, col2 = st.columns([1, 2])

    with col1:
        new_mode = st.radio(
            "Select Trading Mode:",
            options=["paper", "live"],
            index=0 if current_mode == "paper" else 1,
            format_func=lambda x: "📝 Paper Trading (Simulated)" if x == "paper" else "🔴 Live Trading (Real Money)",
            key=f"{session_key}_radio",
        )

    with col2:
        if new_mode == "paper":
            st.info("""
            **Paper Trading Mode:**
            - ✅ No real money at risk
            - ✅ Safe for testing strategies
            - ✅ Uses simulated account
            - ✅ Real market data
            - Port: 7497 (TWS) / 4002 (Gateway)
            """)
        else:
            st.warning("""
            **Live Trading Mode:**
            - ⚠️ Real money is at risk
            - ⚠️ Only use after thorough testing
            - ⚠️ Requires live account credentials
            - ⚠️ All trades are executed for real
            - Port: 7496 (TWS) / 4001 (Gateway)
            """)

    # Handle mode change with confirmation
    if new_mode != current_mode:
        st.markdown("---")

        if new_mode == "live":
            # Switching to LIVE - require strong confirmation
            st.error("""
            ### ⚠️ WARNING: Switching to LIVE Trading Mode ⚠️

            You are about to switch to **LIVE TRADING MODE** where real money is at risk.

            **Before proceeding:**
            - [ ] I have thoroughly tested my strategies in paper trading
            - [ ] I understand that all orders will use real money
            - [ ] I have reviewed my risk management settings
            - [ ] I am prepared for potential financial losses
            - [ ] I have configured my live trading credentials correctly
            """)

            # Two-step confirmation for live mode
            confirm1 = st.checkbox(
                "I understand that live trading involves real money and real risk", key=f"{session_key}_confirm1"
            )

            confirm2 = st.checkbox(
                "I have tested my strategies and am ready to trade with real money", key=f"{session_key}_confirm2"
            )

            col1, col2 = st.columns(2)

            with col1:
                if st.button(
                    "🔴 Switch to LIVE Trading",
                    type="primary",
                    disabled=not (confirm1 and confirm2),
                    use_container_width=True,
                    key=f"{session_key}_confirm_btn",
                ):
                    # Log the mode switch
                    logger.warning(f"⚠️ TRADING MODE SWITCHED: PAPER → LIVE at {datetime.now().isoformat()}")

                    # Update session state
                    st.session_state[session_key] = "live"
                    st.session_state[f"{session_key}_history"].append(
                        {"timestamp": datetime.now().isoformat(), "mode": "live", "confirmed": True}
                    )
                    mode_changed = True

                    st.success("✅ Switched to LIVE trading mode")
                    st.rerun()

            with col2:
                if st.button("Cancel", use_container_width=True, key=f"{session_key}_cancel_btn"):
                    st.info("Mode change cancelled - staying in PAPER trading mode")
                    st.rerun()

        else:
            # Switching to PAPER - simple confirmation
            st.info("""
            ### Switching to Paper Trading Mode

            You are about to switch to **PAPER TRADING MODE** (simulated trading).
            This is the safe mode for testing strategies without real money.
            """)

            col1, col2 = st.columns(2)

            with col1:
                if st.button(
                    "📝 Switch to PAPER Trading",
                    type="primary",
                    use_container_width=True,
                    key=f"{session_key}_paper_btn",
                ):
                    # Log the mode switch
                    logger.info(f"Trading mode switched: LIVE → PAPER at {datetime.now().isoformat()}")

                    # Update session state
                    st.session_state[session_key] = "paper"
                    st.session_state[f"{session_key}_history"].append(
                        {"timestamp": datetime.now().isoformat(), "mode": "paper"}
                    )
                    mode_changed = True

                    st.success("✅ Switched to PAPER trading mode")
                    st.rerun()

            with col2:
                if st.button("Cancel", use_container_width=True, key=f"{session_key}_paper_cancel_btn"):
                    st.info("Mode change cancelled - staying in LIVE trading mode")
                    st.rerun()

    return st.session_state[session_key], mode_changed


def render_mode_status_banner(session_key: str = "trading_mode") -> None:
    """
    Render a compact status banner showing current trading mode.

    Args:
        session_key: Session state key for trading mode
    """
    if session_key not in st.session_state:
        st.session_state[session_key] = "paper"

    current_mode = st.session_state[session_key]

    if current_mode == "paper":
        st.info("📝 **Mode:** Paper Trading (Simulated)", icon="ℹ️")
    else:
        st.error("🔴 **Mode:** LIVE Trading (Real Money)", icon="⚠️")


def get_mode_history(session_key: str = "trading_mode") -> list[dict]:
    """
    Get history of mode changes.

    Args:
        session_key: Session state key for trading mode

    Returns:
        List of mode change events
    """
    history_key = f"{session_key}_history"
    return st.session_state.get(history_key, [])


def render_mode_history(session_key: str = "trading_mode") -> None:
    """
    Render mode change history for audit trail.

    Args:
        session_key: Session state key for trading mode
    """
    history = get_mode_history(session_key)

    if len(history) > 0:
        st.markdown("### Mode Change History")

        for _i, event in enumerate(reversed(history)):
            timestamp = event.get("timestamp", "Unknown")
            mode = event.get("mode", "Unknown")
            confirmed = event.get("confirmed", False)

            mode_icon = "📝" if mode == "paper" else "🔴"
            confirm_text = " (Confirmed)" if confirmed else ""

            st.text(f"{mode_icon} {timestamp}: {mode.upper()}{confirm_text}")
