#!/usr/bin/env python3
"""
Comprehensive example demonstrating prediction market data fetchers.

This script shows how to:
1. List markets from each platform
2. Fetch market details
3. Save data to storage
4. Load data back from storage
"""

import logging
import sys
from pathlib import Path

# Add parent directory to path to import copilot_quant
sys.path.insert(0, str(Path(__file__).parent.parent))

from copilot_quant.data.prediction_markets import (
    PolymarketProvider,
    KalshiProvider,
    PredictItProvider,
    MetaculusProvider,
    PredictionMarketStorage,
)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def demo_polymarket():
    """Demonstrate Polymarket data fetching."""
    print("\n" + "="*60)
    print("POLYMARKET DEMO")
    print("="*60)
    
    provider = PolymarketProvider()
    
    # List markets
    print("\nFetching markets...")
    markets = provider.list_markets(limit=5)
    
    if not markets.empty:
        print(f"\nFound {len(markets)} markets:")
        for idx, row in markets.iterrows():
            print(f"\n{idx+1}. {row['title']}")
            print(f"   ID: {row['market_id']}")
            print(f"   Category: {row['category']}")
            print(f"   Volume: ${row['volume']:,.2f}")
    else:
        print("No markets found (this is expected if API is unavailable)")
    
    return markets


def demo_kalshi():
    """Demonstrate Kalshi data fetching."""
    print("\n" + "="*60)
    print("KALSHI DEMO")
    print("="*60)
    
    provider = KalshiProvider()
    
    print("\nFetching markets...")
    markets = provider.list_markets(limit=5)
    
    if not markets.empty:
        print(f"\nFound {len(markets)} markets:")
        for idx, row in markets.iterrows():
            print(f"\n{idx+1}. {row['title']}")
            print(f"   Ticker: {row['market_id']}")
            print(f"   Category: {row['category']}")
    else:
        print("No markets found (this is expected if API is unavailable)")
    
    return markets


def demo_predictit():
    """Demonstrate PredictIt data fetching."""
    print("\n" + "="*60)
    print("PREDICTIT DEMO")
    print("="*60)
    
    provider = PredictItProvider()
    
    print("\nFetching markets...")
    markets = provider.list_markets(limit=5)
    
    if not markets.empty:
        print(f"\nFound {len(markets)} markets:")
        for idx, row in markets.iterrows():
            print(f"\n{idx+1}. {row['title']}")
            print(f"   ID: {row['market_id']}")
            print(f"   Status: {row['status']}")
    else:
        print("No markets found (this is expected if API is unavailable)")
    
    return markets


def demo_metaculus():
    """Demonstrate Metaculus data fetching."""
    print("\n" + "="*60)
    print("METACULUS DEMO")
    print("="*60)
    
    provider = MetaculusProvider()
    
    print("\nFetching questions...")
    questions = provider.list_markets(limit=5)
    
    if not questions.empty:
        print(f"\nFound {len(questions)} questions:")
        for idx, row in questions.iterrows():
            print(f"\n{idx+1}. {row['title']}")
            print(f"   ID: {row['market_id']}")
            print(f"   Predictions: {row['num_predictions']}")
            print(f"   Community: {row['community_prediction']}")
    else:
        print("No questions found (this is expected if API is unavailable)")
    
    return questions


def demo_storage(markets_data):
    """Demonstrate data storage."""
    print("\n" + "="*60)
    print("STORAGE DEMO")
    print("="*60)
    
    # Create storage
    storage = PredictionMarketStorage(
        storage_type='sqlite',
        db_path='/tmp/prediction_markets_demo.db'
    )
    
    # Save data from each platform
    for provider_name, markets in markets_data.items():
        if not markets.empty:
            print(f"\nSaving {len(markets)} markets from {provider_name}...")
            storage.save_markets(provider_name, markets)
    
    # Load data back
    print("\n\nLoading data back from storage:")
    for provider_name in markets_data.keys():
        loaded = storage.load_markets(provider_name)
        if not loaded.empty:
            print(f"  {provider_name}: {len(loaded)} markets")
    
    print("\nData saved to: /tmp/prediction_markets_demo.db")


def main():
    """Run all demos."""
    print("\n" + "="*60)
    print("PREDICTION MARKET DATA FETCHERS - COMPREHENSIVE DEMO")
    print("="*60)
    print("\nThis demo will attempt to fetch data from all supported platforms.")
    print("Some platforms may be unavailable or rate-limited, which is normal.")
    
    markets_data = {}
    
    # Run demos for each platform
    try:
        markets_data['polymarket'] = demo_polymarket()
    except Exception as e:
        logger.error(f"Polymarket demo failed: {e}")
        markets_data['polymarket'] = None
    
    try:
        markets_data['kalshi'] = demo_kalshi()
    except Exception as e:
        logger.error(f"Kalshi demo failed: {e}")
        markets_data['kalshi'] = None
    
    try:
        markets_data['predictit'] = demo_predictit()
    except Exception as e:
        logger.error(f"PredictIt demo failed: {e}")
        markets_data['predictit'] = None
    
    try:
        markets_data['metaculus'] = demo_metaculus()
    except Exception as e:
        logger.error(f"Metaculus demo failed: {e}")
        markets_data['metaculus'] = None
    
    # Filter out None values
    markets_data = {k: v for k, v in markets_data.items() if v is not None and not v.empty}
    
    # Demonstrate storage if we have any data
    if markets_data:
        try:
            demo_storage(markets_data)
        except Exception as e:
            logger.error(f"Storage demo failed: {e}")
    
    print("\n" + "="*60)
    print("DEMO COMPLETE")
    print("="*60)
    print("\nFor more examples, see:")
    print("  - notebooks/prediction_markets_tutorial.ipynb")
    print("  - examples/prediction_markets/*_cli.py")
    print("  - README.md (Prediction Market Data Fetchers section)")


if __name__ == '__main__':
    main()
