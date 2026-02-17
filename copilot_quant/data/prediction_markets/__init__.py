"""
Prediction market data fetchers for various platforms.

This module provides data fetchers for:
- Polymarket
- Kalshi
- PredictIt
- Metaculus

Each fetcher provides methods to:
- List available markets/contracts
- Fetch historical price data
- Normalize market/contract names
- Save data to CSV or SQLite
"""

from copilot_quant.data.prediction_markets.base import PredictionMarketProvider
from copilot_quant.data.prediction_markets.polymarket import PolymarketProvider
from copilot_quant.data.prediction_markets.kalshi import KalshiProvider
from copilot_quant.data.prediction_markets.predictit import PredictItProvider
from copilot_quant.data.prediction_markets.metaculus import MetaculusProvider
from copilot_quant.data.prediction_markets.storage import PredictionMarketStorage


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


__all__ = [
    "PredictionMarketProvider",
    "PolymarketProvider",
    "KalshiProvider",
    "PredictItProvider",
    "MetaculusProvider",
    "PredictionMarketStorage",
    "get_prediction_market_provider",
]
