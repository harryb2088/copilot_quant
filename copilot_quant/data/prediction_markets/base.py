"""
Base class for prediction market data providers.

Defines the interface that all prediction market providers must implement.
"""

import logging
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Dict, List, Optional, Union

import pandas as pd

logger = logging.getLogger(__name__)


class PredictionMarketProvider(ABC):
    """Abstract base class for prediction market data providers."""

    def __init__(self, name: str):
        """
        Initialize the prediction market provider.

        Args:
            name: Human-readable name of the provider
        """
        self.name = name
        logger.info(f"Initialized {self.name} provider")

    @abstractmethod
    def list_markets(self, limit: Optional[int] = None) -> pd.DataFrame:
        """
        List available markets/contracts.

        Args:
            limit: Maximum number of markets to return (None for all)

        Returns:
            DataFrame with columns:
                - market_id: Unique identifier
                - title: Market title/question
                - category: Market category
                - close_time: Market close/resolution time
                - status: Market status (active, resolved, etc.)
                - volume: Trading volume (if available)
        """
        pass

    @abstractmethod
    def get_market_data(
        self,
        market_id: str,
        start_date: Optional[Union[str, datetime]] = None,
        end_date: Optional[Union[str, datetime]] = None,
    ) -> pd.DataFrame:
        """
        Get historical price/probability data for a specific market.

        Args:
            market_id: Market identifier
            start_date: Start date for historical data
            end_date: End date for historical data

        Returns:
            DataFrame with columns:
                - timestamp: Time of observation
                - price: Price or probability (0-1 or 0-100)
                - volume: Trading volume (if available)
                - shares_yes: Shares for "yes" outcome (if applicable)
                - shares_no: Shares for "no" outcome (if applicable)
        """
        pass

    @abstractmethod
    def get_market_details(self, market_id: str) -> Dict:
        """
        Get detailed information about a specific market.

        Args:
            market_id: Market identifier

        Returns:
            Dictionary with market details including:
                - market_id
                - title
                - description
                - category
                - outcomes (possible outcomes)
                - volume
                - liquidity (if available)
                - creator (if available)
                - resolution_criteria
                - close_time
                - resolution_time
        """
        pass

    def normalize_market_name(self, market_title: str) -> str:
        """
        Normalize market title for consistent naming.

        Args:
            market_title: Original market title

        Returns:
            Normalized title (lowercase, alphanumeric, underscores)
        """
        import re
        # Convert to lowercase
        normalized = market_title.lower()
        # Replace non-alphanumeric with underscores
        normalized = re.sub(r'[^a-z0-9]+', '_', normalized)
        # Remove leading/trailing underscores
        normalized = normalized.strip('_')
        # Limit length
        if len(normalized) > 100:
            normalized = normalized[:100]
        return normalized

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(name='{self.name}')"
