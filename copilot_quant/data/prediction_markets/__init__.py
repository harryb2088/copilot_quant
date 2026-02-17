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

__all__ = [
    "PredictionMarketProvider",
    "PolymarketProvider",
    "KalshiProvider",
    "PredictItProvider",
    "MetaculusProvider",
    "PredictionMarketStorage",
]
