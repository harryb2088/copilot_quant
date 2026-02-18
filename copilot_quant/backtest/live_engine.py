"""
Live Strategy Engine for Real-Time Trading

This module provides a strategy engine that can execute trading strategies
in live mode using real-time data from IBKR, while maintaining compatibility
with the backtest engine interface.

Features:
- Execute strategies in real-time with live market data
- Seamless integration with backtest-compatible strategies
- Automatic reconnection on disconnection
- Position and order tracking
- Performance monitoring
- Error handling and logging

Example Usage:
    >>> from copilot_quant.backtest.live_engine import LiveStrategyEngine
    >>> from my_strategies import MyStrategy
    >>> 
    >>> # Initialize live engine
    >>> engine = LiveStrategyEngine(
    ...     paper_trading=True,
    ...     commission=0.001,
    ...     slippage=0.0005
    ... )
    >>> 
    >>> # Add strategy
    >>> engine.add_strategy(MyStrategy())
    >>> 
    >>> # Connect and start
    >>> if engine.connect():
    ...     # Start live trading
    ...     engine.start(symbols=['AAPL', 'MSFT'])
    ...     
    ...     # Run for a while...
    ...     time.sleep(3600)  # 1 hour
    ...     
    ...     # Stop and disconnect
    ...     engine.stop()
    ...     engine.disconnect()
"""

import logging
import threading
import time
from datetime import datetime
from typing import Dict, List, Optional
from collections import defaultdict

import pandas as pd

from copilot_quant.backtest.strategy import Strategy
from copilot_quant.backtest.orders import Fill, Order
from copilot_quant.brokers.live_data_adapter import LiveDataFeedAdapter
from copilot_quant.brokers.live_broker_adapter import LiveBrokerAdapter

logger = logging.getLogger(__name__)


class LiveStrategyEngine:
    """
    Live strategy execution engine with real-time market data.
    
    This engine runs strategies in live mode, processing real-time market
    data from IBKR and executing orders through the live broker. It maintains
    compatibility with the backtest engine interface, allowing strategies
    designed for backtesting to run in live mode with minimal changes.
    
    Features:
    - Real-time data processing
    - Automatic reconnection on disconnection
    - Position and order tracking
    - Performance monitoring
    - Error handling and recovery
    - Graceful shutdown
    
    Example:
        >>> engine = LiveStrategyEngine(paper_trading=True)
        >>> engine.add_strategy(MyStrategy())
        >>> engine.connect()
        >>> engine.start(symbols=['AAPL'])
        >>> # ... engine runs ...
        >>> engine.stop()
        >>> engine.disconnect()
    """
    
    def __init__(
        self,
        paper_trading: bool = True,
        host: Optional[str] = None,
        port: Optional[int] = None,
        client_id: Optional[int] = None,
        use_gateway: bool = False,
        commission: float = 0.001,
        slippage: float = 0.0005,
        update_interval: float = 1.0,
        enable_reconnect: bool = True
    ):
        """
        Initialize live strategy engine.
        
        Args:
            paper_trading: If True, use paper trading account
            host: IB API host address
            port: IB API port
            client_id: Unique client identifier
            use_gateway: If True, use IB Gateway, else TWS
            commission: Commission rate as decimal (e.g., 0.001 = 0.1%)
            slippage: Slippage rate as decimal (e.g., 0.0005 = 0.05%)
            update_interval: How often to call strategy (in seconds)
            enable_reconnect: If True, automatically reconnect on disconnection
        """
        # Initialize adapters
        self.data_feed = LiveDataFeedAdapter(
            paper_trading=paper_trading,
            host=host,
            port=port,
            client_id=client_id,
            use_gateway=use_gateway,
            enable_cache=True,
            cache_size=1000
        )
        
        self.broker = LiveBrokerAdapter(
            paper_trading=paper_trading,
            host=host,
            port=port,
            client_id=client_id,
            use_gateway=use_gateway,
            commission_rate=commission,
            slippage_rate=slippage,
            enable_position_tracking=True
        )
        
        # Configuration
        self.update_interval = update_interval
        self.enable_reconnect = enable_reconnect
        
        # Engine state
        self.strategy: Optional[Strategy] = None
        self.symbols: List[str] = []
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        
        # Data tracking
        self._historical_data: Dict[str, pd.DataFrame] = {}
        self._latest_data: Dict[str, pd.Series] = {}
        
        # Performance tracking
        self.fills: List[Fill] = []
        self.errors: List[Dict] = []
        
        logger.info(
            f"LiveStrategyEngine initialized: "
            f"mode={'Paper' if paper_trading else 'Live'}, "
            f"update_interval={update_interval}s"
        )
    
    def add_strategy(self, strategy: Strategy) -> None:
        """
        Register a trading strategy.
        
        Args:
            strategy: Strategy instance to run
        """
        self.strategy = strategy
        logger.info(f"Added strategy: {strategy.name}")
    
    def connect(self, timeout: int = 30, retry_count: int = 3) -> bool:
        """
        Establish connections to IBKR for both data and execution.
        
        Args:
            timeout: Connection timeout in seconds
            retry_count: Number of retry attempts
            
        Returns:
            True if both connections successful, False otherwise
        """
        logger.info("Connecting to IBKR...")
        
        # Connect data feed
        if not self.data_feed.connect(timeout=timeout, retry_count=retry_count):
            logger.error("Failed to connect data feed")
            return False
        
        logger.info("✓ Data feed connected")
        
        # Connect broker
        if not self.broker.connect(timeout=timeout, retry_count=retry_count):
            logger.error("Failed to connect broker")
            self.data_feed.disconnect()
            return False
        
        logger.info("✓ Broker connected")
        logger.info("✓ Live engine connected successfully")
        
        return True
    
    def is_connected(self) -> bool:
        """
        Check if engine is connected.
        
        Returns:
            True if both data feed and broker are connected
        """
        return self.data_feed.is_connected() and self.broker.is_connected()
    
    def start(
        self,
        symbols: List[str],
        lookback_days: int = 30,
        data_interval: str = '1d'
    ) -> bool:
        """
        Start live strategy execution.
        
        Args:
            symbols: List of symbols to trade
            lookback_days: Days of historical data to load initially
            data_interval: Data interval for historical data
            
        Returns:
            True if started successfully, False otherwise
        """
        if self.strategy is None:
            logger.error("No strategy registered. Call add_strategy() first.")
            return False
        
        if not self.is_connected():
            logger.error("Not connected. Call connect() first.")
            return False
        
        if self._running:
            logger.warning("Engine already running")
            return False
        
        self.symbols = symbols
        logger.info(f"Starting live engine with symbols: {symbols}")
        
        try:
            # Load historical data for context
            self._load_historical_data(symbols, lookback_days, data_interval)
            
            # Subscribe to real-time data
            results = self.data_feed.subscribe(symbols)
            failed_subs = [s for s, success in results.items() if not success]
            if failed_subs:
                logger.warning(f"Failed to subscribe to: {failed_subs}")
            
            # Initialize strategy
            logger.info("Initializing strategy...")
            self.strategy.initialize()
            
            # Start execution thread
            self._running = True
            self._stop_event.clear()
            self._thread = threading.Thread(target=self._run_loop, daemon=True)
            self._thread.start()
            
            logger.info("✓ Live engine started successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error starting live engine: {e}", exc_info=True)
            self._running = False
            return False
    
    def stop(self) -> None:
        """
        Stop live strategy execution.
        
        Gracefully stops the execution loop and finalizes the strategy.
        """
        if not self._running:
            logger.warning("Engine not running")
            return
        
        logger.info("Stopping live engine...")
        
        # Signal stop
        self._running = False
        self._stop_event.set()
        
        # Wait for thread to finish
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=10)
        
        # Unsubscribe from data
        if self.symbols:
            self.data_feed.unsubscribe(self.symbols)
        
        # Finalize strategy
        if self.strategy:
            try:
                self.strategy.finalize()
            except Exception as e:
                logger.error(f"Error finalizing strategy: {e}")
        
        logger.info("✓ Live engine stopped")
    
    def disconnect(self) -> None:
        """
        Disconnect from IBKR.
        
        Closes connections to both data feed and broker.
        """
        logger.info("Disconnecting from IBKR...")
        
        # Stop engine if running
        if self._running:
            self.stop()
        
        # Disconnect
        self.data_feed.disconnect()
        self.broker.disconnect()
        
        logger.info("✓ Disconnected from IBKR")
    
    def _run_loop(self) -> None:
        """
        Main execution loop running in separate thread.
        
        This loop:
        1. Checks connection status
        2. Updates market data
        3. Calls strategy.on_data()
        4. Executes generated orders
        5. Handles errors and reconnection
        """
        logger.info("Execution loop started")
        
        while self._running and not self._stop_event.is_set():
            try:
                # Check connection
                if not self.is_connected():
                    logger.warning("Lost connection to IBKR")
                    
                    if self.enable_reconnect:
                        logger.info("Attempting to reconnect...")
                        if self._reconnect():
                            logger.info("✓ Reconnected successfully")
                        else:
                            logger.error("Reconnection failed - stopping engine")
                            self._running = False
                            break
                    else:
                        logger.error("Reconnection disabled - stopping engine")
                        self._running = False
                        break
                
                # Update market data
                self._update_market_data()
                
                # Prepare data for strategy
                current_data = self._prepare_strategy_data()
                
                if current_data is None or current_data.empty:
                    logger.debug("No data available for strategy")
                    time.sleep(self.update_interval)
                    continue
                
                # Call strategy
                timestamp = datetime.now()
                orders = self.strategy.on_data(timestamp, current_data)
                
                if orders is None:
                    orders = []
                
                # Execute orders
                for order in orders:
                    self._execute_order(order, timestamp)
                
                # Sleep until next update
                time.sleep(self.update_interval)
                
            except Exception as e:
                logger.error(f"Error in execution loop: {e}", exc_info=True)
                self.errors.append({
                    'timestamp': datetime.now(),
                    'error': str(e),
                    'type': type(e).__name__
                })
                
                # Sleep before retry
                time.sleep(self.update_interval)
        
        logger.info("Execution loop ended")
    
    def _load_historical_data(
        self,
        symbols: List[str],
        lookback_days: int,
        interval: str
    ) -> None:
        """
        Load historical data for symbols.
        
        Args:
            symbols: List of symbols
            lookback_days: Days of history to load
            interval: Data interval
        """
        logger.info(f"Loading {lookback_days} days of historical data...")
        
        start_date = datetime.now() - pd.Timedelta(days=lookback_days)
        end_date = datetime.now()
        
        for symbol in symbols:
            try:
                df = self.data_feed.get_historical_data(
                    symbol=symbol,
                    start_date=start_date,
                    end_date=end_date,
                    interval=interval
                )
                
                if not df.empty:
                    self._historical_data[symbol] = df
                    logger.info(f"✓ Loaded {len(df)} bars for {symbol}")
                else:
                    logger.warning(f"No historical data for {symbol}")
                    
            except Exception as e:
                logger.error(f"Error loading historical data for {symbol}: {e}")
    
    def _update_market_data(self) -> None:
        """
        Update latest market data for all subscribed symbols.
        """
        for symbol in self.symbols:
            try:
                latest_bar = self.data_feed.get_latest_bar(symbol)
                
                if latest_bar is not None:
                    self._latest_data[symbol] = latest_bar
                    
            except Exception as e:
                logger.error(f"Error updating data for {symbol}: {e}")
    
    def _prepare_strategy_data(self) -> Optional[pd.DataFrame]:
        """
        Prepare data in format expected by strategy.
        
        Combines historical data with latest real-time data.
        
        Returns:
            DataFrame with all available data, or None if no data
        """
        if not self._historical_data and not self._latest_data:
            return None
        
        # For now, return historical data
        # TODO: Append latest real-time bars to historical data
        
        if len(self.symbols) == 1:
            # Single symbol - return DataFrame for that symbol
            symbol = self.symbols[0]
            if symbol in self._historical_data:
                return self._historical_data[symbol].copy()
        else:
            # Multiple symbols - combine into multi-column DataFrame
            combined = {}
            for symbol in self.symbols:
                if symbol in self._historical_data:
                    combined[symbol] = self._historical_data[symbol]
            
            if combined:
                return pd.concat(combined, axis=1)
        
        return None
    
    def _execute_order(self, order: Order, timestamp: datetime) -> None:
        """
        Execute an order through the live broker.
        
        Args:
            order: Order to execute
            timestamp: Current timestamp
        """
        try:
            # Get current price
            current_price = self.data_feed.get_latest_price(order.symbol)
            
            if current_price is None:
                logger.warning(f"Cannot execute order - no price for {order.symbol}")
                return
            
            # Execute through broker adapter
            fill = self.broker.execute_order(order, current_price, timestamp)
            
            if fill:
                # Record fill
                self.fills.append(fill)
                
                # Notify strategy
                try:
                    self.strategy.on_fill(fill)
                except Exception as e:
                    logger.error(f"Error in strategy.on_fill(): {e}")
                
                logger.info(
                    f"✓ Order filled: {order.side} {order.quantity} {order.symbol} "
                    f"@ ${fill.fill_price:.2f}"
                )
            else:
                logger.warning(f"Order not filled: {order}")
                
        except Exception as e:
            logger.error(f"Error executing order: {e}", exc_info=True)
    
    def _reconnect(self) -> bool:
        """
        Attempt to reconnect to IBKR.
        
        Returns:
            True if reconnection successful, False otherwise
        """
        try:
            # Reconnect data feed
            if not self.data_feed.is_connected():
                if not self.data_feed.reconnect():
                    return False
            
            # Reconnect broker
            if not self.broker.is_connected():
                if not self.broker.connect():
                    return False
            
            # Resubscribe to data
            if self.symbols:
                self.data_feed.subscribe(self.symbols)
            
            return True
            
        except Exception as e:
            logger.error(f"Error during reconnection: {e}")
            return False
    
    def get_positions(self) -> Dict:
        """
        Get current positions.
        
        Returns:
            Dictionary of positions
        """
        return self.broker.get_positions()
    
    def get_account_value(self) -> float:
        """
        Get total account value.
        
        Returns:
            Account value in dollars
        """
        return self.broker.get_account_value()
    
    def get_cash_balance(self) -> float:
        """
        Get cash balance.
        
        Returns:
            Cash balance in dollars
        """
        return self.broker.get_cash_balance()
    
    def get_performance_summary(self) -> Dict:
        """
        Get performance summary.
        
        Returns:
            Dictionary with performance metrics
        """
        return {
            'total_fills': len(self.fills),
            'total_errors': len(self.errors),
            'account_value': self.get_account_value(),
            'cash_balance': self.get_cash_balance(),
            'positions': len(self.get_positions()),
            'is_running': self._running,
            'is_connected': self.is_connected()
        }
    
    def __enter__(self):
        """Context manager entry"""
        self.connect()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.disconnect()
        return False
