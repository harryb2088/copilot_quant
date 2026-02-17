"""
Polymarket data fetcher.

Fetches market data from Polymarket using their public API.
API Documentation: https://docs.polymarket.com/
"""

import logging
from datetime import datetime
from typing import Dict, Optional, Union

import pandas as pd
import requests

from copilot_quant.data.prediction_markets.base import PredictionMarketProvider

logger = logging.getLogger(__name__)


class PolymarketProvider(PredictionMarketProvider):
    """Polymarket data provider."""

    def __init__(self):
        """Initialize Polymarket provider."""
        super().__init__("Polymarket")
        self.base_url = "https://clob.polymarket.com"
        self.gamma_url = "https://gamma-api.polymarket.com"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'copilot_quant/1.0.0',
            'Accept': 'application/json'
        })

    def list_markets(self, limit: Optional[int] = None) -> pd.DataFrame:
        """
        List available markets on Polymarket.

        Args:
            limit: Maximum number of markets to return

        Returns:
            DataFrame with market information
        """
        try:
            # Use the markets endpoint
            url = f"{self.gamma_url}/markets"
            params = {}
            if limit:
                params['limit'] = limit
            else:
                params['limit'] = 100  # Default limit

            response = self.session.get(url, params=params, timeout=30)
            response.raise_for_status()
            data = response.json()

            markets = []
            for market in data:
                markets.append({
                    'market_id': market.get('condition_id', ''),
                    'title': market.get('question', ''),
                    'category': market.get('category', ''),
                    'close_time': market.get('end_date_iso', ''),
                    'status': 'active' if market.get('active', False) else 'closed',
                    'volume': float(market.get('volume', 0)),
                    'liquidity': float(market.get('liquidity', 0)),
                })

            df = pd.DataFrame(markets)
            if not df.empty and 'close_time' in df.columns:
                df['close_time'] = pd.to_datetime(df['close_time'], errors='coerce')
            
            logger.info(f"Retrieved {len(df)} markets from Polymarket")
            return df

        except requests.RequestException as e:
            logger.error(f"Failed to fetch Polymarket markets: {e}")
            return pd.DataFrame()
        except Exception as e:
            logger.error(f"Unexpected error fetching Polymarket markets: {e}")
            return pd.DataFrame()

    def get_market_data(
        self,
        market_id: str,
        start_date: Optional[Union[str, datetime]] = None,
        end_date: Optional[Union[str, datetime]] = None,
    ) -> pd.DataFrame:
        """
        Get historical price data for a Polymarket market.

        Args:
            market_id: Market condition_id
            start_date: Start date for data
            end_date: End date for data

        Returns:
            DataFrame with historical prices
        """
        try:
            # Polymarket uses token_id for price history
            # First, get market details to find token_id
            market_details = self.get_market_details(market_id)
            if not market_details or 'tokens' not in market_details:
                logger.warning(f"Could not find token info for market {market_id}")
                return pd.DataFrame()

            # Get price history for the first token (usually "Yes")
            tokens = market_details['tokens']
            if not tokens:
                return pd.DataFrame()

            token_id = tokens[0].get('token_id', '')
            if not token_id:
                return pd.DataFrame()

            # Note: Polymarket's public API may have limited historical data
            # This is a simplified implementation
            url = f"{self.gamma_url}/prices"
            params = {
                'market': market_id,
                'interval': 'max'  # Get all available data
            }

            response = self.session.get(url, params=params, timeout=30)
            response.raise_for_status()
            data = response.json()

            # Parse the response into a DataFrame
            prices = []
            if isinstance(data, list):
                for point in data:
                    prices.append({
                        'timestamp': point.get('t', ''),
                        'price': float(point.get('p', 0)),
                        'volume': float(point.get('v', 0)),
                    })

            df = pd.DataFrame(prices)
            if not df.empty:
                df['timestamp'] = pd.to_datetime(df['timestamp'], unit='s', errors='coerce')
                df = df.set_index('timestamp').sort_index()

                # Filter by date range if provided
                if start_date:
                    if isinstance(start_date, str):
                        start_date = pd.to_datetime(start_date)
                    df = df[df.index >= start_date]
                if end_date:
                    if isinstance(end_date, str):
                        end_date = pd.to_datetime(end_date)
                    df = df[df.index <= end_date]

            logger.info(f"Retrieved {len(df)} data points for market {market_id}")
            return df

        except requests.RequestException as e:
            logger.error(f"Failed to fetch Polymarket market data: {e}")
            return pd.DataFrame()
        except Exception as e:
            logger.error(f"Unexpected error fetching Polymarket market data: {e}")
            return pd.DataFrame()

    def get_market_details(self, market_id: str) -> Dict:
        """
        Get detailed information about a Polymarket market.

        Args:
            market_id: Market condition_id

        Returns:
            Dictionary with market details
        """
        try:
            url = f"{self.gamma_url}/markets/{market_id}"
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            data = response.json()

            return {
                'market_id': data.get('condition_id', ''),
                'title': data.get('question', ''),
                'description': data.get('description', ''),
                'category': data.get('category', ''),
                'outcomes': data.get('outcomes', []),
                'tokens': data.get('tokens', []),
                'volume': float(data.get('volume', 0)),
                'liquidity': float(data.get('liquidity', 0)),
                'close_time': data.get('end_date_iso', ''),
                'resolution_time': data.get('closed', ''),
                'active': data.get('active', False),
            }

        except requests.RequestException as e:
            logger.error(f"Failed to fetch Polymarket market details: {e}")
            return {}
        except Exception as e:
            logger.error(f"Unexpected error fetching Polymarket market details: {e}")
            return {}
