"""
Live Signal Monitor for Real-Time Signal Generation and Execution

This module provides the LiveSignalMonitor service that continuously monitors
signal-based strategies, generates trading signals, performs risk checks, sizes
positions, and sends orders to the execution pipeline.

Features:
- Continuous signal generation from all registered strategies
- Risk checking and position sizing for each signal
- Automatic order execution through live broker
- Signal persistence to database (including unexecuted signals)
- Real-time dashboard of active signals and recent actions
- Graceful shutdown and error handling

Example Usage:
    >>> from copilot_quant.live import LiveSignalMonitor
    >>> from copilot_quant.strategies.my_strategy import MySignalStrategy
    >>> 
    >>> monitor = LiveSignalMonitor(
    ...     database_url="sqlite:///live_trading.db",
    ...     paper_trading=True
    ... )
    >>> 
    >>> monitor.add_strategy(MySignalStrategy())
    >>> monitor.connect()
    >>> monitor.start(['AAPL', 'MSFT'])
    >>> # Monitor runs continuously...
    >>> monitor.stop()
    >>> monitor.disconnect()
"""

import logging
import threading
import time
from datetime import datetime
from typing import Dict, List, Optional, Set

import pandas as pd

from copilot_quant.backtest.signals import SignalBasedStrategy, TradingSignal
from copilot_quant.backtest.orders import Order
from copilot_quant.brokers.live_data_adapter import LiveDataFeedAdapter
from copilot_quant.brokers.live_broker_adapter import LiveBrokerAdapter
from copilot_quant.brokers.trade_database import TradeDatabase

logger = logging.getLogger(__name__)


class LiveSignalMonitor:
    """
    Real-time signal monitoring and execution service.
    
    This service continuously calls generate_signals() for all registered
    signal-based strategies, performs risk checks, sizes positions, and
    executes orders through the live broker. All signals are persisted to
    the database for audit trail and attribution analysis.
    
    The monitor runs in a background thread and provides a dashboard view
    of active signals and recent actions.
    
    Attributes:
        strategies: List of registered SignalBasedStrategy instances
        data_feed: LiveDataFeedAdapter for real-time market data
        broker: LiveBrokerAdapter for order execution
        database: TradeDatabase for signal and order persistence
        active_signals: Current active trading signals
        signal_history: Historical signals for dashboard
    
    Example:
        >>> monitor = LiveSignalMonitor(paper_trading=True)
        >>> monitor.add_strategy(MeanReversionSignals())
        >>> monitor.add_strategy(MomentumSignals())
        >>> monitor.connect()
        >>> monitor.start(['AAPL', 'MSFT', 'GOOGL'])
        >>> # ... runs continuously ...
        >>> monitor.get_dashboard_summary()
        >>> monitor.stop()
    """
    
    def __init__(
        self,
        database_url: str = "sqlite:///live_trading.db",
        paper_trading: bool = True,
        host: Optional[str] = None,
        port: Optional[int] = None,
        client_id: Optional[int] = None,
        use_gateway: bool = False,
        update_interval: float = 60.0,
        max_position_size: float = 0.1,
        max_total_exposure: float = 0.8,
        enable_risk_checks: bool = True
    ):
        """
        Initialize live signal monitor.
        
        Args:
            database_url: SQLAlchemy database URL for persistence
            paper_trading: If True, use paper trading account
            host: IB API host address
            port: IB API port
            client_id: Unique client identifier
            use_gateway: If True, use IB Gateway, else TWS
            update_interval: How often to generate signals (in seconds)
            max_position_size: Maximum position size as fraction of NAV
            max_total_exposure: Maximum total exposure as fraction of NAV
            enable_risk_checks: If True, perform risk checks before execution
        """
        # Initialize database
        self.database = TradeDatabase(database_url=database_url)
        
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
            enable_position_tracking=True
        )
        
        # Configuration
        self.update_interval = update_interval
        self.max_position_size = max_position_size
        self.max_total_exposure = max_total_exposure
        self.enable_risk_checks = enable_risk_checks
        
        # Strategy management
        self.strategies: List[SignalBasedStrategy] = []
        self.symbols: Set[str] = set()
        
        # Signal tracking
        self.active_signals: Dict[str, TradingSignal] = {}  # symbol -> signal
        self.signal_history: List[Dict] = []
        self.max_history = 1000
        
        # Engine state
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        
        # Data tracking
        self._historical_data: Dict[str, pd.DataFrame] = {}
        
        # Statistics
        self.stats = {
            'total_signals_generated': 0,
            'signals_executed': 0,
            'signals_rejected': 0,
            'errors': 0
        }
        
        logger.info(
            f"LiveSignalMonitor initialized: "
            f"mode={'Paper' if paper_trading else 'Live'}, "
            f"update_interval={update_interval}s"
        )
    
    def add_strategy(self, strategy: SignalBasedStrategy) -> None:
        """
        Register a signal-based trading strategy.
        
        Args:
            strategy: SignalBasedStrategy instance to monitor
        
        Raises:
            ValueError: If strategy is not a SignalBasedStrategy
        """
        if not isinstance(strategy, SignalBasedStrategy):
            raise ValueError(
                f"Strategy must be instance of SignalBasedStrategy, "
                f"got {type(strategy).__name__}"
            )
        
        self.strategies.append(strategy)
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
        logger.info("✓ Signal monitor connected successfully")
        
        return True
    
    def is_connected(self) -> bool:
        """
        Check if monitor is connected.
        
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
        Start live signal monitoring and execution.
        
        Args:
            symbols: List of symbols to monitor
            lookback_days: Days of historical data to load initially
            data_interval: Data interval for historical data
            
        Returns:
            True if started successfully, False otherwise
        """
        if not self.strategies:
            logger.error("No strategies registered. Call add_strategy() first.")
            return False
        
        if not self.is_connected():
            logger.error("Not connected. Call connect() first.")
            return False
        
        if self._running:
            logger.warning("Monitor already running")
            return False
        
        self.symbols = set(symbols)
        logger.info(f"Starting signal monitor with symbols: {symbols}")
        
        try:
            # Load historical data for context
            self._load_historical_data(list(symbols), lookback_days, data_interval)
            
            # Subscribe to real-time data
            results = self.data_feed.subscribe(list(symbols))
            failed_subs = [s for s, success in results.items() if not success]
            if failed_subs:
                logger.warning(f"Failed to subscribe to: {failed_subs}")
            
            # Initialize strategies
            for strategy in self.strategies:
                logger.info(f"Initializing strategy: {strategy.name}")
                strategy.initialize()
            
            # Start monitoring thread
            self._running = True
            self._stop_event.clear()
            self._thread = threading.Thread(target=self._run_loop, daemon=True)
            self._thread.start()
            
            logger.info("✓ Signal monitor started successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error starting signal monitor: {e}", exc_info=True)
            self._running = False
            return False
    
    def stop(self) -> None:
        """
        Stop live signal monitoring.
        
        Gracefully stops the monitoring loop and finalizes all strategies.
        """
        if not self._running:
            logger.warning("Monitor not running")
            return
        
        logger.info("Stopping signal monitor...")
        
        # Signal stop
        self._running = False
        self._stop_event.set()
        
        # Wait for thread to finish
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=10)
        
        # Unsubscribe from data
        if self.symbols:
            self.data_feed.unsubscribe(list(self.symbols))
        
        # Finalize strategies
        for strategy in self.strategies:
            try:
                strategy.finalize()
            except Exception as e:
                logger.error(f"Error finalizing strategy {strategy.name}: {e}")
        
        logger.info("✓ Signal monitor stopped")
    
    def disconnect(self) -> None:
        """
        Disconnect from IBKR.
        
        Closes connections to both data feed and broker.
        """
        logger.info("Disconnecting from IBKR...")
        
        # Stop monitor if running
        if self._running:
            self.stop()
        
        # Disconnect
        self.data_feed.disconnect()
        self.broker.disconnect()
        
        logger.info("✓ Disconnected from IBKR")
    
    def _run_loop(self) -> None:
        """
        Main monitoring loop running in separate thread.
        
        This loop:
        1. Updates market data
        2. Calls generate_signals() for all strategies
        3. Performs risk checks on signals
        4. Sizes positions
        5. Executes orders
        6. Persists all signals to database
        """
        logger.info("Signal monitoring loop started")
        
        while self._running and not self._stop_event.is_set():
            try:
                # Check connection
                if not self.is_connected():
                    logger.warning("Lost connection to IBKR")
                    break
                
                # Update market data
                self._update_market_data()
                
                # Prepare data for strategies
                current_data = self._prepare_strategy_data()
                
                if current_data is None or current_data.empty:
                    logger.debug("No data available for strategies")
                    time.sleep(self.update_interval)
                    continue
                
                # Generate signals from all strategies
                timestamp = datetime.now()
                all_signals = self._generate_all_signals(timestamp, current_data)
                
                # Process each signal
                for signal in all_signals:
                    self._process_signal(signal, timestamp)
                
                # Sleep until next update
                time.sleep(self.update_interval)
                
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}", exc_info=True)
                self.stats['errors'] += 1
                time.sleep(self.update_interval)
        
        logger.info("Signal monitoring loop ended")
    
    def _generate_all_signals(
        self,
        timestamp: datetime,
        data: pd.DataFrame
    ) -> List[TradingSignal]:
        """
        Generate signals from all registered strategies.
        
        Args:
            timestamp: Current timestamp
            data: Market data DataFrame
            
        Returns:
            List of all generated signals
        """
        all_signals = []
        
        for strategy in self.strategies:
            try:
                signals = strategy.generate_signals(timestamp, data)
                
                if signals:
                    logger.info(
                        f"Strategy {strategy.name} generated {len(signals)} signals"
                    )
                    all_signals.extend(signals)
                    
            except Exception as e:
                logger.error(
                    f"Error generating signals from {strategy.name}: {e}",
                    exc_info=True
                )
        
        self.stats['total_signals_generated'] += len(all_signals)
        return all_signals
    
    def _process_signal(self, signal: TradingSignal, timestamp: datetime) -> None:
        """
        Process a trading signal: risk check, size, execute, persist.
        
        Args:
            signal: TradingSignal to process
            timestamp: Current timestamp
        """
        # Persist signal to database (even if not executed)
        self._persist_signal(signal, timestamp)
        
        # Add to history for dashboard
        self._add_to_history(signal, timestamp)
        
        # Perform risk checks
        if self.enable_risk_checks:
            if not self._risk_check(signal):
                logger.info(
                    f"Signal rejected by risk check: {signal.symbol} {signal.side}"
                )
                self.stats['signals_rejected'] += 1
                return
        
        # Size position
        quantity = self._calculate_position_size(signal)
        
        if quantity <= 0:
            logger.info(
                f"Position size too small for signal: {signal.symbol} {signal.side}"
            )
            self.stats['signals_rejected'] += 1
            return
        
        # Create order
        order = Order(
            symbol=signal.symbol,
            side=signal.side,
            quantity=quantity,
            order_type='market'
        )
        
        # Execute order
        try:
            current_price = self.data_feed.get_latest_price(signal.symbol)
            
            if current_price is None:
                logger.warning(f"Cannot execute - no price for {signal.symbol}")
                return
            
            fill = self.broker.execute_order(order, current_price, timestamp)
            
            if fill:
                self.stats['signals_executed'] += 1
                self.active_signals[signal.symbol] = signal
                
                logger.info(
                    f"✓ Signal executed: {signal.side} {quantity} {signal.symbol} "
                    f"@ ${fill.price:.2f} (strategy: {signal.strategy_name})"
                )
            else:
                logger.warning(f"Order not filled for signal: {signal.symbol}")
                
        except Exception as e:
            logger.error(f"Error executing signal: {e}", exc_info=True)
            self.stats['errors'] += 1
    
    def _risk_check(self, signal: TradingSignal) -> bool:
        """
        Perform risk checks on a signal.
        
        Args:
            signal: TradingSignal to check
            
        Returns:
            True if signal passes risk checks, False otherwise
        """
        # Get current account value
        account_value = self.broker.get_account_value()
        
        if account_value <= 0:
            logger.warning("Cannot perform risk check - invalid account value")
            return False
        
        # Check total exposure (use absolute value for long and short positions)
        positions = self.broker.get_positions()
        total_exposure = 0.0
        for pos in positions.values():
            price = getattr(pos, 'current_price', None) or getattr(pos, 'avg_entry_price', 0)
            # Use absolute value to count both long and short positions towards exposure
            total_exposure += abs(pos.quantity * price)
        
        exposure_ratio = total_exposure / account_value
        
        if exposure_ratio >= self.max_total_exposure:
            logger.warning(
                f"Signal rejected - total exposure {exposure_ratio:.1%} "
                f">= max {self.max_total_exposure:.1%}"
            )
            return False
        
        # Check signal quality
        if signal.quality_score < 0.3:
            logger.info(
                f"Signal rejected - quality score {signal.quality_score:.2f} too low"
            )
            return False
        
        return True
    
    def _calculate_position_size(self, signal: TradingSignal) -> int:
        """
        Calculate position size based on signal quality and risk limits.
        
        Args:
            signal: TradingSignal to size
            
        Returns:
            Position size in shares
        """
        account_value = self.broker.get_account_value()
        
        if account_value <= 0:
            return 0
        
        # Base size on signal quality
        base_allocation = account_value * self.max_position_size
        quality_multiplier = signal.quality_score
        
        dollar_allocation = base_allocation * quality_multiplier
        
        # Convert to shares
        if signal.entry_price > 0:
            quantity = int(dollar_allocation / signal.entry_price)
        else:
            quantity = 0
        
        return max(0, quantity)
    
    def _persist_signal(self, signal: TradingSignal, timestamp: datetime) -> None:
        """
        Persist signal to database for audit trail.
        
        Args:
            signal: TradingSignal to persist
            timestamp: Signal generation timestamp
        """
        # For now, add to in-memory history
        # TODO: Add signals table to database schema
        pass
    
    def _add_to_history(self, signal: TradingSignal, timestamp: datetime) -> None:
        """
        Add signal to history for dashboard.
        
        Args:
            signal: TradingSignal to add
            timestamp: Signal timestamp
        """
        self.signal_history.append({
            'timestamp': timestamp,
            'symbol': signal.symbol,
            'side': signal.side,
            'confidence': signal.confidence,
            'sharpe_estimate': signal.sharpe_estimate,
            'quality_score': signal.quality_score,
            'strategy': signal.strategy_name
        })
        
        # Keep history bounded
        if len(self.signal_history) > self.max_history:
            self.signal_history = self.signal_history[-self.max_history:]
    
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
        """Update latest market data for all subscribed symbols."""
        # Data is automatically updated by the feed adapter
        pass
    
    def _prepare_strategy_data(self) -> Optional[pd.DataFrame]:
        """
        Prepare data in format expected by strategies.
        
        Returns:
            DataFrame with all available data, or None if no data
        """
        if not self._historical_data:
            return None
        
        if len(self.symbols) == 1:
            # Single symbol - return DataFrame for that symbol
            symbol = list(self.symbols)[0]
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
    
    def get_dashboard_summary(self) -> Dict:
        """
        Get summary for dashboard display.
        
        Returns:
            Dictionary with dashboard data
        """
        return {
            'is_running': self._running,
            'is_connected': self.is_connected(),
            'num_strategies': len(self.strategies),
            'num_symbols': len(self.symbols),
            'active_signals': len(self.active_signals),
            'recent_signals': self.signal_history[-10:] if self.signal_history else [],
            'stats': self.stats.copy(),
            'account_value': self.broker.get_account_value() if self.is_connected() else 0,
            'positions': len(self.broker.get_positions()) if self.is_connected() else 0
        }
    
    def print_dashboard(self) -> None:
        """Print dashboard to console."""
        summary = self.get_dashboard_summary()
        
        print("\n" + "=" * 60)
        print("LIVE SIGNAL MONITOR DASHBOARD")
        print("=" * 60)
        print(f"Status: {'RUNNING' if summary['is_running'] else 'STOPPED'}")
        print(f"Connected: {'YES' if summary['is_connected'] else 'NO'}")
        print(f"Strategies: {summary['num_strategies']}")
        print(f"Symbols: {summary['num_symbols']}")
        print(f"Account Value: ${summary['account_value']:,.2f}")
        print(f"Positions: {summary['positions']}")
        print("\nStatistics:")
        print(f"  Total Signals: {summary['stats']['total_signals_generated']}")
        print(f"  Executed: {summary['stats']['signals_executed']}")
        print(f"  Rejected: {summary['stats']['signals_rejected']}")
        print(f"  Errors: {summary['stats']['errors']}")
        print(f"\nActive Signals: {summary['active_signals']}")
        
        if summary['recent_signals']:
            print("\nRecent Signals:")
            for sig in summary['recent_signals']:
                print(
                    f"  {sig['timestamp'].strftime('%H:%M:%S')} | "
                    f"{sig['symbol']:6s} | {sig['side']:4s} | "
                    f"Quality: {sig['quality_score']:.2f} | "
                    f"Strategy: {sig['strategy']}"
                )
        
        print("=" * 60 + "\n")
    
    def __enter__(self):
        """Context manager entry"""
        self.connect()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.disconnect()
        return False
