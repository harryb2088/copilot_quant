"""
API Authentication Module

Provides API key-based authentication for REST API endpoints.
"""

import logging
import secrets
from datetime import datetime, timedelta
from typing import Optional

from fastapi import HTTPException, Security, status
from fastapi.security import APIKeyHeader

logger = logging.getLogger(__name__)

# API Key header
API_KEY_NAME = "X-API-Key"
api_key_header = APIKeyHeader(name=API_KEY_NAME, auto_error=False)


class APIKeyManager:
    """
    Manage API keys for authentication.

    In production, this should be replaced with a database-backed solution.
    For now, it uses environment variables or in-memory storage.
    """

    def __init__(self):
        """Initialize API key manager"""
        self._api_keys = {}
        logger.info("APIKeyManager initialized")

    def generate_key(self, name: str, expiry_days: Optional[int] = None) -> str:
        """
        Generate a new API key.

        Args:
            name: Human-readable name for the key
            expiry_days: Optional expiry in days

        Returns:
            Generated API key
        """
        api_key = secrets.token_urlsafe(32)

        expiry = None
        if expiry_days:
            expiry = datetime.now() + timedelta(days=expiry_days)

        self._api_keys[api_key] = {"name": name, "created": datetime.now(), "expiry": expiry, "last_used": None}

        logger.info(f"Generated API key for '{name}'")
        return api_key

    def validate_key(self, api_key: str) -> bool:
        """
        Validate an API key.

        Args:
            api_key: API key to validate

        Returns:
            True if valid, False otherwise
        """
        if api_key not in self._api_keys:
            return False

        key_info = self._api_keys[api_key]

        # Check expiry
        if key_info["expiry"] and datetime.now() > key_info["expiry"]:
            logger.warning(f"Expired API key used: {key_info['name']}")
            return False

        # Update last used
        key_info["last_used"] = datetime.now()

        return True

    def revoke_key(self, api_key: str) -> bool:
        """
        Revoke an API key.

        Args:
            api_key: API key to revoke

        Returns:
            True if revoked, False if not found
        """
        if api_key in self._api_keys:
            name = self._api_keys[api_key]["name"]
            del self._api_keys[api_key]
            logger.info(f"Revoked API key for '{name}'")
            return True
        return False

    def list_keys(self) -> list:
        """List all API keys with metadata"""
        return [
            {
                "name": info["name"],
                "created": info["created"].isoformat(),
                "expiry": info["expiry"].isoformat() if info["expiry"] else None,
                "last_used": info["last_used"].isoformat() if info["last_used"] else None,
            }
            for info in self._api_keys.values()
        ]


# Global instance
_key_manager = APIKeyManager()


def get_api_key_manager() -> APIKeyManager:
    """Get the global API key manager instance"""
    return _key_manager


async def verify_api_key(api_key: str = Security(api_key_header)) -> str:
    """
    Verify API key from request header.

    This is a FastAPI dependency that can be used to protect endpoints.

    Args:
        api_key: API key from header

    Returns:
        Validated API key

    Raises:
        HTTPException: If API key is invalid
    """
    if not api_key:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="API key is missing")

    manager = get_api_key_manager()

    if not manager.validate_key(api_key):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid or expired API key")

    return api_key
