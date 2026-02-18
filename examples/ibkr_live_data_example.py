"""
Example: Using IBKR Live Market Data Feed

This script demonstrates how to use the IBKRLiveDataFeed class to:
- Connect to Interactive Brokers
- Subscribe to real-time market data
- Download historical data for backfilling
- Handle streaming updates

Prerequisites:
1. IB TWS or IB Gateway running
2. API connections enabled in TWS/Gateway settings
3. ib_insync installed: pip install ib_insync>=0.9.86

Configuration:
- Edit the symbols list below to change which stocks to monitor
- Adjust connection parameters as needed
"""

import logging
import time
from datetime import datetime

from copilot_quant.brokers.live_market_data import IBKRLiveDataFeed


# Configure logging to see what's happening
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


def on_price_update(symbol: str, data: dict):
    """
    Callback function for real-time price updates.
    
    This function is called whenever new market data arrives for a subscribed symbol.
    
    Args:
        symbol: Ticker symbol
        data: Dictionary with market data (bid, ask, last, volume, etc.)
    """
    # Extract relevant data
    last = data.get('last')
    bid = data.get('bid')
    ask = data.get('ask')
    volume = data.get('volume')
    time_str = data.get('time', datetime.now()).strftime('%H:%M:%S')
    
    # Print update
    price_str = f"${last:.2f}" if last else "N/A"
    bid_str = f"${bid:.2f}" if bid else "N/A"
    ask_str = f"${ask:.2f}" if ask else "N/A"
    vol_str = f"{volume:,}" if volume else "N/A"
    
    logger.info(
        f"[{time_str}] {symbol:6s} | Last: {price_str:8s} | "
        f"Bid: {bid_str:8s} | Ask: {ask_str:8s} | Vol: {vol_str}"
    )


def example_basic_usage():
    """Basic example: Subscribe and monitor prices"""
    print("\n" + "="*70)
    print("Example 1: Basic Usage - Real-time Price Monitoring")
    print("="*70 + "\n")
    
    # Create the data feed (paper trading by default)
    feed = IBKRLiveDataFeed(paper_trading=True)
    
    # Connect to IBKR
    if not feed.connect():
        print("Failed to connect to IBKR. Make sure TWS/Gateway is running.")
        return
    
    print("✓ Connected to IBKR\n")
    
    # Define symbols to monitor
    symbols = ['AAPL', 'MSFT', 'GOOGL']
    
    # Subscribe to real-time data with callback
    print(f"Subscribing to: {', '.join(symbols)}")
    results = feed.subscribe(symbols, callback=on_price_update)
    
    # Check subscription results
    for symbol, success in results.items():
        status = "✓" if success else "✗"
        print(f"{status} {symbol}")
    
    print("\nMonitoring prices for 30 seconds...")
    print("(Press Ctrl+C to stop earlier)\n")
    
    try:
        # Monitor for 30 seconds
        time.sleep(30)
    except KeyboardInterrupt:
        print("\n\nStopped by user")
    
    # Get latest prices
    print("\n" + "-"*70)
    print("Latest Prices:")
    print("-"*70)
    for symbol in symbols:
        price = feed.get_latest_price(symbol)
        data = feed.get_latest_data(symbol)
        
        if price:
            print(f"{symbol:6s}: ${price:8.2f} | Volume: {data.get('volume', 'N/A')}")
        else:
            print(f"{symbol:6s}: No data available")
    
    # Unsubscribe and disconnect
    print("\nUnsubscribing and disconnecting...")
    feed.unsubscribe(symbols)
    feed.disconnect()
    print("✓ Done\n")


def example_historical_data():
    """Example: Download historical data for backfilling"""
    print("\n" + "="*70)
    print("Example 2: Historical Data Download")
    print("="*70 + "\n")
    
    # Use context manager for automatic connection/disconnection
    with IBKRLiveDataFeed(paper_trading=True) as feed:
        symbol = 'AAPL'
        
        print(f"Downloading historical data for {symbol}...")
        
        # Get 1 month of daily bars
        df = feed.get_historical_bars(
            symbol=symbol,
            duration='1 M',
            bar_size='1 day'
        )
        
        if df is not None:
            print(f"\n✓ Retrieved {len(df)} bars\n")
            print("First 5 bars:")
            print(df.head())
            print("\nLast 5 bars:")
            print(df.tail())
            print("\nData summary:")
            print(df.describe())
        else:
            print("Failed to retrieve historical data")


def example_multiple_timeframes():
    """Example: Get historical data with different timeframes"""
    print("\n" + "="*70)
    print("Example 3: Multiple Timeframes")
    print("="*70 + "\n")
    
    feed = IBKRLiveDataFeed(paper_trading=True)
    
    if not feed.connect():
        print("Failed to connect")
        return
    
    symbol = 'AAPL'
    
    # Get different timeframes
    timeframes = [
        ('5 D', '5 mins', "5 days of 5-minute bars"),
        ('2 W', '1 hour', "2 weeks of hourly bars"),
        ('1 M', '1 day', "1 month of daily bars"),
    ]
    
    for duration, bar_size, description in timeframes:
        print(f"\n{description}:")
        print("-" * 50)
        
        df = feed.get_historical_bars(
            symbol=symbol,
            duration=duration,
            bar_size=bar_size
        )
        
        if df is not None:
            print(f"Retrieved {len(df)} bars")
            print(f"Date range: {df.index[0]} to {df.index[-1]}")
            print(f"Price range: ${df['low'].min():.2f} - ${df['high'].max():.2f}")
        else:
            print("Failed to retrieve data")
    
    feed.disconnect()


def example_reconnection():
    """Example: Automatic reconnection handling"""
    print("\n" + "="*70)
    print("Example 4: Reconnection Handling")
    print("="*70 + "\n")
    
    feed = IBKRLiveDataFeed(paper_trading=True)
    
    if not feed.connect():
        print("Failed to connect")
        return
    
    # Subscribe to symbols
    symbols = ['AAPL', 'MSFT']
    feed.subscribe(symbols, callback=on_price_update)
    
    print(f"Subscribed to: {', '.join(symbols)}")
    print("Monitoring for 10 seconds...")
    time.sleep(10)
    
    # Simulate disconnection
    print("\nSimulating reconnection...")
    if feed.reconnect():
        print("✓ Reconnected successfully")
        print("Subscriptions restored automatically")
        
        # Check which symbols are still subscribed
        active_symbols = feed.get_subscribed_symbols()
        print(f"Active subscriptions: {', '.join(active_symbols)}")
    else:
        print("✗ Reconnection failed")
    
    feed.disconnect()


def example_symbol_universe():
    """Example: Managing symbol universe"""
    print("\n" + "="*70)
    print("Example 5: Managing Symbol Universe")
    print("="*70 + "\n")
    
    print("""
To change which symbols to monitor:

1. Method 1: Subscribe to a different list
   ----------------------------------------
   symbols = ['TSLA', 'NVDA', 'AMD']
   feed.subscribe(symbols)

2. Method 2: Add/remove symbols dynamically
   -----------------------------------------
   # Add new symbols
   feed.subscribe(['META', 'NFLX'])
   
   # Remove symbols
   feed.unsubscribe(['AAPL'])
   
   # Check active subscriptions
   active = feed.get_subscribed_symbols()

3. Method 3: Subscribe to S&P 500 or custom list
   ----------------------------------------------
   # Load symbols from a file or database
   with open('my_watchlist.txt') as f:
       symbols = [line.strip() for line in f]
   
   feed.subscribe(symbols)

4. Best Practices:
   ---------------
   - Start with a small watchlist (5-10 symbols) for testing
   - IBKR market data subscriptions have costs (free for delayed data)
   - Subscribe only to symbols you're actively trading
   - Unsubscribe when you no longer need the data
   - Monitor connection status and handle reconnections
    """)


def main():
    """Run all examples"""
    print("\n" + "="*70)
    print("IBKR Live Market Data Feed - Examples")
    print("="*70)
    
    print("""
Make sure you have:
1. TWS or IB Gateway running
2. API connections enabled (Configuration > API > Settings)
3. Correct port: 7497 for Paper TWS, 7496 for Live TWS
    """)
    
    input("Press Enter to continue with examples...")
    
    try:
        # Run examples
        example_basic_usage()
        
        input("\nPress Enter for next example...")
        example_historical_data()
        
        input("\nPress Enter for next example...")
        example_multiple_timeframes()
        
        input("\nPress Enter for next example...")
        example_reconnection()
        
        input("\nPress Enter for next example...")
        example_symbol_universe()
        
    except KeyboardInterrupt:
        print("\n\nExamples interrupted by user")
    except Exception as e:
        logger.error(f"Error running examples: {e}", exc_info=True)
    
    print("\n" + "="*70)
    print("Examples completed!")
    print("="*70 + "\n")


if __name__ == '__main__':
    main()
