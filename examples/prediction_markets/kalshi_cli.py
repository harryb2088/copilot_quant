#!/usr/bin/env python3
"""
Example CLI for fetching Kalshi data.

This script demonstrates how to:
1. List available markets on Kalshi
2. Fetch price history for a specific market
3. Save data to CSV or SQLite

Usage:
    # List markets
    python kalshi_cli.py list --limit 10

    # Get market data
    python kalshi_cli.py fetch --market-id <TICKER> --output data.csv

    # Save to SQLite
    python kalshi_cli.py fetch --market-id <TICKER> --sqlite --db-path markets.db

Note: Some Kalshi API endpoints may require authentication.
      Set KALSHI_API_KEY environment variable if you have one.
"""

import argparse
import logging
import os
import sys
from pathlib import Path

# Add parent directory to path to import copilot_quant
sys.path.insert(0, str(Path(__file__).parent.parent))

from copilot_quant.data.prediction_markets import KalshiProvider, PredictionMarketStorage

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def list_markets(args):
    """List available markets on Kalshi."""
    api_key = os.environ.get('KALSHI_API_KEY')
    provider = KalshiProvider(api_key=api_key)
    markets = provider.list_markets(limit=args.limit)
    
    if markets.empty:
        logger.warning("No markets found")
        return
    
    print(f"\nFound {len(markets)} markets:\n")
    print(markets.to_string(index=False))
    
    if args.save:
        storage = PredictionMarketStorage(
            storage_type='csv' if not args.sqlite else 'sqlite',
            db_path=args.db_path
        )
        storage.save_markets('kalshi', markets)
        print("\nSaved markets to storage")


def fetch_market(args):
    """Fetch data for a specific market."""
    api_key = os.environ.get('KALSHI_API_KEY')
    provider = KalshiProvider(api_key=api_key)
    
    # Get market details
    details = provider.get_market_details(args.market_id)
    if not details:
        logger.error(f"Could not find market: {args.market_id}")
        return
    
    print(f"\nMarket: {details.get('title', 'Unknown')}")
    print(f"Category: {details.get('category', 'Unknown')}")
    print(f"Status: {details.get('status', 'Unknown')}")
    print(f"Yes Price: ${details.get('yes_price', 0):.2f}")
    print(f"No Price: ${details.get('no_price', 0):.2f}")
    print(f"Volume: ${details.get('volume', 0):,.2f}")
    
    # Fetch price data
    print("\nFetching price data...")
    data = provider.get_market_data(
        args.market_id,
        start_date=args.start_date,
        end_date=args.end_date
    )
    
    if data.empty:
        logger.warning("No price data available")
        return
    
    print(f"\nFetched {len(data)} data points")
    print("\nLatest prices:")
    print(data.tail(10).to_string())
    
    # Save data
    if args.output:
        data.to_csv(args.output)
        print(f"\nSaved data to {args.output}")
    
    if args.sqlite:
        storage = PredictionMarketStorage(
            storage_type='sqlite',
            db_path=args.db_path
        )
        storage.save_market_data('kalshi', args.market_id, data)
        print("\nSaved data to SQLite database")


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description='Kalshi Data Fetcher CLI',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Command to run')
    
    # List command
    list_parser = subparsers.add_parser('list', help='List available markets')
    list_parser.add_argument('--limit', type=int, default=20,
                            help='Maximum number of markets to list')
    list_parser.add_argument('--save', action='store_true',
                            help='Save markets to storage')
    list_parser.add_argument('--sqlite', action='store_true',
                            help='Use SQLite storage instead of CSV')
    list_parser.add_argument('--db-path', default='data/prediction_markets/markets.db',
                            help='SQLite database path')
    
    # Fetch command
    fetch_parser = subparsers.add_parser('fetch', help='Fetch market data')
    fetch_parser.add_argument('--market-id', required=True,
                             help='Market ticker (e.g., INX-23DEC31-T4200)')
    fetch_parser.add_argument('--start-date', help='Start date (YYYY-MM-DD)')
    fetch_parser.add_argument('--end-date', help='End date (YYYY-MM-DD)')
    fetch_parser.add_argument('--output', help='Output CSV file path')
    fetch_parser.add_argument('--sqlite', action='store_true',
                             help='Save to SQLite database')
    fetch_parser.add_argument('--db-path', default='data/prediction_markets/markets.db',
                             help='SQLite database path')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    if args.command == 'list':
        list_markets(args)
    elif args.command == 'fetch':
        fetch_market(args)


if __name__ == '__main__':
    main()
