"""
Data Provider Factory

This module provides a factory function to create the appropriate data provider
based on the execution mode (live, backtest, or mock).

Features:
- Unified interface for creating data providers
- Support for live (IBKR), backtest (yfinance), and mock modes
- MockDataProvider for testing without network calls
"""

import logging
from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Union

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


class MockDataProvider(ABC):
    """
    Mock data provider for testing purposes.
    
    Generates realistic-looking OHLCV data without making network calls.
    Implements the same interface as YFinanceProvider and LiveDataFeedAdapter.
    """
    
    def __init__(self, seed: int = 42, base_price: float = 100.0, volatility: float = 0.02):
        """
        Initialize mock data provider.
        
        Args:
            seed: Random seed for reproducible data generation
            base_price: Starting price for synthetic data
            volatility: Daily volatility (std dev of returns)
        """
        self.seed = seed
        self.base_price = base_price
        self.volatility = volatility
        self.name = "Mock Data Provider"
        logger.info(f"Initialized {self.name}")
    
    def get_historical_data(
        self,
        symbol: str,
        start_date: Optional[Union[str, datetime]] = None,
        end_date: Optional[Union[str, datetime]] = None,
        interval: str = "1d",
    ) -> pd.DataFrame:
        """
        Generate mock historical OHLCV data.
        
        Args:
            symbol: Ticker symbol (used for seeding)
            start_date: Start date for data (default: 1 year ago)
            end_date: End date for data (default: today)
            interval: Data interval (only '1d' supported for now)
        
        Returns:
            DataFrame with columns: Open, High, Low, Close, Volume
        """
        # Set default dates
        if start_date is None:
            start_date = datetime.now() - timedelta(days=365)
        if end_date is None:
            end_date = datetime.now()
        
        # Convert strings to datetime if needed
        if isinstance(start_date, str):
            start_date = pd.to_datetime(start_date)
        if isinstance(end_date, str):
            end_date = pd.to_datetime(end_date)
        
        # Generate date range
        dates = pd.date_range(start=start_date, end=end_date, freq="D")
        
        # Set seed based on symbol for consistency
        np.random.seed(self.seed + hash(symbol) % 1000)
        
        # Generate price series with geometric brownian motion
        n_days = len(dates)
        returns = np.random.normal(0.0001, self.volatility, n_days)  # Small positive drift
        price_multipliers = np.exp(returns)
        
        # Calculate close prices
        close_prices = self.base_price * np.cumprod(price_multipliers)
        
        # Generate OHLC data
        # High is close + random amount, low is close - random amount
        high_variation = np.abs(np.random.normal(0, self.volatility * self.base_price, n_days))
        low_variation = np.abs(np.random.normal(0, self.volatility * self.base_price, n_days))
        
        high_prices = close_prices + high_variation
        low_prices = close_prices - low_variation
        
        # Ensure low <= close <= high
        low_prices = np.minimum(low_prices, close_prices)
        high_prices = np.maximum(high_prices, close_prices)
        
        # Open is previous close (roughly)
        open_prices = np.roll(close_prices, 1)
        open_prices[0] = self.base_price
        
        # Ensure open is within low-high range
        open_prices = np.clip(open_prices, low_prices, high_prices)
        
        # Generate volume (random but realistic)
        volume = np.random.lognormal(15, 1, n_days).astype(int)  # Approx 1-10M shares
        
        # Create DataFrame
        df = pd.DataFrame(
            {
                "Open": open_prices,
                "High": high_prices,
                "Low": low_prices,
                "Close": close_prices,
                "Volume": volume,
            },
            index=dates,
        )
        
        logger.info(f"Generated {len(df)} mock bars for {symbol}")
        return df
    
    def get_multiple_symbols(
        self,
        symbols: List[str],
        start_date: Optional[Union[str, datetime]] = None,
        end_date: Optional[Union[str, datetime]] = None,
        interval: str = "1d",
    ) -> pd.DataFrame:
        """
        Generate mock data for multiple symbols.
        
        Args:
            symbols: List of ticker symbols
            start_date: Start date for data
            end_date: End date for data
            interval: Data interval
        
        Returns:
            DataFrame with multi-level columns (Metric, Symbol)
        """
        if not symbols:
            return pd.DataFrame()
        
        all_data = {}
        for symbol in symbols:
            df = self.get_historical_data(symbol, start_date, end_date, interval)
            if not df.empty:
                all_data[symbol] = df
        
        if not all_data:
            return pd.DataFrame()
        
        # Combine into multi-level column format
        combined_df = pd.concat(all_data, axis=1)
        
        # Swap levels to get (Metric, Symbol) format
        if isinstance(combined_df.columns, pd.MultiIndex):
            combined_df.columns = combined_df.columns.swaplevel(0, 1)
        
        return combined_df
    
    def get_ticker_info(self, symbol: str) -> Dict:
        """
        Return mock ticker information.
        
        Args:
            symbol: Ticker symbol
        
        Returns:
            Dictionary with mock metadata
        """
        return {
            "symbol": symbol,
            "longName": f"{symbol} Mock Corporation",
            "sector": "Technology",
            "industry": "Software",
            "marketCap": 1000000000000,  # $1T
            "currency": "USD",
        }


def create_data_provider(mode: str = "backtest", **kwargs):
    """
    Factory function to create the appropriate data provider.
    
    This function creates different data provider instances based on the
    execution mode, allowing seamless switching between live IBKR data,
    backtest yfinance data, and mock data for testing.
    
    Args:
        mode: Execution mode - "live", "backtest", or "mock"
        **kwargs: Additional arguments passed to the provider constructor
            For "live" mode:
                - paper_trading (bool): Use paper trading account
                - host (str): IB API host
                - port (int): IB API port
                - client_id (int): Client ID
                - use_gateway (bool): Use IB Gateway vs TWS
            For "backtest" mode:
                - No additional arguments needed
            For "mock" mode:
                - seed (int): Random seed
                - base_price (float): Starting price
                - volatility (float): Daily volatility
    
    Returns:
        Data provider instance implementing the common interface
    
    Raises:
        ValueError: If mode is not recognized
        ImportError: If required package is not available for the mode
    
    Examples:
        >>> # Live mode with IBKR
        >>> provider = create_data_provider("live", paper_trading=True)
        >>> data = provider.get_historical_data("AAPL")
        
        >>> # Backtest mode with yfinance
        >>> provider = create_data_provider("backtest")
        >>> data = provider.get_historical_data("SPY", start_date="2024-01-01")
        
        >>> # Mock mode for testing
        >>> provider = create_data_provider("mock", seed=123, base_price=150.0)
        >>> data = provider.get_historical_data("TSLA")
    """
    mode = mode.lower()
    
    if mode == "live":
        try:
            from copilot_quant.brokers.live_data_adapter import LiveDataFeedAdapter
        except ImportError as e:
            raise ImportError(
                "Live mode requires IBKR dependencies. "
                "Make sure all broker dependencies are installed."
            ) from e
        
        logger.info("Creating live data provider (IBKR)")
        return LiveDataFeedAdapter(**kwargs)
    
    elif mode == "backtest":
        try:
            from copilot_quant.data.providers import YFinanceProvider
        except ImportError as e:
            raise ImportError(
                "Backtest mode requires yfinance. "
                "Install it with: pip install yfinance"
            ) from e
        
        logger.info("Creating backtest data provider (yfinance)")
        return YFinanceProvider()
    
    elif mode == "mock":
        logger.info("Creating mock data provider")
        return MockDataProvider(**kwargs)
    
    else:
        raise ValueError(
            f"Unknown mode: {mode}. "
            f"Valid modes are: 'live', 'backtest', 'mock'"
        )
