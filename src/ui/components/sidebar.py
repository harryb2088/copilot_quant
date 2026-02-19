"""Shared sidebar component"""

import streamlit as st


def render_sidebar():
    """Render the application sidebar with branding and footer"""

    with st.sidebar:
        # App logo/title
        st.title("🚀 Copilot Quant")
        st.markdown("### Platform")

        st.divider()

        # Navigation info (Streamlit handles this automatically with pages/)
        st.markdown("**Navigation**")
        st.caption("Use the sidebar menu to navigate between pages")

        st.divider()

        # Footer section
        st.markdown("---")

        # Current mode indicator
        st.markdown("**Current Mode:**")
        st.success("📝 Paper Trading")

        # Version
        st.caption("Version: v0.1.0-alpha")
        st.caption("© 2024 Copilot Quant")


def render_connection_status():
    """Render broker connection status in sidebar"""
    with st.sidebar:
        st.markdown("---")
        st.markdown("**Connection Status**")

        if st.session_state.get("broker_connected", False):
            st.success("🟢 Connected")
        else:
            st.error("🔴 Disconnected")
