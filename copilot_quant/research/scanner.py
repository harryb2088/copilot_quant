"""
Securities Research Scanner

This module provides functionality to filter and search for equities and ETFs
based on various criteria such as sector, market cap, volatility, and more.
"""

import logging
from typing import List, Optional

import pandas as pd
import yfinance as yf

from copilot_quant.data.sp500 import get_sp500_tickers

logger = logging.getLogger(__name__)


class SecurityScanner:
    """
    Scanner for filtering equities and ETFs by profile criteria.

    The SecurityScanner provides flexible filtering capabilities for securities
    based on fundamental and technical characteristics. It can use local data
    or fetch live data from Yahoo Finance.

    Attributes:
        data_source: Data source to use ('local' or 'yfinance')
        df: DataFrame containing the securities universe (when using local source)

    Example:
        >>> scanner = SecurityScanner(data_source='local')
        >>> results = scanner.find(
        ...     sector='Technology',
        ...     market_cap_min=5e9,
        ...     asset_type='equity'
        ... )
        >>> print(results.head())
    """

    def __init__(self, data_source: str = "local"):
        """
        Initialize the SecurityScanner.

        Args:
            data_source: Data source to use - 'local' (default) or 'yfinance'

        Raises:
            ValueError: If data_source is not 'local' or 'yfinance'
        """
        if data_source not in ["local", "yfinance"]:
            raise ValueError(f"Invalid data_source: {data_source}. Must be 'local' or 'yfinance'")

        self.data_source = data_source
        self.df = None

        if data_source == "local":
            self._load_local_universe()

        logger.info(f"SecurityScanner initialized with data_source='{data_source}'")

    def _load_local_universe(self):
        """
        Load securities universe from local data sources.

        This method fetches S&P 500 constituents and enriches them with
        metadata from Yahoo Finance. The data is cached for efficient filtering.
        """
        logger.info("Loading local securities universe...")

        # Get S&P 500 tickers as the base universe
        tickers = get_sp500_tickers(source="manual")

        # Create a basic DataFrame
        # In a production system, this would load from a cached CSV/database
        securities_data = []

        for ticker in tickers:
            securities_data.append(
                {
                    "ticker": ticker,
                    "name": None,
                    "sector": None,
                    "industry": None,
                    "market_cap": None,
                    "avg_volume": None,
                    "volatility": None,
                    "dividend_yield": None,
                    "asset_type": "equity",  # Default to equity for S&P 500
                }
            )

        self.df = pd.DataFrame(securities_data)
        logger.info(f"Loaded {len(self.df)} securities into local universe")

    def _fetch_ticker_data(self, ticker: str) -> dict:
        """
        Fetch current data for a ticker from Yahoo Finance.

        Args:
            ticker: Ticker symbol

        Returns:
            Dictionary with ticker information
        """
        try:
            stock = yf.Ticker(ticker)
            info = stock.info

            # Calculate volatility if historical data is available
            volatility = None
            try:
                hist = stock.history(period="1y")
                if not hist.empty and len(hist) > 20:
                    returns = hist["Close"].pct_change().dropna()
                    volatility = returns.std() * (252**0.5)  # Annualized volatility
            except Exception:
                pass

            # Extract relevant fields with safe fallbacks
            return {
                "ticker": ticker,
                "name": info.get("longName", info.get("shortName", ticker)),
                "sector": info.get("sector"),
                "industry": info.get("industry"),
                "market_cap": info.get("marketCap"),
                "avg_volume": info.get("averageVolume"),
                "volatility": volatility,
                "dividend_yield": info.get("dividendYield"),
                "asset_type": self._determine_asset_type(info),
            }
        except Exception as e:
            logger.warning(f"Error fetching data for {ticker}: {e}")
            return {
                "ticker": ticker,
                "name": None,
                "sector": None,
                "industry": None,
                "market_cap": None,
                "avg_volume": None,
                "volatility": None,
                "dividend_yield": None,
                "asset_type": "equity",
            }

    def _determine_asset_type(self, info: dict) -> str:
        """
        Determine asset type from ticker info.

        Args:
            info: Yahoo Finance ticker info dictionary

        Returns:
            Asset type string ('equity' or 'etf')
        """
        quote_type = info.get("quoteType", "").lower()
        if quote_type == "etf":
            return "etf"
        return "equity"

    def find(
        self,
        sector: Optional[str] = None,
        industry: Optional[str] = None,
        market_cap_min: Optional[float] = None,
        market_cap_max: Optional[float] = None,
        avg_volume_min: Optional[float] = None,
        volatility_max: Optional[float] = None,
        volatility_min: Optional[float] = None,
        asset_type: Optional[str] = None,
        dividend_yield_min: Optional[float] = None,
        dividend_yield_max: Optional[float] = None,
        tickers: Optional[List[str]] = None,
        exclude_tickers: Optional[List[str]] = None,
        as_json: bool = False,
        fetch_live_data: bool = False,
    ) -> pd.DataFrame:
        """
        Find securities matching the specified criteria.

        Args:
            sector: Filter by GICS sector (e.g., 'Technology', 'Healthcare')
            industry: Filter by industry classification
            market_cap_min: Minimum market capitalization in dollars
            market_cap_max: Maximum market capitalization in dollars
            avg_volume_min: Minimum average daily trading volume
            volatility_max: Maximum annualized volatility (e.g., 0.35 for 35%)
            volatility_min: Minimum annualized volatility
            asset_type: Filter by asset type ('equity' or 'etf')
            dividend_yield_min: Minimum dividend yield (e.g., 0.02 for 2%)
            dividend_yield_max: Maximum dividend yield
            tickers: Specific list of tickers to include (filters universe)
            exclude_tickers: List of tickers to exclude
            as_json: If True, return results as list of dictionaries (JSON format)
            fetch_live_data: If True, fetch live data from yfinance for each ticker

        Returns:
            DataFrame with matching securities (or list of dicts if as_json=True)

        Raises:
            ValueError: If no securities match the criteria

        Example:
            >>> scanner = SecurityScanner()
            >>> # Find tech stocks over $5B market cap
            >>> results = scanner.find(
            ...     sector='Technology',
            ...     market_cap_min=5e9,
            ...     avg_volume_min=2e6,
            ... )
            >>> # Find high dividend ETFs
            >>> etfs = scanner.find(
            ...     asset_type='etf',
            ...     dividend_yield_min=0.02,
            ... )
        """
        # Start with the full universe
        if self.data_source == "yfinance" or fetch_live_data:
            # For yfinance mode, we need to fetch data for tickers
            if tickers is None:
                # Default to S&P 500 if no tickers specified
                tickers = get_sp500_tickers(source="manual")

            logger.info(f"Fetching live data for {len(tickers)} tickers...")
            securities_data = []
            for ticker in tickers:
                data = self._fetch_ticker_data(ticker)
                securities_data.append(data)

            df = pd.DataFrame(securities_data)
        else:
            # Use cached local data
            if self.df is None:
                raise ValueError("No local data loaded. Initialize with data_source='local'")
            df = self.df.copy()

            # Filter to specific tickers if provided
            if tickers is not None:
                df = df[df["ticker"].isin(tickers)]

        # Exclude specific tickers if provided
        if exclude_tickers is not None:
            df = df[~df["ticker"].isin(exclude_tickers)]

        # Apply filters
        if sector is not None:
            df = df[df["sector"] == sector]

        if industry is not None:
            df = df[df["industry"] == industry]

        if market_cap_min is not None:
            df = df[df["market_cap"] >= market_cap_min]

        if market_cap_max is not None:
            df = df[df["market_cap"] <= market_cap_max]

        if avg_volume_min is not None:
            df = df[df["avg_volume"] >= avg_volume_min]

        if volatility_max is not None:
            df = df[df["volatility"] <= volatility_max]

        if volatility_min is not None:
            df = df[df["volatility"] >= volatility_min]

        if asset_type is not None:
            df = df[df["asset_type"] == asset_type]

        if dividend_yield_min is not None:
            df = df[df["dividend_yield"] >= dividend_yield_min]

        if dividend_yield_max is not None:
            df = df[df["dividend_yield"] <= dividend_yield_max]

        # Check if any results found
        if df.empty:
            raise ValueError("No securities match the provided criteria. Try relaxing your filter parameters.")

        logger.info(f"Found {len(df)} securities matching criteria")

        # Return in requested format
        if as_json:
            return df.to_dict(orient="records")

        return df
