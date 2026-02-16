"""
Data ingestion and storage modules.

This module provides:
- Market data providers (yfinance, etc.)
- S&P500 constituent management
- Data caching and storage utilities
"""

from copilot_quant.data.providers import (
    DataProvider,
    YFinanceProvider,
    get_data_provider,
)
from copilot_quant.data.sp500 import (
    DOW_30_TICKERS,
    FAANG,
    MAGNIFICENT_7,
    get_sp500_by_sector,
    get_sp500_info,
    get_sp500_tickers,
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
]
