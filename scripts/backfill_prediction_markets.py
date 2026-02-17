#!/usr/bin/env python3
"""
Prediction Markets Historical Data Backfill Script

This script performs a complete historical backfill of prediction market data
from supported platforms (Polymarket, Kalshi, etc.).

Usage:
    # Backfill all active markets from Polymarket
    python scripts/backfill_prediction_markets.py --provider polymarket
    
    # Backfill specific markets
    python scripts/backfill_prediction_markets.py --provider polymarket --market-ids MARKET_ID_1,MARKET_ID_2
    
    # Use SQLite storage
    python scripts/backfill_prediction_markets.py --provider polymarket --storage sqlite
    
    # Backfill multiple providers
    python scripts/backfill_prediction_markets.py --provider polymarket,kalshi

Features:
    - Fetches active markets and historical data
    - Progress tracking and status reporting
    - Comprehensive error handling and logging
    - Configurable storage backend (CSV/SQLite)
    - Multi-provider support
    - Detailed summary statistics
"""

import argparse
import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import List, Optional

import pandas as pd

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from copilot_quant.data.prediction_markets import PolymarketProvider, KalshiProvider
from copilot_quant.data.prediction_markets.storage import PredictionMarketStorage


def setup_logging(log_dir: str = 'data/logs', verbose: bool = False) -> None:
    """
    Configure logging for the backfill script.
    
    Args:
        log_dir: Directory for log files
        verbose: Enable verbose (DEBUG) logging
    """
    log_path = Path(log_dir)
    log_path.mkdir(parents=True, exist_ok=True)
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    log_file = log_path / f'backfill_prediction_markets_{timestamp}.log'
    
    level = logging.DEBUG if verbose else logging.INFO
    
    # Configure logging
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler(sys.stdout)
        ]
    )
    
    logger = logging.getLogger(__name__)
    logger.info(f"Logging to {log_file}")


def get_provider(provider_name: str, **kwargs):
    """
    Get a prediction market provider instance.
    
    Args:
        provider_name: Name of the provider
        **kwargs: Additional provider arguments
        
    Returns:
        Provider instance
    """
    providers = {
        'polymarket': PolymarketProvider,
        'kalshi': KalshiProvider,
    }
    
    provider_class = providers.get(provider_name.lower())
    if provider_class is None:
        raise ValueError(f"Unknown provider: {provider_name}")
    
    return provider_class(**kwargs)


def backfill_provider_markets(
    provider_name: str,
    storage: PredictionMarketStorage,
    market_ids: Optional[List[str]] = None,
    category: Optional[str] = None,
    limit: int = 100,
    rate_limit_delay: float = 0.5
) -> dict:
    """
    Backfill markets for a specific provider.
    
    Args:
        provider_name: Name of the provider
        storage: Storage instance
        market_ids: Optional list of specific market IDs
        category: Optional category filter
        limit: Maximum number of markets to fetch
        rate_limit_delay: Delay between API calls
        
    Returns:
        Dictionary with 'success' and 'failed' market lists
    """
    logger = logging.getLogger(__name__)
    
    logger.info(f"Starting backfill for {provider_name}...")
    
    # Initialize provider
    provider = get_provider(provider_name, rate_limit_delay=rate_limit_delay)
    
    success = []
    failed = []
    
    # Fetch active markets if no specific IDs provided
    if market_ids is None:
        logger.info(f"Fetching active markets from {provider_name}...")
        try:
            markets_df = provider.get_active_markets(category=category, limit=limit)
            
            if markets_df.empty:
                logger.warning(f"No active markets found for {provider_name}")
                return {'success': [], 'failed': []}
            
            # Save markets list
            storage.save_markets(provider_name, markets_df)
            logger.info(f"Saved {len(markets_df)} markets from {provider_name}")
            
            market_ids = markets_df['market_id'].tolist()
            
        except Exception as e:
            logger.error(f"Failed to fetch markets from {provider_name}: {e}")
            return {'success': [], 'failed': []}
    
    # Fetch market data for each market
    logger.info(f"Fetching data for {len(market_ids)} markets...")
    
    for i, market_id in enumerate(market_ids):
        logger.info(f"Processing {i+1}/{len(market_ids)}: {market_id}")
        
        try:
            # Get market price data
            prices_df = provider.get_market_prices(market_id)
            
            if not prices_df.empty:
                storage.save_market_data(provider_name, market_id, prices_df)
                success.append(market_id)
                logger.info(f"✓ Saved data for market {market_id}")
            else:
                logger.warning(f"✗ No data returned for market {market_id}")
                failed.append(market_id)
                
        except Exception as e:
            logger.error(f"✗ Failed to fetch data for market {market_id}: {e}")
            failed.append(market_id)
    
    return {'success': success, 'failed': failed}


def backfill_prediction_markets(
    providers: List[str],
    market_ids: Optional[List[str]] = None,
    category: Optional[str] = None,
    limit: int = 100,
    storage_type: str = 'csv',
    base_path: str = 'data/prediction_markets',
    db_path: Optional[str] = None,
    rate_limit_delay: float = 0.5
) -> dict:
    """
    Backfill prediction market data from multiple providers.
    
    Args:
        providers: List of provider names
        market_ids: Optional list of specific market IDs
        category: Optional category filter
        limit: Maximum number of markets per provider
        storage_type: 'csv' or 'sqlite'
        base_path: Base path for CSV storage
        db_path: Path to SQLite database
        rate_limit_delay: Delay between API calls
        
    Returns:
        Dictionary mapping provider names to results
    """
    logger = logging.getLogger(__name__)
    
    # Initialize storage
    storage = PredictionMarketStorage(
        storage_type=storage_type,
        base_path=base_path,
        db_path=db_path
    )
    
    logger.info(f"Starting backfill for {len(providers)} providers")
    logger.info(f"Storage: {storage_type}")
    
    start_time = datetime.now()
    all_results = {}
    
    # Process each provider
    for provider_name in providers:
        logger.info(f"\n{'='*80}")
        logger.info(f"Processing provider: {provider_name}")
        logger.info(f"{'='*80}")
        
        try:
            result = backfill_provider_markets(
                provider_name=provider_name,
                storage=storage,
                market_ids=market_ids,
                category=category,
                limit=limit,
                rate_limit_delay=rate_limit_delay
            )
            all_results[provider_name] = result
            
        except Exception as e:
            logger.error(f"Failed to process {provider_name}: {e}")
            all_results[provider_name] = {'success': [], 'failed': []}
    
    # Calculate overall statistics
    end_time = datetime.now()
    duration = (end_time - start_time).total_seconds()
    
    total_success = sum(len(r['success']) for r in all_results.values())
    total_failed = sum(len(r['failed']) for r in all_results.values())
    total_processed = total_success + total_failed
    
    # Print summary
    logger.info("\n" + "="*80)
    logger.info("BACKFILL SUMMARY")
    logger.info("="*80)
    logger.info(f"Providers: {', '.join(providers)}")
    logger.info(f"Storage Type: {storage_type}")
    logger.info(f"Total Markets Processed: {total_processed}")
    logger.info(f"Successful: {total_success}")
    logger.info(f"Failed: {total_failed}")
    logger.info(f"Duration: {duration:.1f} seconds ({duration/60:.1f} minutes)")
    
    logger.info("\nPer-Provider Results:")
    for provider, result in all_results.items():
        success_count = len(result['success'])
        failed_count = len(result['failed'])
        logger.info(f"  {provider}: {success_count} success, {failed_count} failed")
    
    logger.info("="*80)
    
    return all_results


def main():
    """Main entry point for the backfill script."""
    parser = argparse.ArgumentParser(
        description='Backfill prediction market data from supported providers',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Backfill Polymarket data
  python scripts/backfill_prediction_markets.py --provider polymarket
  
  # Backfill multiple providers
  python scripts/backfill_prediction_markets.py --provider polymarket,kalshi
  
  # Backfill with category filter
  python scripts/backfill_prediction_markets.py --provider polymarket --category crypto
  
  # Use SQLite storage
  python scripts/backfill_prediction_markets.py --provider polymarket --storage sqlite
        """
    )
    
    parser.add_argument(
        '--provider',
        required=True,
        help='Comma-separated list of providers (polymarket, kalshi)'
    )
    parser.add_argument(
        '--market-ids',
        help='Comma-separated list of specific market IDs'
    )
    parser.add_argument(
        '--category',
        help='Category filter (e.g., crypto, politics, sports)'
    )
    parser.add_argument(
        '--limit',
        type=int,
        default=100,
        help='Maximum number of markets per provider (default: 100)'
    )
    parser.add_argument(
        '--storage',
        choices=['csv', 'sqlite'],
        default='csv',
        help='Storage backend (default: csv)'
    )
    parser.add_argument(
        '--base-path',
        default='data/prediction_markets',
        help='Base path for CSV storage (default: data/prediction_markets)'
    )
    parser.add_argument(
        '--db-path',
        help='Path to SQLite database (default: data/prediction_markets/prediction_markets.db)'
    )
    parser.add_argument(
        '--rate-limit-delay',
        type=float,
        default=0.5,
        help='Delay between API calls in seconds (default: 0.5)'
    )
    parser.add_argument(
        '--log-dir',
        default='data/logs',
        help='Directory for log files (default: data/logs)'
    )
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Enable verbose (DEBUG) logging'
    )
    
    args = parser.parse_args()
    
    # Setup logging
    setup_logging(args.log_dir, args.verbose)
    logger = logging.getLogger(__name__)
    
    # Parse providers
    providers = [p.strip().lower() for p in args.provider.split(',')]
    
    # Parse market IDs if provided
    market_ids = None
    if args.market_ids:
        market_ids = [m.strip() for m in args.market_ids.split(',')]
    
    # Run backfill
    try:
        results = backfill_prediction_markets(
            providers=providers,
            market_ids=market_ids,
            category=args.category,
            limit=args.limit,
            storage_type=args.storage,
            base_path=args.base_path,
            db_path=args.db_path,
            rate_limit_delay=args.rate_limit_delay
        )
        
        # Exit with error code if there were failures
        total_failed = sum(len(r['failed']) for r in results.values())
        if total_failed > 0:
            logger.warning(f"Backfill completed with {total_failed} failures")
            sys.exit(1)
        else:
            logger.info("Backfill completed successfully!")
            sys.exit(0)
            
    except Exception as e:
        logger.error(f"Backfill failed with error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == '__main__':
    main()
