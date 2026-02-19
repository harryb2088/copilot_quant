"""
Tests for authentication utility module
"""

import os
from unittest.mock import patch


class TestAuthCredentials:
    """Test authentication credentials handling"""

    def test_get_credentials_with_env_vars(self):
        """Test that credentials are properly generated from environment variables"""
        from src.ui.utils.auth import get_credentials

        with patch.dict(
            os.environ, {"AUTH_EMAIL": "test@example.com", "AUTH_PASSWORD": "testpass123", "AUTH_NAME": "Test User"}
        ):
            credentials = get_credentials()

            assert credentials is not None
            assert "usernames" in credentials
            assert "test@example.com" in credentials["usernames"]
            assert credentials["usernames"]["test@example.com"]["email"] == "test@example.com"
            assert credentials["usernames"]["test@example.com"]["name"] == "Test User"
            # Password should be hashed
            assert credentials["usernames"]["test@example.com"]["password"] != "testpass123"

    def test_get_credentials_without_env_vars(self):
        """Test that credentials return None when env vars are not set"""
        from src.ui.utils.auth import get_credentials

        with patch.dict(os.environ, {}, clear=True):
            credentials = get_credentials()
            assert credentials is None

    def test_get_credentials_with_partial_env_vars(self):
        """Test that credentials return None when only some env vars are set"""
        from src.ui.utils.auth import get_credentials

        # Only email, no password
        with patch.dict(os.environ, {"AUTH_EMAIL": "test@example.com"}, clear=True):
            credentials = get_credentials()
            assert credentials is None

        # Only password, no email
        with patch.dict(os.environ, {"AUTH_PASSWORD": "testpass123"}, clear=True):
            credentials = get_credentials()
            assert credentials is None

    def test_get_credentials_default_name(self):
        """Test that default name is used when AUTH_NAME is not set"""
        from src.ui.utils.auth import get_credentials

        with patch.dict(os.environ, {"AUTH_EMAIL": "test@example.com", "AUTH_PASSWORD": "testpass123"}, clear=True):
            credentials = get_credentials()

            assert credentials is not None
            assert credentials["usernames"]["test@example.com"]["name"] == "Demo User"


class TestAuthInitialization:
    """Test authentication initialization"""

    @patch("src.ui.utils.auth.st")
    def test_init_authentication_disabled(self, mock_st):
        """Test that authentication can be disabled when env vars are not set"""
        from src.ui.utils.auth import init_authentication

        with patch.dict(os.environ, {}, clear=True):
            with patch("src.ui.utils.auth.get_credentials", return_value=None):
                name, auth_status, username = init_authentication()

                assert name is None
                assert auth_status is None
                assert username is None
                # Should show warning when auth is disabled
                mock_st.warning.assert_called_once()
