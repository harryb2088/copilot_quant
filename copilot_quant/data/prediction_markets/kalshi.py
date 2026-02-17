"""
Kalshi data fetcher.

Fetches market data from Kalshi using their public API.
API Documentation: https://trading-api.readme.io/reference/getting-started
"""

import logging
from datetime import datetime
from typing import Dict, List, Optional, Union

import pandas as pd
import requests

from copilot_quant.data.prediction_markets.base import PredictionMarketProvider

logger = logging.getLogger(__name__)


class KalshiProvider(PredictionMarketProvider):
    """Kalshi data provider."""

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize Kalshi provider.

        Args:
            api_key: Optional API key for authenticated requests
        """
        super().__init__("Kalshi")
        self.base_url = "https://api.elections.kalshi.com/trade-api/v2"
        self.api_key = api_key
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'copilot_quant/1.0.0',
            'Accept': 'application/json'
        })
        if api_key:
            self.session.headers['Authorization'] = f'Bearer {api_key}'

    def list_markets(self, limit: Optional[int] = None) -> pd.DataFrame:
        """
        List available markets on Kalshi.

        Args:
            limit: Maximum number of markets to return

        Returns:
            DataFrame with market information
        """
        try:
            url = f"{self.base_url}/events"
            params = {
                'status': 'open',
                'limit': limit if limit else 100
            }

            response = self.session.get(url, params=params, timeout=30)
            response.raise_for_status()
            data = response.json()

            markets = []
            events = data.get('events', [])
            
            for event in events:
                # Each event can have multiple markets
                event_ticker = event.get('event_ticker', '')
                markets_data = event.get('markets', [])
                
                for market in markets_data:
                    markets.append({
                        'market_id': market.get('ticker', ''),
                        'title': market.get('title', ''),
                        'category': event.get('category', ''),
                        'close_time': market.get('close_time', ''),
                        'status': market.get('status', ''),
                        'volume': float(market.get('volume', 0)),
                        'liquidity': 0,  # Kalshi doesn't provide liquidity in listing
                    })

            df = pd.DataFrame(markets)
            if not df.empty and 'close_time' in df.columns:
                df['close_time'] = pd.to_datetime(df['close_time'], errors='coerce')
            
            logger.info(f"Retrieved {len(df)} markets from Kalshi")
            return df

        except requests.RequestException as e:
            logger.error(f"Failed to fetch Kalshi markets: {e}")
            return pd.DataFrame()
        except Exception as e:
            logger.error(f"Unexpected error fetching Kalshi markets: {e}")
            return pd.DataFrame()

    def get_market_data(
        self,
        market_id: str,
        start_date: Optional[Union[str, datetime]] = None,
        end_date: Optional[Union[str, datetime]] = None,
    ) -> pd.DataFrame:
        """
        Get historical price data for a Kalshi market.

        Args:
            market_id: Market ticker
            start_date: Start date for data
            end_date: End date for data

        Returns:
            DataFrame with historical prices
        """
        try:
            url = f"{self.base_url}/markets/{market_id}/history"
            params = {}
            
            if start_date:
                if isinstance(start_date, str):
                    params['start_time'] = start_date
                else:
                    params['start_time'] = start_date.isoformat()
            
            if end_date:
                if isinstance(end_date, str):
                    params['end_time'] = end_date
                else:
                    params['end_time'] = end_date.isoformat()

            response = self.session.get(url, params=params, timeout=30)
            response.raise_for_status()
            data = response.json()

            prices = []
            history = data.get('history', [])
            
            for point in history:
                prices.append({
                    'timestamp': point.get('ts', ''),
                    'price': float(point.get('yes_price', 0)) / 100,  # Convert cents to dollars
                    'volume': float(point.get('volume', 0)),
                })

            df = pd.DataFrame(prices)
            if not df.empty:
                df['timestamp'] = pd.to_datetime(df['timestamp'], errors='coerce')
                df = df.set_index('timestamp').sort_index()

            logger.info(f"Retrieved {len(df)} data points for market {market_id}")
            return df

        except requests.RequestException as e:
            logger.error(f"Failed to fetch Kalshi market data: {e}")
            return pd.DataFrame()
        except Exception as e:
            logger.error(f"Unexpected error fetching Kalshi market data: {e}")
            return pd.DataFrame()

    def get_market_details(self, market_id: str) -> Dict:
        """
        Get detailed information about a Kalshi market.

        Args:
            market_id: Market ticker

        Returns:
            Dictionary with market details
        """
        try:
            url = f"{self.base_url}/markets/{market_id}"
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            data = response.json()

            market = data.get('market', {})
            
            return {
                'market_id': market.get('ticker', ''),
                'title': market.get('title', ''),
                'description': market.get('subtitle', ''),
                'category': market.get('category', ''),
                'outcomes': ['Yes', 'No'],  # Kalshi markets are binary
                'volume': float(market.get('volume', 0)),
                'liquidity': float(market.get('liquidity', 0)),
                'close_time': market.get('close_time', ''),
                'resolution_time': market.get('expiration_time', ''),
                'status': market.get('status', ''),
                'yes_price': float(market.get('yes_bid', 0)) / 100,
                'no_price': float(market.get('no_bid', 0)) / 100,
            }

        except requests.RequestException as e:
            logger.error(f"Failed to fetch Kalshi market details: {e}")
            return {}
        except Exception as e:
            logger.error(f"Unexpected error fetching Kalshi market details: {e}")
            return {}
