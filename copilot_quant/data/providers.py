"""
Market data providers for downloading historical and real-time data.

This module implements data provider interfaces for various sources.
Primary provider: yfinance (Yahoo Finance)
"""

import logging
from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from typing import List, Optional, Union

import pandas as pd
import yfinance as yf

logger = logging.getLogger(__name__)


class DataProvider(ABC):
    """Abstract base class for market data providers."""

    @abstractmethod
    def get_historical_data(
        self,
        symbol: str,
        start_date: Optional[Union[str, datetime]] = None,
        end_date: Optional[Union[str, datetime]] = None,
        interval: str = "1d",
    ) -> pd.DataFrame:
        """
        Get historical OHLCV data for a symbol.

        Args:
            symbol: Ticker symbol (e.g., 'AAPL', '^GSPC')
            start_date: Start date for historical data
            end_date: End date for historical data
            interval: Data interval ('1d', '1wk', '1mo', etc.)

        Returns:
            DataFrame with columns: Open, High, Low, Close, Volume, Dividends, Stock Splits
        """
        pass

    @abstractmethod
    def get_multiple_symbols(
        self,
        symbols: List[str],
        start_date: Optional[Union[str, datetime]] = None,
        end_date: Optional[Union[str, datetime]] = None,
        interval: str = "1d",
    ) -> pd.DataFrame:
        """
        Get historical data for multiple symbols at once.

        Args:
            symbols: List of ticker symbols
            start_date: Start date for historical data
            end_date: End date for historical data
            interval: Data interval ('1d', '1wk', '1mo', etc.)

        Returns:
            Multi-index DataFrame with (Date, Symbol) index or
            DataFrame with multi-level columns (Metric, Symbol)
        """
        pass

    @abstractmethod
    def get_ticker_info(self, symbol: str) -> dict:
        """
        Get metadata about a ticker.

        Args:
            symbol: Ticker symbol

        Returns:
            Dictionary with ticker information (name, sector, industry, etc.)
        """
        pass


class YFinanceProvider(DataProvider):
    """
    Yahoo Finance data provider using yfinance library.

    This is the primary data source for the platform.
    Provides free, unlimited access to historical market data.
    """

    def __init__(self):
        """Initialize Yahoo Finance provider."""
        self.name = "Yahoo Finance (yfinance)"
        logger.info(f"Initialized {self.name} provider")

    def get_historical_data(
        self,
        symbol: str,
        start_date: Optional[Union[str, datetime]] = None,
        end_date: Optional[Union[str, datetime]] = None,
        interval: str = "1d",
    ) -> pd.DataFrame:
        """
        Get historical OHLCV data for a symbol from Yahoo Finance.

        Args:
            symbol: Ticker symbol (e.g., 'AAPL', '^GSPC')
            start_date: Start date for historical data (default: 1 year ago)
            end_date: End date for historical data (default: today)
            interval: Data interval - '1d', '1wk', '1mo' (default: '1d')

        Returns:
            DataFrame with columns: Open, High, Low, Close, Volume, Dividends, Stock Splits
            Index: DatetimeIndex

        Example:
            >>> provider = YFinanceProvider()
            >>> data = provider.get_historical_data('AAPL', start_date='2023-01-01', end_date='2024-01-01')
            >>> print(data.head())
        """
        try:
            ticker = yf.Ticker(symbol)

            # Set default dates if not provided
            if start_date is None:
                start_date = datetime.now() - timedelta(days=365)
            if end_date is None:
                end_date = datetime.now()

            # Convert dates to strings if datetime objects
            if isinstance(start_date, datetime):
                start_date = start_date.strftime("%Y-%m-%d")
            if isinstance(end_date, datetime):
                end_date = end_date.strftime("%Y-%m-%d")

            # Download historical data
            data = ticker.history(
                start=start_date,
                end=end_date,
                interval=interval,
                actions=True,  # Include dividends and splits
                auto_adjust=False,  # Keep both adjusted and unadjusted prices
            )

            if data.empty:
                logger.warning(f"No data returned for {symbol}")
                return pd.DataFrame()

            logger.info(f"Downloaded {len(data)} rows for {symbol} from {start_date} to {end_date}")
            return data

        except Exception as e:
            logger.error(f"Error downloading data for {symbol}: {e}")
            raise

    def get_multiple_symbols(
        self,
        symbols: List[str],
        start_date: Optional[Union[str, datetime]] = None,
        end_date: Optional[Union[str, datetime]] = None,
        interval: str = "1d",
    ) -> pd.DataFrame:
        """
        Get historical data for multiple symbols efficiently.

        Args:
            symbols: List of ticker symbols
            start_date: Start date for historical data
            end_date: End date for historical data
            interval: Data interval ('1d', '1wk', '1mo')

        Returns:
            DataFrame with multi-level columns: (Metric, Symbol)
            Index: DatetimeIndex

        Example:
            >>> provider = YFinanceProvider()
            >>> data = provider.get_multiple_symbols(['AAPL', 'MSFT'], start_date='2023-01-01')
            >>> print(data['Close'])  # Close prices for all symbols
        """
        try:
            # Set default dates
            if start_date is None:
                start_date = datetime.now() - timedelta(days=365)
            if end_date is None:
                end_date = datetime.now()

            # Convert dates to strings if datetime objects
            if isinstance(start_date, datetime):
                start_date = start_date.strftime("%Y-%m-%d")
            if isinstance(end_date, datetime):
                end_date = end_date.strftime("%Y-%m-%d")

            # Download data for multiple symbols
            data = yf.download(
                symbols,
                start=start_date,
                end=end_date,
                interval=interval,
                actions=True,
                auto_adjust=False,
                progress=False,  # Suppress progress bar
                group_by="column",  # Group by metric, not ticker
            )

            if data.empty:
                logger.warning(f"No data returned for symbols: {symbols}")
                return pd.DataFrame()

            logger.info(f"Downloaded data for {len(symbols)} symbols from {start_date} to {end_date}")
            return data

        except Exception as e:
            logger.error(f"Error downloading data for multiple symbols: {e}")
            raise

    def get_ticker_info(self, symbol: str) -> dict:
        """
        Get metadata about a ticker from Yahoo Finance.

        Args:
            symbol: Ticker symbol

        Returns:
            Dictionary with ticker information including:
            - longName: Company name
            - sector: Business sector
            - industry: Industry classification
            - marketCap: Market capitalization
            - And other available fields

        Example:
            >>> provider = YFinanceProvider()
            >>> info = provider.get_ticker_info('AAPL')
            >>> print(info['longName'])  # Apple Inc.
        """
        try:
            ticker = yf.Ticker(symbol)
            info = ticker.info

            logger.info(f"Retrieved info for {symbol}: {info.get('longName', 'N/A')}")
            return info

        except Exception as e:
            logger.error(f"Error getting info for {symbol}: {e}")
            raise

    def get_sp500_index(
        self,
        start_date: Optional[Union[str, datetime]] = None,
        end_date: Optional[Union[str, datetime]] = None,
    ) -> pd.DataFrame:
        """
        Get S&P500 index (^GSPC) historical data.

        Args:
            start_date: Start date for historical data
            end_date: End date for historical data

        Returns:
            DataFrame with S&P500 index OHLCV data

        Example:
            >>> provider = YFinanceProvider()
            >>> sp500 = provider.get_sp500_index(start_date='2020-01-01')
            >>> print(sp500.head())
        """
        return self.get_historical_data("^GSPC", start_date, end_date)


# Factory function for easy provider creation
def get_data_provider(provider_name: str = "yfinance") -> DataProvider:
    """
    Factory function to get a data provider instance.

    Args:
        provider_name: Name of the provider ('yfinance', etc.)

    Returns:
        DataProvider instance

    Example:
        >>> provider = get_data_provider('yfinance')
        >>> data = provider.get_historical_data('AAPL')
    """
    providers = {
        "yfinance": YFinanceProvider,
        "yahoo": YFinanceProvider,
    }

    provider_class = providers.get(provider_name.lower())
    if provider_class is None:
        raise ValueError(f"Unknown provider: {provider_name}. Available: {list(providers.keys())}")

    return provider_class()
