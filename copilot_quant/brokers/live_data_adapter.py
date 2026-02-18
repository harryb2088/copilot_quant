"""
Live Data Feed Adapter for Strategy Engine Integration

This module provides an adapter that implements the IDataFeed interface
from the backtest engine, allowing live IBKR market data to be used with
strategies designed for backtesting.

Features:
- Implements IDataFeed interface for seamless strategy integration
- Real-time data streaming with automatic reconnection
- Historical data fallback when live feed is disconnected
- Transparent handling of data format conversion
- Error handling and logging

Example Usage:
    >>> from copilot_quant.brokers.live_data_adapter import LiveDataFeedAdapter
    >>> 
    >>> # Initialize adapter
    >>> adapter = LiveDataFeedAdapter(paper_trading=True)
    >>> if adapter.connect():
    ...     # Use with strategy engine
    ...     data = adapter.get_historical_data('AAPL', interval='1d')
    ...     
    ...     # Subscribe for real-time updates
    ...     adapter.subscribe(['AAPL', 'MSFT'])
    ...     
    ...     # Get latest data in backtest-compatible format
    ...     latest = adapter.get_latest_bar('AAPL')
    ...     
    ...     adapter.disconnect()
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import pandas as pd

from copilot_quant.backtest.interfaces import IDataFeed
from copilot_quant.brokers.live_market_data import IBKRLiveDataFeed

logger = logging.getLogger(__name__)


class LiveDataFeedAdapter(IDataFeed):
    """
    Adapter that implements IDataFeed interface using IBKR live market data.
    
    This class bridges the gap between the backtest engine's data feed interface
    and IBKR's live market data API, allowing strategies to work seamlessly in
    both backtest and live trading modes.
    
    The adapter:
    - Implements all IDataFeed methods
    - Manages real-time data subscriptions
    - Handles reconnection and fallback scenarios
    - Normalizes data format to match backtest expectations
    - Provides caching for recent data
    
    Example:
        >>> adapter = LiveDataFeedAdapter(paper_trading=True)
        >>> adapter.connect()
        >>> 
        >>> # Get historical data (backtest-compatible)
        >>> hist_data = adapter.get_historical_data(
        ...     'AAPL',
        ...     start_date=datetime(2024, 1, 1),
        ...     end_date=datetime(2024, 12, 31),
        ...     interval='1d'
        ... )
        >>> 
        >>> # Subscribe to real-time data
        >>> adapter.subscribe(['AAPL'])
        >>> 
        >>> # Get latest price as if it were historical data
        >>> latest_bar = adapter.get_latest_bar('AAPL')
        >>> 
        >>> adapter.disconnect()
    """
    
    def __init__(
        self,
        paper_trading: bool = True,
        host: Optional[str] = None,
        port: Optional[int] = None,
        client_id: Optional[int] = None,
        use_gateway: bool = False,
        enable_cache: bool = True,
        cache_size: int = 1000
    ):
        """
        Initialize the live data feed adapter.
        
        Args:
            paper_trading: If True, connect to paper trading account
            host: IB API host address (default: from env or '127.0.0.1')
            port: IB API port (default: auto-detected based on mode)
            client_id: Unique client identifier (default: from env or 1)
            use_gateway: If True, use IB Gateway ports, else use TWS ports
            enable_cache: If True, cache recent bars for each symbol
            cache_size: Maximum number of bars to cache per symbol
        """
        # Initialize underlying IBKR live data feed
        self._live_feed = IBKRLiveDataFeed(
            paper_trading=paper_trading,
            host=host,
            port=port,
            client_id=client_id,
            use_gateway=use_gateway
        )
        
        # Configuration
        self.enable_cache = enable_cache
        self.cache_size = cache_size
        
        # Data caching for recent bars
        self._bar_cache: Dict[str, pd.DataFrame] = {}  # symbol -> DataFrame of recent bars
        
        # Track disconnection state for fallback
        self._is_fallback_mode = False
        self._fallback_data: Dict[str, pd.DataFrame] = {}
        
        logger.info("LiveDataFeedAdapter initialized")
    
    def connect(self, timeout: int = 30, retry_count: int = 3) -> bool:
        """
        Establish connection to IBKR.
        
        Args:
            timeout: Connection timeout in seconds
            retry_count: Number of connection retry attempts
            
        Returns:
            True if connection successful, False otherwise
        """
        success = self._live_feed.connect(timeout=timeout, retry_count=retry_count)
        if success:
            self._is_fallback_mode = False
            logger.info("Live data feed connected")
        else:
            logger.error("Failed to connect to live data feed")
        return success
    
    def is_connected(self) -> bool:
        """Check if currently connected to IBKR"""
        return self._live_feed.is_connected()
    
    def reconnect(self, timeout: int = 30) -> bool:
        """
        Attempt to reconnect to IBKR after disconnection.
        
        Args:
            timeout: Connection timeout in seconds
            
        Returns:
            True if reconnection successful, False otherwise
        """
        logger.info("Attempting to reconnect to IBKR...")
        success = self._live_feed.reconnect(timeout=timeout)
        
        if success:
            self._is_fallback_mode = False
            logger.info("✓ Reconnection successful")
        else:
            logger.warning("Reconnection failed - entering fallback mode")
            self._is_fallback_mode = True
        
        return success
    
    # IDataFeed interface implementation
    
    def get_historical_data(
        self,
        symbol: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        interval: str = '1d'
    ) -> pd.DataFrame:
        """
        Retrieve historical OHLCV data for a single symbol.
        
        This method uses IBKR's historical data API to download bars.
        The data format matches the backtest engine's expectations.
        
        Args:
            symbol: Ticker symbol (e.g., 'AAPL', 'SPY')
            start_date: Start date for data (None = use duration)
            end_date: End date for data (None = current time)
            interval: Data frequency ('1d', '1h', '1m', etc.)
        
        Returns:
            DataFrame with DatetimeIndex and columns:
                - Open: Opening price
                - High: High price
                - Low: Low price
                - Close: Closing price
                - Volume: Trading volume
        
        Raises:
            ValueError: If symbol is invalid
            ConnectionError: If not connected and cannot reconnect
        """
        if not self.is_connected():
            logger.warning("Not connected - attempting reconnection...")
            if not self.reconnect():
                raise ConnectionError("Cannot retrieve historical data - not connected to IBKR")
        
        try:
            # Convert interval format to IBKR format
            bar_size = self._convert_interval_to_bar_size(interval)
            
            # Calculate duration if start_date provided
            duration = self._calculate_duration(start_date, end_date)
            
            # Request historical data from IBKR
            df = self._live_feed.get_historical_bars(
                symbol=symbol,
                duration=duration,
                bar_size=bar_size,
                what_to_show='TRADES',
                use_rth=True
            )
            
            if df is None or df.empty:
                logger.warning(f"No historical data returned for {symbol}")
                return pd.DataFrame()
            
            # Ensure proper format for backtest compatibility
            df = self._normalize_for_backtest(df, symbol)
            
            # Filter by date range if specified
            if start_date:
                df = df[df.index >= start_date]
            if end_date:
                df = df[df.index <= end_date]
            
            # Cache the data
            if self.enable_cache:
                self._update_cache(symbol, df)
            
            logger.info(f"Retrieved {len(df)} historical bars for {symbol}")
            return df
            
        except Exception as e:
            logger.error(f"Error retrieving historical data for {symbol}: {e}")
            
            # Try fallback to cached data
            if symbol in self._bar_cache and not self._bar_cache[symbol].empty:
                logger.info(f"Using cached data for {symbol} as fallback")
                return self._bar_cache[symbol].copy()
            
            return pd.DataFrame()
    
    def get_multiple_symbols(
        self,
        symbols: List[str],
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        interval: str = '1d'
    ) -> pd.DataFrame:
        """
        Retrieve historical data for multiple symbols efficiently.
        
        Args:
            symbols: List of ticker symbols
            start_date: Start date for data
            end_date: End date for data
            interval: Data frequency
        
        Returns:
            DataFrame with multi-level columns (Metric, Symbol)
            
        Note:
            This implementation fetches data sequentially for each symbol.
            For production use, consider implementing concurrent requests.
        """
        if not symbols:
            return pd.DataFrame()
        
        all_data = {}
        
        for symbol in symbols:
            try:
                df = self.get_historical_data(
                    symbol=symbol,
                    start_date=start_date,
                    end_date=end_date,
                    interval=interval
                )
                
                if not df.empty:
                    all_data[symbol] = df
                    
            except Exception as e:
                logger.error(f"Error fetching data for {symbol}: {e}")
                continue
        
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
        Get metadata about a security.
        
        Args:
            symbol: Ticker symbol
        
        Returns:
            Dictionary with metadata
            
        Note:
            Basic implementation - can be extended with contract details
            from IBKR if needed.
        """
        return {
            'symbol': symbol,
            'name': symbol,
            'exchange': 'SMART',
            'currency': 'USD',
            'type': 'STOCK'
        }
    
    # Additional methods for live data integration
    
    def subscribe(self, symbols: List[str]) -> Dict[str, bool]:
        """
        Subscribe to real-time market data for symbols.
        
        Args:
            symbols: List of ticker symbols to subscribe to
            
        Returns:
            Dictionary mapping symbols to subscription success status
        """
        if not self.is_connected():
            logger.error("Not connected to IBKR")
            return {symbol: False for symbol in symbols}
        
        return self._live_feed.subscribe(symbols)
    
    def unsubscribe(self, symbols: List[str]) -> Dict[str, bool]:
        """
        Unsubscribe from real-time market data.
        
        Args:
            symbols: List of ticker symbols to unsubscribe from
            
        Returns:
            Dictionary mapping symbols to unsubscription success status
        """
        return self._live_feed.unsubscribe(symbols)
    
    def get_latest_price(self, symbol: str) -> Optional[float]:
        """
        Get the latest price for a subscribed symbol.
        
        Args:
            symbol: Ticker symbol
            
        Returns:
            Latest price or None if not available
        """
        return self._live_feed.get_latest_price(symbol)
    
    def get_latest_bar(self, symbol: str) -> Optional[pd.Series]:
        """
        Get the latest OHLCV bar for a symbol in backtest-compatible format.
        
        This creates a pseudo-bar from the latest tick data, useful for
        strategies that expect bar data rather than tick data.
        
        Args:
            symbol: Ticker symbol
            
        Returns:
            Series with OHLCV data or None if not available
        """
        latest_data = self._live_feed.get_latest_data(symbol)
        
        if not latest_data:
            return None
        
        # Create a bar-like series from tick data
        bar_data = {
            'Open': latest_data.get('open') or latest_data.get('last'),
            'High': latest_data.get('high') or latest_data.get('last'),
            'Low': latest_data.get('low') or latest_data.get('last'),
            'Close': latest_data.get('last') or latest_data.get('close'),
            'Volume': latest_data.get('volume', 0)
        }
        
        # Remove None values
        bar_data = {k: v for k, v in bar_data.items() if v is not None}
        
        if not bar_data:
            return None
        
        # Create series with timestamp index
        timestamp = latest_data.get('time', datetime.now())
        series = pd.Series(bar_data, name=timestamp)
        
        return series
    
    def disconnect(self):
        """Disconnect from IBKR and clean up"""
        self._live_feed.disconnect()
        logger.info("Live data feed disconnected")
    
    # Helper methods
    
    def _convert_interval_to_bar_size(self, interval: str) -> str:
        """
        Convert backtest interval format to IBKR bar size format.
        
        Args:
            interval: Backtest interval (e.g., '1d', '1h', '5m')
            
        Returns:
            IBKR bar size string (e.g., '1 day', '1 hour', '5 mins')
        """
        # Map common interval formats
        interval_map = {
            '1m': '1 min',
            '5m': '5 mins',
            '15m': '15 mins',
            '30m': '30 mins',
            '1h': '1 hour',
            '1d': '1 day',
            '1w': '1 week',
            '1M': '1 month',
        }
        
        return interval_map.get(interval, '1 day')
    
    def _calculate_duration(
        self,
        start_date: Optional[datetime],
        end_date: Optional[datetime]
    ) -> str:
        """
        Calculate IBKR duration string from date range.
        
        Args:
            start_date: Start date
            end_date: End date (default: now)
            
        Returns:
            IBKR duration string (e.g., '1 M', '1 Y', '5 D')
        """
        if start_date is None:
            # Default to 1 month
            return '1 M'
        
        end = end_date or datetime.now()
        delta = end - start_date
        
        # Convert to IBKR duration format
        if delta.days >= 365:
            years = delta.days // 365
            return f'{years} Y'
        elif delta.days >= 30:
            months = delta.days // 30
            return f'{months} M'
        elif delta.days >= 7:
            weeks = delta.days // 7
            return f'{weeks} W'
        else:
            return f'{delta.days} D'
    
    def _normalize_for_backtest(self, df: pd.DataFrame, symbol: str) -> pd.DataFrame:
        """
        Normalize data format to match backtest expectations.
        
        Args:
            df: Raw DataFrame from IBKR
            symbol: Ticker symbol
            
        Returns:
            Normalized DataFrame with proper column names and index
        """
        if df.empty:
            return df
        
        # Ensure standard column names (capitalized)
        column_map = {
            'open': 'Open',
            'high': 'High',
            'low': 'Low',
            'close': 'Close',
            'volume': 'Volume'
        }
        
        df = df.rename(columns=column_map)
        
        # Ensure DatetimeIndex
        if not isinstance(df.index, pd.DatetimeIndex):
            if 'date' in df.columns:
                df = df.set_index('date')
            elif 'time' in df.columns:
                df = df.set_index('time')
        
        # Remove symbol column if present (not needed for single-symbol data)
        if 'symbol' in df.columns:
            df = df.drop(columns=['symbol'])
        
        return df
    
    def _update_cache(self, symbol: str, df: pd.DataFrame):
        """
        Update the bar cache for a symbol.
        
        Args:
            symbol: Ticker symbol
            df: DataFrame of bars to cache
        """
        if not self.enable_cache:
            return
        
        # Limit cache size
        if len(df) > self.cache_size:
            df = df.tail(self.cache_size)
        
        self._bar_cache[symbol] = df.copy()
    
    def get_cached_data(self, symbol: str) -> Optional[pd.DataFrame]:
        """
        Get cached bar data for a symbol.
        
        Args:
            symbol: Ticker symbol
            
        Returns:
            Cached DataFrame or None
        """
        return self._bar_cache.get(symbol)
    
    def clear_cache(self, symbol: Optional[str] = None):
        """
        Clear cached data.
        
        Args:
            symbol: If specified, clear only this symbol's cache.
                   If None, clear all cached data.
        """
        if symbol:
            if symbol in self._bar_cache:
                del self._bar_cache[symbol]
        else:
            self._bar_cache.clear()
    
    def is_fallback_mode(self) -> bool:
        """
        Check if adapter is in fallback mode (using cached data).
        
        Returns:
            True if in fallback mode, False otherwise
        """
        return self._is_fallback_mode
    
    def __enter__(self):
        """Context manager entry"""
        self.connect()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.disconnect()
        return False
