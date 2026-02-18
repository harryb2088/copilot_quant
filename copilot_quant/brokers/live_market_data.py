"""
Live Market Data Feed via Interactive Brokers

This module provides real-time market data streaming and historical data
downloading through the Interactive Brokers API using ib_insync.

Features:
- Real-time price streaming for user-selected symbols
- Historical bar data download for backfilling
- Data normalization to match internal format
- Subscription/unsubscription management
- Automatic reconnection handling
- Streaming updates (tick/price/volume)
- Comprehensive logging and error handling

Example Usage:
    # Initialize the live data feed
    >>> data_feed = IBKRLiveDataFeed(paper_trading=True)
    >>> if data_feed.connect():
    ...     # Subscribe to real-time data
    ...     data_feed.subscribe(['AAPL', 'MSFT', 'GOOGL'])
    ...     
    ...     # Get historical data for backfilling
    ...     hist_data = data_feed.get_historical_bars('AAPL', duration='1 M', bar_size='1 day')
    ...     
    ...     # Get latest price
    ...     price = data_feed.get_latest_price('AAPL')
    ...     
    ...     # Unsubscribe
    ...     data_feed.unsubscribe(['AAPL'])
    ...     data_feed.disconnect()

Port Configuration:
- Paper Trading (TWS): 7497
- Live Trading (TWS): 7496
- Paper Trading (IB Gateway): 4002
- Live Trading (IB Gateway): 4001
"""

import logging
import os
import time
from datetime import datetime
from typing import Dict, List, Optional, Callable, Any
from collections import defaultdict
import pandas as pd

try:
    from ib_insync import IB, Stock, util
except ImportError as e:
    raise ImportError(
        "ib_insync is required for IBKR live data feed. "
        "Install it with: pip install ib_insync>=0.9.86"
    ) from e

from .connection_manager import IBKRConnectionManager
from copilot_quant.data.normalization import (
    normalize_symbol,
    standardize_column_names,
    normalize_timestamps,
    validate_data_quality
)

logger = logging.getLogger(__name__)


class IBKRLiveDataFeed:
    """
    Live market data feed using Interactive Brokers API.
    
    This class provides real-time streaming market data and historical data
    downloading capabilities through IBKR's TWS or IB Gateway.
    
    The data feed handles:
    - Real-time price subscriptions
    - Historical bar data downloads
    - Data normalization to internal format
    - Connection management and reconnection
    - Error handling and logging
    
    Example:
        >>> feed = IBKRLiveDataFeed(paper_trading=True)
        >>> feed.connect()
        >>> feed.subscribe(['AAPL', 'MSFT'])
        >>> price = feed.get_latest_price('AAPL')
        >>> feed.disconnect()
    """
    
    def __init__(
        self,
        paper_trading: bool = True,
        host: Optional[str] = None,
        port: Optional[int] = None,
        client_id: Optional[int] = None,
        use_gateway: bool = False
    ):
        """
        Initialize the live market data feed.
        
        Args:
            paper_trading: If True, connect to paper trading account
            host: IB API host address (default: from IB_HOST env or '127.0.0.1')
            port: IB API port (default: auto-detected based on mode)
            client_id: Unique client identifier (default: from IB_CLIENT_ID env or 1)
            use_gateway: If True, use IB Gateway ports, else use TWS ports
        """
        # Use connection manager to handle all connection logic
        self.connection_manager = IBKRConnectionManager(
            paper_trading=paper_trading,
            host=host,
            port=port,
            client_id=client_id,
            use_gateway=use_gateway,
            auto_reconnect=True
        )
        
        # Convenience properties
        self.paper_trading = paper_trading
        self.use_gateway = use_gateway
        
        # Data tracking
        self._subscriptions: Dict[str, Any] = {}  # symbol -> contract mapping
        self._latest_data: Dict[str, Dict[str, Any]] = defaultdict(dict)  # symbol -> data
        self._callbacks: Dict[str, List[Callable]] = defaultdict(list)  # symbol -> callbacks
        
        # Setup custom event handlers (in addition to connection manager's handlers)
        self.connection_manager.add_disconnect_handler(self._on_custom_disconnect)
        
        logger.info(
            f"Initialized IBKRLiveDataFeed: "
            f"mode={'Paper' if paper_trading else 'Live'}, "
            f"app={'Gateway' if use_gateway else 'TWS'}"
        )
    
    def connect(self, timeout: int = 30, retry_count: int = 3) -> bool:
        """
        Establish connection to IBKR.
        
        Args:
            timeout: Connection timeout in seconds
            retry_count: Number of connection retry attempts
            
        Returns:
            True if connection successful, False otherwise
        """
        try:
            return self.connection_manager.connect(timeout=timeout, retry_count=retry_count)
        except ConnectionError:
            return False
    
    def is_connected(self) -> bool:
        """Check if currently connected to IBKR"""
        return self.connection_manager.is_connected()
    
    @property
    def ib(self) -> IB:
        """Get the underlying IB instance"""
        return self.connection_manager.get_ib()
    
    def subscribe(
        self,
        symbols: List[str],
        callback: Optional[Callable[[str, Dict], None]] = None
    ) -> Dict[str, bool]:
        """
        Subscribe to real-time market data for symbols.
        
        Args:
            symbols: List of ticker symbols to subscribe to
            callback: Optional callback function(symbol, data) called on updates
            
        Returns:
            Dictionary mapping symbols to subscription success status
            
        Example:
            >>> def on_update(symbol, data):
            ...     print(f"{symbol}: ${data.get('last', 'N/A')}")
            >>> feed.subscribe(['AAPL', 'MSFT'], callback=on_update)
        """
        if not self.is_connected():
            logger.error("Not connected to IBKR. Call connect() first.")
            return {symbol: False for symbol in symbols}
        
        results = {}
        
        for symbol in symbols:
            try:
                # Normalize symbol for IBKR
                ib_symbol = normalize_symbol(symbol, source='ib')
                
                # Create contract
                contract = Stock(ib_symbol, 'SMART', 'USD')
                
                # Qualify contract to get full details
                qualified = self.ib.qualifyContracts(contract)
                if not qualified:
                    logger.warning(f"Failed to qualify contract for {symbol}")
                    results[symbol] = False
                    continue
                
                contract = qualified[0]
                
                # Request market data (streaming)
                ticker = self.ib.reqMktData(contract, '', False, False)
                
                # Setup update callback
                ticker.updateEvent += lambda t, sym=symbol: self._on_ticker_update(sym, t)
                
                # Store subscription
                self._subscriptions[symbol] = contract
                
                # Store callback if provided
                if callback:
                    self._callbacks[symbol].append(callback)
                
                logger.info(f"✓ Subscribed to real-time data for {symbol}")
                results[symbol] = True
                
            except Exception as e:
                logger.error(f"Failed to subscribe to {symbol}: {e}")
                results[symbol] = False
        
        return results
    
    def unsubscribe(self, symbols: List[str]) -> Dict[str, bool]:
        """
        Unsubscribe from real-time market data.
        
        Args:
            symbols: List of ticker symbols to unsubscribe from
            
        Returns:
            Dictionary mapping symbols to unsubscription success status
        """
        if not self.is_connected():
            logger.warning("Not connected to IBKR")
            return {symbol: False for symbol in symbols}
        
        results = {}
        
        for symbol in symbols:
            try:
                if symbol in self._subscriptions:
                    contract = self._subscriptions[symbol]
                    self.ib.cancelMktData(contract)
                    
                    # Clean up
                    del self._subscriptions[symbol]
                    if symbol in self._latest_data:
                        del self._latest_data[symbol]
                    if symbol in self._callbacks:
                        del self._callbacks[symbol]
                    
                    logger.info(f"✓ Unsubscribed from {symbol}")
                    results[symbol] = True
                else:
                    logger.warning(f"Not subscribed to {symbol}")
                    results[symbol] = False
                    
            except Exception as e:
                logger.error(f"Failed to unsubscribe from {symbol}: {e}")
                results[symbol] = False
        
        return results
    
    def get_latest_price(self, symbol: str) -> Optional[float]:
        """
        Get the latest price for a subscribed symbol.
        
        Args:
            symbol: Ticker symbol
            
        Returns:
            Latest price or None if not available
        """
        data = self._latest_data.get(symbol, {})
        return data.get('last') or data.get('close') or data.get('bid')
    
    def get_latest_data(self, symbol: str) -> Dict[str, Any]:
        """
        Get the latest market data for a subscribed symbol.
        
        Args:
            symbol: Ticker symbol
            
        Returns:
            Dictionary with latest market data (bid, ask, last, volume, etc.)
        """
        return self._latest_data.get(symbol, {}).copy()
    
    def get_historical_bars(
        self,
        symbol: str,
        duration: str = '1 M',
        bar_size: str = '1 day',
        what_to_show: str = 'TRADES',
        use_rth: bool = True
    ) -> Optional[pd.DataFrame]:
        """
        Download historical bar data for backfilling.
        
        Args:
            symbol: Ticker symbol
            duration: How far back to request (e.g., '1 M', '1 Y', '5 D')
            bar_size: Bar size (e.g., '1 min', '5 mins', '1 hour', '1 day')
            what_to_show: Data type ('TRADES', 'MIDPOINT', 'BID', 'ASK')
            use_rth: Use regular trading hours only
            
        Returns:
            DataFrame with OHLCV data normalized to internal format, or None on error
            
        Example:
            >>> # Get 1 month of daily bars
            >>> df = feed.get_historical_bars('AAPL', duration='1 M', bar_size='1 day')
            >>> 
            >>> # Get 5 days of 5-minute bars
            >>> df = feed.get_historical_bars('AAPL', duration='5 D', bar_size='5 mins')
        """
        if not self.is_connected():
            logger.error("Not connected to IBKR")
            return None
        
        try:
            # Normalize symbol for IBKR
            ib_symbol = normalize_symbol(symbol, source='ib')
            
            # Create and qualify contract
            contract = Stock(ib_symbol, 'SMART', 'USD')
            qualified = self.ib.qualifyContracts(contract)
            
            if not qualified:
                logger.error(f"Failed to qualify contract for {symbol}")
                return None
            
            contract = qualified[0]
            
            # Request historical data
            logger.info(
                f"Requesting historical data for {symbol}: "
                f"duration={duration}, bar_size={bar_size}"
            )
            
            bars = self.ib.reqHistoricalData(
                contract,
                endDateTime='',  # Current time
                durationStr=duration,
                barSizeSetting=bar_size,
                whatToShow=what_to_show,
                useRTH=use_rth,
                formatDate=1  # Return as datetime objects
            )
            
            if not bars:
                logger.warning(f"No historical data returned for {symbol}")
                return None
            
            # Convert to DataFrame
            df = util.df(bars)
            
            # Normalize data to internal format
            df = self._normalize_historical_data(df, symbol)
            
            logger.info(f"✓ Retrieved {len(df)} bars for {symbol}")
            return df
            
        except Exception as e:
            logger.error(f"Failed to get historical data for {symbol}: {e}")
            return None
    
    def _normalize_historical_data(
        self,
        df: pd.DataFrame,
        symbol: str
    ) -> pd.DataFrame:
        """
        Normalize historical data to match internal format.
        
        Args:
            df: Raw DataFrame from IBKR
            symbol: Ticker symbol
            
        Returns:
            Normalized DataFrame
        """
        if df.empty:
            return df
        
        # Standardize column names (lowercase with underscores)
        df = standardize_column_names(df)
        
        # Ensure 'date' column exists
        if 'date' not in df.columns:
            if isinstance(df.index, pd.DatetimeIndex):
                df = df.reset_index()
                df.rename(columns={'index': 'date'}, inplace=True)
        
        # Normalize timestamps to NYSE timezone for equities
        df = normalize_timestamps(df, market_type='equity')
        
        # Add symbol column
        df['symbol'] = symbol
        
        # Validate data quality
        errors = validate_data_quality(df)
        if errors:
            logger.warning(f"Data quality issues for {symbol}: {errors}")
        
        # Set date as index
        if 'date' in df.columns:
            df.set_index('date', inplace=True)
        
        return df
    
    def _on_ticker_update(self, symbol: str, ticker: Any):
        """
        Handle real-time ticker updates.
        
        Args:
            symbol: Ticker symbol
            ticker: Ticker object from ib_insync
        """
        try:
            # Extract data from ticker
            data = {
                'symbol': symbol,
                'time': ticker.time or datetime.now(),
                'bid': float(ticker.bid) if ticker.bid and ticker.bid > 0 else None,
                'ask': float(ticker.ask) if ticker.ask and ticker.ask > 0 else None,
                'last': float(ticker.last) if ticker.last and ticker.last > 0 else None,
                'close': float(ticker.close) if ticker.close and ticker.close > 0 else None,
                'volume': int(ticker.volume) if ticker.volume else None,
                'bid_size': int(ticker.bidSize) if ticker.bidSize else None,
                'ask_size': int(ticker.askSize) if ticker.askSize else None,
                'high': float(ticker.high) if ticker.high and ticker.high > 0 else None,
                'low': float(ticker.low) if ticker.low and ticker.low > 0 else None,
                'open': float(ticker.open) if ticker.open and ticker.open > 0 else None,
            }
            
            # Update latest data
            self._latest_data[symbol].update(data)
            
            # Call registered callbacks
            for callback in self._callbacks.get(symbol, []):
                try:
                    callback(symbol, data)
                except Exception as e:
                    logger.error(f"Error in callback for {symbol}: {e}")
        
        except Exception as e:
            logger.error(f"Error processing ticker update for {symbol}: {e}")
    
    def _on_custom_disconnect(self):
        """Handle disconnection event - clean up subscriptions"""
        logger.warning("Disconnected from IBKR - clearing subscriptions")
        
        # Clear subscriptions
        self._subscriptions.clear()
        self._latest_data.clear()
    
    def reconnect(self, timeout: int = 30) -> bool:
        """
        Attempt to reconnect to IBKR and resubscribe to symbols.
        
        Args:
            timeout: Connection timeout in seconds
            
        Returns:
            True if reconnection successful, False otherwise
        """
        logger.info("Attempting to reconnect to IBKR...")
        
        # Store current subscriptions
        symbols_to_resubscribe = list(self._subscriptions.keys())
        callbacks_to_restore = {sym: cbs[:] for sym, cbs in self._callbacks.items()}
        
        # Use connection manager to reconnect
        if not self.connection_manager.reconnect(timeout=timeout):
            logger.error("Reconnection failed")
            return False
        
        # Resubscribe to symbols
        if symbols_to_resubscribe:
            logger.info(f"Resubscribing to {len(symbols_to_resubscribe)} symbols...")
            results = self.subscribe(symbols_to_resubscribe)
            
            # Restore callbacks
            for symbol, callbacks in callbacks_to_restore.items():
                if results.get(symbol):
                    self._callbacks[symbol] = callbacks
            
            success_count = sum(1 for success in results.values() if success)
            logger.info(f"Resubscribed to {success_count}/{len(symbols_to_resubscribe)} symbols")
        
        logger.info("✓ Reconnection successful")
        return True
    
    def disconnect(self):
        """Disconnect from IBKR and clean up"""
        if self.is_connected():
            # Unsubscribe from all symbols
            if self._subscriptions:
                symbols = list(self._subscriptions.keys())
                self.unsubscribe(symbols)
            
            self.connection_manager.disconnect()
    
    def get_subscribed_symbols(self) -> List[str]:
        """
        Get list of currently subscribed symbols.
        
        Returns:
            List of subscribed ticker symbols
        """
        return list(self._subscriptions.keys())
    
    def __enter__(self):
        """Context manager entry"""
        self.connect()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.disconnect()
        return False
