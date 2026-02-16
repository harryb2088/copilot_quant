"""Session state management for Streamlit app"""
import streamlit as st


def init_session_state():
    """Initialize session state variables if they don't exist"""
    
    # Navigation state
    if 'current_page' not in st.session_state:
        st.session_state.current_page = 'Home'
    
    # Strategy selection
    if 'selected_strategy' not in st.session_state:
        st.session_state.selected_strategy = None
    
    # Backtest selection
    if 'selected_backtest' not in st.session_state:
        st.session_state.selected_backtest = None
    
    # Paper trading connection status
    if 'paper_trading_enabled' not in st.session_state:
        st.session_state.paper_trading_enabled = False
    
    if 'broker_connected' not in st.session_state:
        st.session_state.broker_connected = False
    
    # User preferences
    if 'theme_mode' not in st.session_state:
        st.session_state.theme_mode = 'light'
    
    if 'show_advanced_metrics' not in st.session_state:
        st.session_state.show_advanced_metrics = False


def get_session_value(key, default=None):
    """Get a value from session state with a default fallback"""
    return st.session_state.get(key, default)


def set_session_value(key, value):
    """Set a value in session state"""
    st.session_state[key] = value


def clear_session_state():
    """Clear all session state (useful for logout/reset)"""
    for key in list(st.session_state.keys()):
        del st.session_state[key]
    init_session_state()
