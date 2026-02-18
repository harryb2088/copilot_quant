"""
Sample Strategy Execution Example

This example demonstrates how to run a strategy in both backtest and live modes
using the new adapter integration.

The same strategy code works seamlessly in both modes without modification.
"""

import logging
from datetime import datetime
import pandas as pd

from copilot_quant.backtest.strategy import Strategy
from copilot_quant.backtest.orders import Order


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class SimpleMovingAverageStrategy(Strategy):
    """
    Simple Moving Average Crossover Strategy
    
    This strategy:
    - Calculates fast and slow moving averages
    - Buys when fast MA crosses above slow MA
    - Sells when fast MA crosses below slow MA
    
    Works in both backtest and live modes.
    """
    
    def initialize(self):
        """Initialize strategy parameters"""
        self.fast_period = 10
        self.slow_period = 30
        self.position = None
        
        logger.info(
            f"Strategy initialized: fast_period={self.fast_period}, "
            f"slow_period={self.slow_period}"
        )
    
    def on_data(self, timestamp: datetime, data: pd.DataFrame) -> list:
        """
        Process market data and generate orders.
        
        Args:
            timestamp: Current timestamp
            data: DataFrame with historical OHLCV data
            
        Returns:
            List of orders to execute
        """
        orders = []
        
        # Extract close prices
        if 'Close' in data.columns:
            # Single symbol format
            close_prices = data['Close']
        elif isinstance(data.columns, pd.MultiIndex) and ('Close', 'AAPL') in data.columns:
            # Multi-symbol format
            close_prices = data[('Close', 'AAPL')]
        else:
            logger.warning("Could not extract close prices from data")
            return orders
        
        # Need enough data for slow MA
        if len(close_prices) < self.slow_period:
            logger.debug(f"Not enough data: {len(close_prices)} < {self.slow_period}")
            return orders
        
        # Calculate moving averages
        fast_ma = close_prices.tail(self.fast_period).mean()
        slow_ma = close_prices.tail(self.slow_period).mean()
        
        current_price = close_prices.iloc[-1]
        
        logger.debug(
            f"{timestamp} - Price: ${current_price:.2f}, "
            f"Fast MA: ${fast_ma:.2f}, Slow MA: ${slow_ma:.2f}"
        )
        
        # Generate signals
        if fast_ma > slow_ma and self.position is None:
            # Buy signal
            logger.info(
                f"BUY SIGNAL: Fast MA ({fast_ma:.2f}) > Slow MA ({slow_ma:.2f})"
            )
            
            orders.append(Order(
                symbol='AAPL',
                quantity=10,
                order_type='market',
                side='buy'
            ))
            self.position = 'long'
        
        elif fast_ma < slow_ma and self.position == 'long':
            # Sell signal
            logger.info(
                f"SELL SIGNAL: Fast MA ({fast_ma:.2f}) < Slow MA ({slow_ma:.2f})"
            )
            
            orders.append(Order(
                symbol='AAPL',
                quantity=10,
                order_type='market',
                side='sell'
            ))
            self.position = None
        
        return orders
    
    def on_fill(self, fill):
        """
        Handle order fill notification.
        
        Args:
            fill: Fill object with execution details
        """
        logger.info(
            f"ORDER FILLED: {fill.order.side} {fill.fill_quantity} {fill.order.symbol} "
            f"@ ${fill.fill_price:.2f}, commission=${fill.commission:.2f}"
        )
    
    def finalize(self):
        """Called when strategy ends"""
        logger.info("Strategy finalized")


def run_backtest():
    """
    Run strategy in backtest mode using historical data.
    """
    logger.info("=" * 60)
    logger.info("BACKTEST MODE")
    logger.info("=" * 60)
    
    from copilot_quant.backtest.engine import BacktestEngine
    from copilot_quant.data.providers import YFinanceProvider
    
    # Create backtest engine
    engine = BacktestEngine(
        initial_capital=100000,
        data_provider=YFinanceProvider(),
        commission=0.001,
        slippage=0.0005
    )
    
    # Add strategy
    strategy = SimpleMovingAverageStrategy()
    engine.add_strategy(strategy)
    
    # Run backtest
    result = engine.run(
        start_date=datetime(2023, 1, 1),
        end_date=datetime(2023, 12, 31),
        symbols=['AAPL']
    )
    
    # Print results
    logger.info("\nBacktest Results:")
    logger.info(f"Initial Capital: ${result.initial_capital:,.2f}")
    logger.info(f"Final Capital: ${result.final_capital:,.2f}")
    logger.info(f"Total Return: {result.total_return:.2%}")
    logger.info(f"Total Trades: {len(result.trades)}")
    
    return result


def run_live_paper_trading():
    """
    Run strategy in live paper trading mode.
    
    NOTE: This requires IBKR TWS or IB Gateway to be running.
    """
    logger.info("=" * 60)
    logger.info("LIVE PAPER TRADING MODE")
    logger.info("=" * 60)
    
    from copilot_quant.backtest.live_engine import LiveStrategyEngine
    import signal
    import sys
    import time
    
    # Create live engine
    engine = LiveStrategyEngine(
        paper_trading=True,
        commission=0.001,
        slippage=0.0005,
        update_interval=60.0,  # Update every 60 seconds
        enable_reconnect=True
    )
    
    # Add strategy
    strategy = SimpleMovingAverageStrategy()
    engine.add_strategy(strategy)
    
    # Setup signal handler for graceful shutdown
    def signal_handler(sig, frame):
        logger.info("\nShutting down gracefully...")
        engine.stop()
        engine.disconnect()
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Connect to IBKR
    logger.info("Connecting to IBKR...")
    if not engine.connect(timeout=30, retry_count=3):
        logger.error("Failed to connect to IBKR")
        logger.error("Please ensure TWS or IB Gateway is running")
        return
    
    logger.info("✓ Connected to IBKR")
    
    # Start live trading
    logger.info("Starting live trading...")
    if not engine.start(
        symbols=['AAPL'],
        lookback_days=60,  # Load 60 days of historical data
        data_interval='1d'
    ):
        logger.error("Failed to start live trading")
        engine.disconnect()
        return
    
    logger.info("✓ Live trading started")
    logger.info("\nMonitoring... (Press Ctrl+C to stop)")
    
    try:
        # Monitor performance
        while True:
            time.sleep(60)  # Update every minute
            
            summary = engine.get_performance_summary()
            logger.info(
                f"\nStatus: Running={summary['is_running']}, "
                f"Connected={summary['is_connected']}"
            )
            logger.info(
                f"Account Value: ${summary['account_value']:,.2f}, "
                f"Cash: ${summary['cash_balance']:,.2f}"
            )
            logger.info(
                f"Positions: {summary['positions']}, "
                f"Fills: {summary['total_fills']}, "
                f"Errors: {summary['total_errors']}"
            )
    
    except KeyboardInterrupt:
        logger.info("\nStopping...")
    
    finally:
        engine.stop()
        engine.disconnect()
        logger.info("✓ Disconnected")


def demo_adapter_usage():
    """
    Demonstrate direct usage of adapters (advanced).
    """
    logger.info("=" * 60)
    logger.info("ADAPTER DIRECT USAGE DEMO")
    logger.info("=" * 60)
    
    from copilot_quant.brokers.live_data_adapter import LiveDataFeedAdapter
    from copilot_quant.brokers.live_broker_adapter import LiveBrokerAdapter
    
    # Initialize adapters
    data_feed = LiveDataFeedAdapter(paper_trading=True)
    broker = LiveBrokerAdapter(paper_trading=True)
    
    try:
        # Connect
        logger.info("Connecting to IBKR...")
        if not data_feed.connect() or not broker.connect():
            logger.error("Failed to connect")
            return
        
        logger.info("✓ Connected")
        
        # Get historical data
        logger.info("\nGetting historical data...")
        hist_data = data_feed.get_historical_data(
            symbol='AAPL',
            start_date=datetime(2024, 1, 1),
            interval='1d'
        )
        
        if not hist_data.empty:
            logger.info(f"✓ Retrieved {len(hist_data)} bars")
            logger.info(f"Latest close: ${hist_data['Close'].iloc[-1]:.2f}")
        
        # Subscribe to real-time data
        logger.info("\nSubscribing to real-time data...")
        results = data_feed.subscribe(['AAPL'])
        if results.get('AAPL'):
            logger.info("✓ Subscribed to AAPL")
        
        # Get latest price
        price = data_feed.get_latest_price('AAPL')
        if price:
            logger.info(f"Current price: ${price:.2f}")
        
        # Get account info
        logger.info("\nAccount information:")
        cash = broker.get_cash_balance()
        logger.info(f"Cash balance: ${cash:,.2f}")
        
        account_value = broker.get_account_value()
        logger.info(f"Account value: ${account_value:,.2f}")
        
        # Get positions
        positions = broker.get_positions()
        logger.info(f"Current positions: {len(positions)}")
        for symbol, position in positions.items():
            logger.info(f"  {symbol}: {position.quantity} shares")
        
        logger.info("\n✓ Demo complete")
    
    finally:
        # Disconnect
        data_feed.disconnect()
        broker.disconnect()
        logger.info("✓ Disconnected")


if __name__ == '__main__':
    import sys
    
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python sample_execution.py backtest    - Run backtest mode")
        print("  python sample_execution.py live        - Run live paper trading")
        print("  python sample_execution.py demo        - Demo adapter usage")
        sys.exit(1)
    
    mode = sys.argv[1].lower()
    
    if mode == 'backtest':
        run_backtest()
    elif mode == 'live':
        run_live_paper_trading()
    elif mode == 'demo':
        demo_adapter_usage()
    else:
        print(f"Unknown mode: {mode}")
        sys.exit(1)
