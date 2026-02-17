"""
Prediction Market Data Providers

This module provides data fetchers for various prediction market platforms.
Supports fetching market data, odds/probabilities, and event information
for use in backtesting and live trading strategies.

Supported platforms:
- Polymarket: Decentralized prediction market platform
- Kalshi: CFTC-regulated prediction market exchange

Example Usage:
    # Fetch Polymarket data
    polymarket = PolymarketProvider()
    markets = polymarket.get_active_markets(category='crypto')
    
    # Fetch Kalshi data
    kalshi = KalshiProvider(api_key='your_key')
    markets = kalshi.get_active_markets()
"""

import logging
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Dict, List, Optional, Union
import time

import pandas as pd
import requests

logger = logging.getLogger(__name__)


class PredictionMarketProvider(ABC):
    """Abstract base class for prediction market data providers."""

    @abstractmethod
    def get_active_markets(
        self,
        category: Optional[str] = None,
        limit: Optional[int] = None
    ) -> pd.DataFrame:
        """
        Get currently active prediction markets.

        Args:
            category: Optional category filter (e.g., 'crypto', 'politics', 'sports')
            limit: Maximum number of markets to return

        Returns:
            DataFrame with market information including:
            - market_id: Unique market identifier
            - question: Market question/description
            - category: Market category
            - end_date: Market close date
            - volume: Trading volume
            - liquidity: Available liquidity
        """
        pass

    @abstractmethod
    def get_market_prices(
        self,
        market_id: str,
        start_date: Optional[Union[str, datetime]] = None,
        end_date: Optional[Union[str, datetime]] = None
    ) -> pd.DataFrame:
        """
        Get historical price/probability data for a market.

        Args:
            market_id: Market identifier
            start_date: Start date for historical data
            end_date: End date for historical data

        Returns:
            DataFrame with time-series price data including:
            - timestamp: Data timestamp
            - price: Current price/probability
            - volume: Trading volume
            - liquidity: Available liquidity
        """
        pass

    @abstractmethod
    def get_market_info(self, market_id: str) -> Dict:
        """
        Get detailed information about a specific market.

        Args:
            market_id: Market identifier

        Returns:
            Dictionary with market metadata
        """
        pass


class PolymarketProvider(PredictionMarketProvider):
    """
    Polymarket data provider for prediction market data.
    
    Polymarket is a decentralized prediction market platform built on Polygon.
    This provider fetches data from Polymarket's public API.
    
    Note: This is a basic implementation using publicly available endpoints.
    For production use, consider rate limiting and error handling enhancements.
    """

    def __init__(self, rate_limit_delay: float = 0.5):
        """
        Initialize Polymarket provider.
        
        Args:
            rate_limit_delay: Delay between API calls in seconds (default: 0.5)
        """
        self.base_url = "https://clob.polymarket.com"
        self.gamma_url = "https://gamma-api.polymarket.com"
        self.rate_limit_delay = rate_limit_delay
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'CopilotQuant/1.0',
            'Accept': 'application/json'
        })
        logger.info("Initialized Polymarket provider")

    def _make_request(self, url: str, params: Optional[Dict] = None) -> Dict:
        """
        Make HTTP request with error handling and rate limiting.
        
        Args:
            url: Request URL
            params: Query parameters
            
        Returns:
            JSON response as dictionary
        """
        try:
            time.sleep(self.rate_limit_delay)
            response = self.session.get(url, params=params, timeout=30)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Error making request to {url}: {e}")
            raise

    def get_active_markets(
        self,
        category: Optional[str] = None,
        limit: Optional[int] = 100
    ) -> pd.DataFrame:
        """
        Get currently active markets from Polymarket.
        
        Args:
            category: Optional category filter (e.g., 'crypto', 'politics', 'sports')
            limit: Maximum number of markets to return (default: 100)
            
        Returns:
            DataFrame with active market information
            
        Example:
            >>> provider = PolymarketProvider()
            >>> markets = provider.get_active_markets(category='crypto', limit=10)
            >>> print(markets[['question', 'end_date', 'volume']])
        """
        try:
            # Use Gamma API for markets list
            url = f"{self.gamma_url}/markets"
            params = {}
            
            if limit:
                params['limit'] = limit
                
            data = self._make_request(url, params)
            
            # Parse response into DataFrame
            markets = []
            
            # Handle both list and dict response formats
            market_list = data if isinstance(data, list) else data.get('markets', [])
            
            for market in market_list:
                # Apply category filter if specified
                if category and market.get('tags', []):
                    if category.lower() not in [tag.lower() for tag in market.get('tags', [])]:
                        continue
                
                markets.append({
                    'market_id': market.get('id') or market.get('condition_id', ''),
                    'question': market.get('question', ''),
                    'category': ', '.join(market.get('tags', [])),
                    'end_date': market.get('end_date_iso', ''),
                    'volume': float(market.get('volume', 0)),
                    'liquidity': float(market.get('liquidity', 0)),
                    'created_at': market.get('created_at', ''),
                    'active': market.get('active', True),
                })
            
            df = pd.DataFrame(markets)
            logger.info(f"Retrieved {len(df)} active markets from Polymarket")
            return df
            
        except Exception as e:
            logger.error(f"Error fetching active markets: {e}")
            return pd.DataFrame()

    def get_market_prices(
        self,
        market_id: str,
        start_date: Optional[Union[str, datetime]] = None,
        end_date: Optional[Union[str, datetime]] = None
    ) -> pd.DataFrame:
        """
        Get historical price data for a Polymarket market.
        
        Args:
            market_id: Polymarket market/condition ID
            start_date: Start date for historical data
            end_date: End date for historical data
            
        Returns:
            DataFrame with time-series price/probability data
            
        Example:
            >>> provider = PolymarketProvider()
            >>> prices = provider.get_market_prices('market_id_123')
            >>> print(prices[['timestamp', 'price', 'volume']])
        """
        try:
            # Note: This is a simplified implementation
            # Actual implementation would need to fetch order book or trade history
            url = f"{self.gamma_url}/markets/{market_id}"
            
            data = self._make_request(url)
            
            # For now, return current snapshot as single-row DataFrame
            # In production, you'd fetch historical trades/snapshots
            current_data = {
                'timestamp': [datetime.now().isoformat()],
                'market_id': [market_id],
                'price': [float(data.get('price', 0))],
                'volume': [float(data.get('volume', 0))],
                'liquidity': [float(data.get('liquidity', 0))],
            }
            
            df = pd.DataFrame(current_data)
            logger.info(f"Retrieved price data for market {market_id}")
            return df
            
        except Exception as e:
            logger.error(f"Error fetching market prices for {market_id}: {e}")
            return pd.DataFrame()

    def get_market_info(self, market_id: str) -> Dict:
        """
        Get detailed information about a Polymarket market.
        
        Args:
            market_id: Polymarket market/condition ID
            
        Returns:
            Dictionary with detailed market information
            
        Example:
            >>> provider = PolymarketProvider()
            >>> info = provider.get_market_info('market_id_123')
            >>> print(f"Question: {info['question']}")
        """
        try:
            url = f"{self.gamma_url}/markets/{market_id}"
            data = self._make_request(url)
            
            logger.info(f"Retrieved info for market {market_id}")
            return data
            
        except Exception as e:
            logger.error(f"Error fetching market info for {market_id}: {e}")
            return {}


class KalshiProvider(PredictionMarketProvider):
    """
    Kalshi data provider for prediction market data.
    
    Kalshi is a CFTC-regulated prediction market exchange.
    This provider fetches data from Kalshi's public API.
    
    Note: Some endpoints may require authentication. For read-only
    market data, authentication is typically not required.
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        api_secret: Optional[str] = None,
        rate_limit_delay: float = 0.5
    ):
        """
        Initialize Kalshi provider.
        
        Args:
            api_key: Optional API key for authenticated requests
            api_secret: Optional API secret for authenticated requests
            rate_limit_delay: Delay between API calls in seconds (default: 0.5)
        """
        self.base_url = "https://api.elections.kalshi.com/trade-api/v2"
        self.api_key = api_key
        self.api_secret = api_secret
        self.rate_limit_delay = rate_limit_delay
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'CopilotQuant/1.0',
            'Accept': 'application/json'
        })
        
        if api_key:
            self.session.headers.update({
                'Authorization': f'Bearer {api_key}'
            })
            
        logger.info("Initialized Kalshi provider")

    def _make_request(self, endpoint: str, params: Optional[Dict] = None) -> Dict:
        """
        Make HTTP request with error handling and rate limiting.
        
        Args:
            endpoint: API endpoint (relative to base_url)
            params: Query parameters
            
        Returns:
            JSON response as dictionary
        """
        try:
            time.sleep(self.rate_limit_delay)
            url = f"{self.base_url}/{endpoint}"
            response = self.session.get(url, params=params, timeout=30)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Error making request to {endpoint}: {e}")
            raise

    def get_active_markets(
        self,
        category: Optional[str] = None,
        limit: Optional[int] = 100
    ) -> pd.DataFrame:
        """
        Get currently active markets from Kalshi.
        
        Args:
            category: Optional category filter (e.g., 'economics', 'politics')
            limit: Maximum number of markets to return (default: 100)
            
        Returns:
            DataFrame with active market information
            
        Example:
            >>> provider = KalshiProvider()
            >>> markets = provider.get_active_markets(limit=10)
            >>> print(markets[['title', 'close_time', 'volume']])
        """
        try:
            params = {
                'status': 'open',
                'limit': limit or 100
            }
            
            if category:
                params['series_ticker'] = category
            
            data = self._make_request('markets', params)
            
            markets = []
            market_list = data.get('markets', [])
            
            for market in market_list:
                markets.append({
                    'market_id': market.get('ticker', ''),
                    'question': market.get('title', ''),
                    'category': market.get('category', ''),
                    'end_date': market.get('close_time', ''),
                    'volume': int(market.get('volume', 0)),
                    'liquidity': float(market.get('liquidity', 0)),
                    'yes_bid': float(market.get('yes_bid', 0)),
                    'yes_ask': float(market.get('yes_ask', 0)),
                    'no_bid': float(market.get('no_bid', 0)),
                    'no_ask': float(market.get('no_ask', 0)),
                })
            
            df = pd.DataFrame(markets)
            logger.info(f"Retrieved {len(df)} active markets from Kalshi")
            return df
            
        except Exception as e:
            logger.error(f"Error fetching active markets: {e}")
            return pd.DataFrame()

    def get_market_prices(
        self,
        market_id: str,
        start_date: Optional[Union[str, datetime]] = None,
        end_date: Optional[Union[str, datetime]] = None
    ) -> pd.DataFrame:
        """
        Get historical price data for a Kalshi market.
        
        Args:
            market_id: Kalshi market ticker
            start_date: Start date for historical data
            end_date: End date for historical data
            
        Returns:
            DataFrame with time-series price data
            
        Example:
            >>> provider = KalshiProvider()
            >>> prices = provider.get_market_prices('TICKER-123')
            >>> print(prices[['timestamp', 'yes_bid', 'yes_ask']])
        """
        try:
            endpoint = f"markets/{market_id}/history"
            params = {}
            
            if start_date:
                if isinstance(start_date, datetime):
                    start_date = start_date.isoformat()
                params['min_ts'] = start_date
                
            if end_date:
                if isinstance(end_date, datetime):
                    end_date = end_date.isoformat()
                params['max_ts'] = end_date
            
            data = self._make_request(endpoint, params)
            
            history = data.get('history', [])
            prices = []
            
            for snapshot in history:
                prices.append({
                    'timestamp': snapshot.get('ts', ''),
                    'market_id': market_id,
                    'yes_bid': float(snapshot.get('yes_bid', 0)),
                    'yes_ask': float(snapshot.get('yes_ask', 0)),
                    'no_bid': float(snapshot.get('no_bid', 0)),
                    'no_ask': float(snapshot.get('no_ask', 0)),
                    'volume': int(snapshot.get('volume', 0)),
                })
            
            df = pd.DataFrame(prices)
            logger.info(f"Retrieved {len(df)} price snapshots for market {market_id}")
            return df
            
        except Exception as e:
            logger.error(f"Error fetching market prices for {market_id}: {e}")
            return pd.DataFrame()

    def get_market_info(self, market_id: str) -> Dict:
        """
        Get detailed information about a Kalshi market.
        
        Args:
            market_id: Kalshi market ticker
            
        Returns:
            Dictionary with detailed market information
            
        Example:
            >>> provider = KalshiProvider()
            >>> info = provider.get_market_info('TICKER-123')
            >>> print(f"Title: {info['title']}")
        """
        try:
            endpoint = f"markets/{market_id}"
            data = self._make_request(endpoint)
            
            market_info = data.get('market', {})
            logger.info(f"Retrieved info for market {market_id}")
            return market_info
            
        except Exception as e:
            logger.error(f"Error fetching market info for {market_id}: {e}")
            return {}


def get_prediction_market_provider(
    provider_name: str,
    **kwargs
) -> PredictionMarketProvider:
    """
    Factory function to get a prediction market provider instance.
    
    Args:
        provider_name: Name of the provider ('polymarket' or 'kalshi')
        **kwargs: Additional arguments to pass to provider constructor
        
    Returns:
        PredictionMarketProvider instance
        
    Example:
        >>> provider = get_prediction_market_provider('polymarket')
        >>> markets = provider.get_active_markets()
        
        >>> kalshi = get_prediction_market_provider('kalshi', api_key='your_key')
        >>> markets = kalshi.get_active_markets()
    """
    providers = {
        'polymarket': PolymarketProvider,
        'kalshi': KalshiProvider,
    }
    
    provider_class = providers.get(provider_name.lower())
    if provider_class is None:
        raise ValueError(
            f"Unknown provider: {provider_name}. Available: {list(providers.keys())}"
        )
    
    return provider_class(**kwargs)
