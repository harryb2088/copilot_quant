"""
Authentication utility for Copilot Quant Platform

This module provides authentication functionality using streamlit-authenticator.
Credentials are loaded from environment variables for security.
"""

import os
import streamlit as st
import streamlit_authenticator as stauth


def get_credentials():
    """
    Get authentication credentials from environment variables.
    
    Returns:
        dict: Credentials dictionary for streamlit-authenticator
    """
    auth_email = os.environ.get("AUTH_EMAIL", "")
    auth_name = os.environ.get("AUTH_NAME", "Demo User")
    auth_password = os.environ.get("AUTH_PASSWORD", "")
    
    if not auth_email or not auth_password:
        # If credentials are not set, return None to skip authentication
        # This allows the app to run without authentication in development
        return None
    
    # Hash the password using the new API
    hasher = stauth.Hasher()
    hashed_password = hasher.hash(auth_password)
    
    credentials = {
        'usernames': {
            auth_email: {
                'email': auth_email,
                'name': auth_name,
                'password': hashed_password
            }
        }
    }
    
    return credentials


def init_authentication():
    """
    Initialize authentication for the Streamlit app.
    
    Returns:
        tuple: (name, authentication_status, username) from authenticator.login()
               Returns (None, None, None) if authentication is disabled
    """
    credentials = get_credentials()
    
    # If no credentials are set, skip authentication (for development)
    if credentials is None:
        st.warning("⚠️ Authentication is disabled. Set AUTH_EMAIL and AUTH_PASSWORD environment variables to enable.")
        return None, None, None
    
    # Create authenticator
    authenticator = stauth.Authenticate(
        credentials,
        "copilot_quant_platform",
        "auth_cookie",
        cookie_expiry_days=1
    )
    
    # Display login form
    name, authentication_status, username = authenticator.login("Login", "main")
    
    # Check authentication status
    if authentication_status is False:
        st.error("Username/password is incorrect")
        st.stop()
    elif authentication_status is None:
        st.warning("Please enter your username and password")
        st.stop()
    
    # Add logout button in sidebar if authenticated
    if authentication_status:
        with st.sidebar:
            st.write(f"Welcome *{name}*")
            authenticator.logout("Logout", "sidebar")
    
    return name, authentication_status, username
