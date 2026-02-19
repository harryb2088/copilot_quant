"""
IBKR Connection Panel Component

Displays IBKR connection status and provides connect/disconnect controls.
"""

import streamlit as st
import logging

logger = logging.getLogger(__name__)


def render_ibkr_connection_panel(
    service,
    trading_mode: str = "paper"
) -> None:
    """
    Render IBKR connection status panel with controls.
    
    Args:
        service: IBKRBrokerService instance
        trading_mode: Current trading mode ("paper" or "live")
    """
    st.markdown("### 🔌 IBKR Connection Status")
    
    # Get current connection status
    status = service.get_connection_status()
    is_connected = status['connected']
    state = status['state']
    accounts = status['accounts']
    uptime = status['uptime_seconds']
    last_error = status['last_error']
    
    # Display status in columns
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown("**Broker**")
        st.info("Interactive Brokers")
    
    with col2:
        st.markdown("**Status**")
        if is_connected:
            if state == "reconnecting":
                st.warning("🟡 Reconnecting...")
            else:
                st.success("🟢 Connected")
        else:
            if state == "connecting":
                st.warning("🟡 Connecting...")
            elif state == "failed":
                st.error("🔴 Failed")
            else:
                st.error("🔴 Disconnected")
    
    with col3:
        st.markdown("**Mode**")
        if trading_mode == "paper":
            st.success("📝 Paper Trading")
        else:
            st.error("🔴 LIVE Trading")
    
    with col4:
        st.markdown("**Uptime**")
        if is_connected and uptime is not None:
            hours = int(uptime // 3600)
            minutes = int((uptime % 3600) // 60)
            seconds = int(uptime % 60)
            st.info(f"⏱️ {hours:02d}:{minutes:02d}:{seconds:02d}")
        else:
            st.info("—")
    
    # Show account info if connected
    if is_connected and accounts:
        st.markdown(f"**Account(s):** {', '.join(accounts)}")
    
    # Show error if any
    if last_error:
        st.error(f"⚠️ {last_error}")
    
    st.markdown("---")
    
    # Connection controls
    st.markdown("### 🔒 Connection Controls")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Enable/disable toggle
        trading_enabled = st.toggle(
            f"Enable {'Paper' if trading_mode == 'paper' else 'Live'} Trading",
            value=st.session_state.get('ibkr_trading_enabled', False),
            help=f"Must be enabled to connect to {'paper' if trading_mode == 'paper' else 'live'} trading account",
            key="ibkr_trading_toggle"
        )
        
        if trading_enabled != st.session_state.get('ibkr_trading_enabled', False):
            st.session_state.ibkr_trading_enabled = trading_enabled
            if trading_enabled:
                st.success(f"✅ {'Paper' if trading_mode == 'paper' else 'Live'} trading enabled")
            else:
                st.warning(f"⚠️ {'Paper' if trading_mode == 'paper' else 'Live'} trading disabled")
                # Disconnect if currently connected
                if is_connected:
                    service.disconnect()
                    st.rerun()
    
    with col2:
        # Connect/Disconnect button
        if st.session_state.get('ibkr_trading_enabled', False):
            if not is_connected:
                btn_label = f"🔌 Connect to {'Paper' if trading_mode == 'paper' else 'Live'} Account"
                if st.button(btn_label, type="primary", use_container_width=True, key="ibkr_connect_btn"):
                    with st.spinner(f"Connecting to {'paper' if trading_mode == 'paper' else 'live'} trading account..."):
                        paper_trading = (trading_mode == "paper")
                        success = service.connect(paper_trading=paper_trading)
                        
                        if success:
                            st.success(f"✅ Connected to {'paper' if paper_trading else 'live'} trading account!")
                        else:
                            st.error(f"❌ Failed to connect: {service.last_error}")
                        
                        st.rerun()
            else:
                if st.button("🔌 Disconnect", type="secondary", use_container_width=True, key="ibkr_disconnect_btn"):
                    service.disconnect()
                    st.success("Disconnected from IBKR")
                    st.rerun()
        else:
            st.button(
                f"🔌 Connect to {'Paper' if trading_mode == 'paper' else 'Live'} Account",
                disabled=True,
                use_container_width=True,
                key="ibkr_connect_disabled_btn"
            )
            st.caption(f"Enable {'paper' if trading_mode == 'paper' else 'live'} trading first")
    
    # Warning for live trading
    if trading_mode == "live" and is_connected:
        st.error("""
        ⚠️ **LIVE TRADING MODE ACTIVE**
        
        You are connected to a LIVE trading account. All trades will use real money!
        - Double-check all orders before submission
        - Monitor your positions actively
        - Have stop losses in place
        - Never risk more than you can afford to lose
        """)
    
    st.markdown("---")


def render_connection_info_expander(service) -> None:
    """
    Render expandable section with detailed connection information.
    
    Args:
        service: IBKRBrokerService instance
    """
    with st.expander("ℹ️ Connection Information"):
        status = service.get_connection_status()
        
        st.markdown("**Connection Details:**")
        st.write(f"- State: `{status['state']}`")
        st.write(f"- Paper Trading: `{status['paper_trading']}`")
        st.write(f"- Using Gateway: `{status['use_gateway']}`")
        
        if status['connected']:
            st.write(f"- Uptime: `{status['uptime_seconds']:.0f} seconds`")
            if status['accounts']:
                st.write(f"- Accounts: `{', '.join(status['accounts'])}`")
        
        st.markdown("**Connection Ports:**")
        if status['paper_trading']:
            if status['use_gateway']:
                st.write("- IB Gateway Paper Trading: Port 4002")
            else:
                st.write("- TWS Paper Trading: Port 7497")
        else:
            if status['use_gateway']:
                st.write("- IB Gateway Live Trading: Port 4001")
            else:
                st.write("- TWS Live Trading: Port 7496")
        
        st.markdown("**Prerequisites:**")
        st.write("- TWS or IB Gateway must be running")
        st.write("- API access must be enabled in settings")
        st.write("- Socket clients must be enabled")
        st.write("- Correct port must be configured")
