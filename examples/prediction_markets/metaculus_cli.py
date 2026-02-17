#!/usr/bin/env python3
"""
Example CLI for fetching Metaculus data.

This script demonstrates how to:
1. List available questions on Metaculus
2. Fetch community prediction history
3. Save data to CSV or SQLite

Usage:
    # List questions
    python metaculus_cli.py list --limit 10

    # Get question data
    python metaculus_cli.py fetch --market-id <QUESTION_ID> --output data.csv

    # Save to SQLite
    python metaculus_cli.py fetch --market-id <QUESTION_ID> --sqlite --db-path markets.db
"""

import argparse
import logging
import sys
from pathlib import Path

# Add parent directory to path to import copilot_quant
sys.path.insert(0, str(Path(__file__).parent.parent))

from copilot_quant.data.prediction_markets import MetaculusProvider, PredictionMarketStorage

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def list_markets(args):
    """List available questions on Metaculus."""
    provider = MetaculusProvider()
    markets = provider.list_markets(limit=args.limit)
    
    if markets.empty:
        logger.warning("No questions found")
        return
    
    print(f"\nFound {len(markets)} questions:\n")
    print(markets.to_string(index=False))
    
    if args.save:
        storage = PredictionMarketStorage(
            storage_type='csv' if not args.sqlite else 'sqlite',
            db_path=args.db_path
        )
        storage.save_markets('metaculus', markets)
        print("\nSaved questions to storage")


def fetch_market(args):
    """Fetch data for a specific question."""
    provider = MetaculusProvider()
    
    # Get question details
    details = provider.get_market_details(args.market_id)
    if not details:
        logger.error(f"Could not find question: {args.market_id}")
        return
    
    print(f"\nQuestion: {details.get('title', 'Unknown')}")
    print(f"Type: {details.get('type', 'Unknown')}")
    print(f"Status: {details.get('status', 'Unknown')}")
    print(f"Number of Predictions: {details.get('num_predictions', 0)}")
    print(f"Community Prediction: {details.get('community_prediction', 'N/A')}")
    
    # Fetch prediction history
    print("\nFetching prediction history...")
    data = provider.get_market_data(
        args.market_id,
        start_date=args.start_date,
        end_date=args.end_date
    )
    
    if data.empty:
        logger.warning("No prediction history available")
        return
    
    print(f"\nFetched {len(data)} prediction points")
    print("\nLatest predictions:")
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
        storage.save_market_data('metaculus', args.market_id, data)
        print("\nSaved data to SQLite database")


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description='Metaculus Data Fetcher CLI',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Command to run')
    
    # List command
    list_parser = subparsers.add_parser('list', help='List available questions')
    list_parser.add_argument('--limit', type=int, default=20,
                            help='Maximum number of questions to list')
    list_parser.add_argument('--save', action='store_true',
                            help='Save questions to storage')
    list_parser.add_argument('--sqlite', action='store_true',
                            help='Use SQLite storage instead of CSV')
    list_parser.add_argument('--db-path', default='data/prediction_markets/markets.db',
                            help='SQLite database path')
    
    # Fetch command
    fetch_parser = subparsers.add_parser('fetch', help='Fetch question data')
    fetch_parser.add_argument('--market-id', required=True,
                             help='Question ID')
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
