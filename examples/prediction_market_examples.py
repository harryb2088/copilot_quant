"""
Prediction Market Data Examples

This script demonstrates how to use the prediction market data providers
to fetch data from Polymarket and Kalshi.

Run this script to explore prediction market data:
    python examples/prediction_market_examples.py
"""

import logging
import pandas as pd
from copilot_quant.data.prediction_markets import (
    PolymarketProvider,
    KalshiProvider,
    get_prediction_market_provider,
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def example_polymarket_markets():
    """Example: Fetch active markets from Polymarket."""
    print("\n" + "="*80)
    print("POLYMARKET - Active Markets")
    print("="*80)
    
    try:
        # Initialize provider
        provider = PolymarketProvider(rate_limit_delay=1.0)
        
        # Fetch active markets
        markets = provider.get_active_markets(limit=10)
        
        if not markets.empty:
            print(f"\nFound {len(markets)} active markets:")
            print("\nMarket Details:")
            for idx, market in markets.iterrows():
                print(f"\n{idx+1}. {market['question']}")
                print(f"   Category: {market['category']}")
                print(f"   Market ID: {market['market_id']}")
                print(f"   Volume: ${market['volume']:,.0f}")
                print(f"   End Date: {market['end_date']}")
        else:
            print("No markets returned (API may be unavailable or require different endpoint)")
            
    except Exception as e:
        logger.error(f"Error fetching Polymarket data: {e}")
        print(f"\nNote: {e}")
        print("The Polymarket API may have changed or may not be publicly accessible.")


def example_polymarket_category_filter():
    """Example: Fetch markets filtered by category."""
    print("\n" + "="*80)
    print("POLYMARKET - Crypto Markets")
    print("="*80)
    
    try:
        provider = PolymarketProvider(rate_limit_delay=1.0)
        
        # Fetch crypto-related markets
        markets = provider.get_active_markets(category='crypto', limit=5)
        
        if not markets.empty:
            print(f"\nFound {len(markets)} crypto markets:")
            for idx, market in markets.iterrows():
                print(f"\n{idx+1}. {market['question']}")
                print(f"   Volume: ${market['volume']:,.0f}")
        else:
            print("No crypto markets found")
            
    except Exception as e:
        logger.error(f"Error: {e}")


def example_kalshi_markets():
    """Example: Fetch active markets from Kalshi."""
    print("\n" + "="*80)
    print("KALSHI - Active Markets")
    print("="*80)
    
    try:
        # Initialize provider (no API key required for public data)
        provider = KalshiProvider(rate_limit_delay=1.0)
        
        # Fetch active markets
        markets = provider.get_active_markets(limit=10)
        
        if not markets.empty:
            print(f"\nFound {len(markets)} active markets:")
            print("\nMarket Details:")
            for idx, market in markets.iterrows():
                print(f"\n{idx+1}. {market['question']}")
                print(f"   Category: {market['category']}")
                print(f"   Ticker: {market['market_id']}")
                print(f"   Yes Bid: {market['yes_bid']:.2f}, Yes Ask: {market['yes_ask']:.2f}")
                print(f"   Volume: {market['volume']:,}")
        else:
            print("No markets returned")
            
    except Exception as e:
        logger.error(f"Error fetching Kalshi data: {e}")
        print(f"\nNote: {e}")
        print("The Kalshi API may require authentication or have different endpoints.")


def example_provider_factory():
    """Example: Use the factory function to get providers."""
    print("\n" + "="*80)
    print("PROVIDER FACTORY - Creating Providers")
    print("="*80)
    
    # Get Polymarket provider
    polymarket = get_prediction_market_provider('polymarket', rate_limit_delay=1.0)
    print(f"\nCreated Polymarket provider: {type(polymarket).__name__}")
    
    # Get Kalshi provider
    kalshi = get_prediction_market_provider('kalshi', rate_limit_delay=1.0)
    print(f"Created Kalshi provider: {type(kalshi).__name__}")
    
    # You can also pass API keys if available
    # kalshi_auth = get_prediction_market_provider(
    #     'kalshi',
    #     api_key='your_api_key',
    #     api_secret='your_api_secret'
    # )


def example_market_comparison():
    """Example: Compare similar markets across platforms."""
    print("\n" + "="*80)
    print("MARKET COMPARISON - Cross-Platform Analysis")
    print("="*80)
    
    try:
        # This is a conceptual example showing how you might compare markets
        polymarket = PolymarketProvider(rate_limit_delay=1.0)
        kalshi = KalshiProvider(rate_limit_delay=1.0)
        
        print("\nFetching markets from both platforms...")
        
        poly_markets = polymarket.get_active_markets(limit=5)
        kalshi_markets = kalshi.get_active_markets(limit=5)
        
        print(f"\nPolymarket: {len(poly_markets)} markets")
        print(f"Kalshi: {len(kalshi_markets)} markets")
        
        # In practice, you would match similar markets by question/topic
        # and compare their prices/probabilities
        
    except Exception as e:
        logger.error(f"Error: {e}")


def main():
    """Run all examples."""
    print("\n" + "#"*80)
    print("# PREDICTION MARKET DATA EXAMPLES")
    print("#"*80)
    
    print("\nThis script demonstrates fetching data from prediction market platforms.")
    print("Note: Some APIs may require authentication or have rate limits.")
    print("The examples use mock endpoints and may not return real data.")
    
    # Run examples
    example_polymarket_markets()
    example_polymarket_category_filter()
    example_kalshi_markets()
    example_provider_factory()
    example_market_comparison()
    
    print("\n" + "#"*80)
    print("# EXAMPLES COMPLETE")
    print("#"*80)
    print("\nNOTE: Prediction market APIs are subject to change and may require")
    print("authentication. Check the provider's documentation for current API details.")
    print("\nFor production use:")
    print("1. Sign up for API access at the respective platforms")
    print("2. Store API keys securely (environment variables)")
    print("3. Implement proper error handling and retry logic")
    print("4. Respect rate limits and API terms of service")


if __name__ == "__main__":
    main()
