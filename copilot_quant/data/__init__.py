"""
Data ingestion and storage modules.

This module provides:
- Market data providers (yfinance, etc.)
- S&P500 constituent management
- Prediction market data providers (Polymarket, Kalshi)
- Data normalization and quality utilities
- Data backfill and incremental update utilities
- Data caching and storage utilities
- Signal persistence and database models
"""

from copilot_quant.data.models import (
    SignalRecord,
    SignalStatus,
)
from copilot_quant.data.normalization import (
    adjust_for_contract_roll,
    adjust_for_splits,
    calculate_adjusted_close,
    detect_missing_data,
    fill_missing_data,
    normalize_symbol,
    normalize_timestamps,
    remove_outliers,
    resample_data,
    standardize_column_names,
    validate_data_quality,
    validate_symbol,
)
from copilot_quant.data.prediction_markets import (
    KalshiProvider,
    PolymarketProvider,
    PredictionMarketProvider,
    get_prediction_market_provider,
)
from copilot_quant.data.providers import (
    DataProvider,
    YFinanceProvider,
    get_data_provider,
)
from copilot_quant.data.signal_repository import (
    SignalRepository,
)
from copilot_quant.data.sp500 import (
    DOW_30_TICKERS,
    FAANG,
    MAGNIFICENT_7,
    get_sp500_by_sector,
    get_sp500_info,
    get_sp500_tickers,
)
from copilot_quant.data.update_jobs import (
    DataUpdater,
)

__all__ = [
    # Providers
    "DataProvider",
    "YFinanceProvider",
    "get_data_provider",
    # S&P500 utilities
    "get_sp500_tickers",
    "get_sp500_info",
    "get_sp500_by_sector",
    "FAANG",
    "MAGNIFICENT_7",
    "DOW_30_TICKERS",
    # Prediction markets
    "PredictionMarketProvider",
    "PolymarketProvider",
    "KalshiProvider",
    "get_prediction_market_provider",
    # Normalization
    "normalize_symbol",
    "validate_symbol",
    "normalize_timestamps",
    "adjust_for_contract_roll",
    "standardize_column_names",
    "adjust_for_splits",
    "calculate_adjusted_close",
    "detect_missing_data",
    "validate_data_quality",
    "fill_missing_data",
    "remove_outliers",
    "resample_data",
    # Update utilities
    "DataUpdater",
    # Signal persistence
    "SignalRecord",
    "SignalStatus",
    "SignalRepository",
]
