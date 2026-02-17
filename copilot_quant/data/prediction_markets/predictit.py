"""
PredictIt data fetcher.

Fetches market data from PredictIt using their public API.
API Documentation: https://www.predictit.org/api/
"""

import logging
from datetime import datetime
from typing import Dict, Optional, Union

import pandas as pd
import requests

from copilot_quant.data.prediction_markets.base import PredictionMarketProvider

logger = logging.getLogger(__name__)


class PredictItProvider(PredictionMarketProvider):
    """PredictIt data provider."""

    def __init__(self):
        """Initialize PredictIt provider."""
        super().__init__("PredictIt")
        self.base_url = "https://www.predictit.org/api/marketdata"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'copilot_quant/1.0.0',
            'Accept': 'application/json'
        })

    def list_markets(self, limit: Optional[int] = None) -> pd.DataFrame:
        """
        List available markets on PredictIt.

        Args:
            limit: Maximum number of markets to return

        Returns:
            DataFrame with market information
        """
        try:
            url = f"{self.base_url}/all"
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            data = response.json()

            markets = []
            raw_markets = data.get('markets', [])
            
            for market in raw_markets[:limit] if limit else raw_markets:
                markets.append({
                    'market_id': str(market.get('id', '')),
                    'title': market.get('name', ''),
                    'category': market.get('url', '').split('/')[0] if market.get('url') else '',
                    'close_time': market.get('dateEnd', ''),
                    'status': market.get('status', ''),
                    'volume': 0,  # PredictIt doesn't provide volume in listing
                    'liquidity': 0,
                })

            df = pd.DataFrame(markets)
            if not df.empty and 'close_time' in df.columns:
                df['close_time'] = pd.to_datetime(df['close_time'], errors='coerce')
            
            logger.info(f"Retrieved {len(df)} markets from PredictIt")
            return df

        except requests.RequestException as e:
            logger.error(f"Failed to fetch PredictIt markets: {e}")
            return pd.DataFrame()
        except Exception as e:
            logger.error(f"Unexpected error fetching PredictIt markets: {e}")
            return pd.DataFrame()

    def get_market_data(
        self,
        market_id: str,
        start_date: Optional[Union[str, datetime]] = None,
        end_date: Optional[Union[str, datetime]] = None,
    ) -> pd.DataFrame:
        """
        Get current price data for a PredictIt market.

        Note: PredictIt's public API does not provide historical time series data.
        This returns the current snapshot of contract prices.

        Args:
            market_id: Market ID
            start_date: Not used (API limitation)
            end_date: Not used (API limitation)

        Returns:
            DataFrame with current contract prices
        """
        try:
            # PredictIt doesn't have a historical data endpoint in their public API
            # We can only get current prices
            market_details = self.get_market_details(market_id)
            
            if not market_details or 'contracts' not in market_details:
                logger.warning(f"Could not find contract info for market {market_id}")
                return pd.DataFrame()

            contracts = market_details['contracts']
            prices = []
            
            for contract in contracts:
                prices.append({
                    'contract_id': contract.get('id', ''),
                    'contract_name': contract.get('name', ''),
                    'last_trade_price': float(contract.get('lastTradePrice', 0)),
                    'best_buy_yes': float(contract.get('bestBuyYesCost', 0)),
                    'best_buy_no': float(contract.get('bestBuyNoCost', 0)),
                    'best_sell_yes': float(contract.get('bestSellYesCost', 0)),
                    'best_sell_no': float(contract.get('bestSellNoCost', 0)),
                })

            df = pd.DataFrame(prices)
            logger.info(f"Retrieved current prices for {len(df)} contracts in market {market_id}")
            
            if start_date or end_date:
                logger.warning("PredictIt API does not support historical data queries. Returning current snapshot only.")
            
            return df

        except Exception as e:
            logger.error(f"Unexpected error fetching PredictIt market data: {e}")
            return pd.DataFrame()

    def get_market_details(self, market_id: str) -> Dict:
        """
        Get detailed information about a PredictIt market.

        Args:
            market_id: Market ID

        Returns:
            Dictionary with market details
        """
        try:
            url = f"{self.base_url}/markets/{market_id}"
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            data = response.json()

            return {
                'market_id': str(data.get('id', '')),
                'title': data.get('name', ''),
                'description': data.get('shortName', ''),
                'category': data.get('url', '').split('/')[0] if data.get('url') else '',
                'image_url': data.get('image', ''),
                'contracts': data.get('contracts', []),
                'close_time': data.get('dateEnd', ''),
                'status': data.get('status', ''),
            }

        except requests.RequestException as e:
            logger.error(f"Failed to fetch PredictIt market details: {e}")
            return {}
        except Exception as e:
            logger.error(f"Unexpected error fetching PredictIt market details: {e}")
            return {}
