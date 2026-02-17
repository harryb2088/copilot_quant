#!/usr/bin/env python3
"""
Daily Prediction Markets Data Update Script

This script performs daily updates of prediction market data from supported
platforms. It refreshes market lists and updates prices for active markets.

Usage:
    # Update all active markets from Polymarket
    python scripts/daily_update_prediction_markets.py --provider polymarket
    
    # Update multiple providers
    python scripts/daily_update_prediction_markets.py --provider polymarket,kalshi
    
    # Use SQLite storage
    python scripts/daily_update_prediction_markets.py --provider polymarket --storage sqlite

Features:
    - Updates active market lists
    - Refreshes price/probability data
    - Progress tracking and status reporting
    - Comprehensive error handling and logging
    - Multi-provider support
    - Detailed summary statistics

Recommended for:
    - Daily cron jobs
    - Scheduled task automation
    - Regular maintenance updates
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
    Configure logging for the daily update script.
    
    Args:
        log_dir: Directory for log files
        verbose: Enable verbose (DEBUG) logging
    """
    log_path = Path(log_dir)
    log_path.mkdir(parents=True, exist_ok=True)
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    log_file = log_path / f'daily_update_prediction_markets_{timestamp}.log'
    
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


def update_provider_markets(
    provider_name: str,
    storage: PredictionMarketStorage,
    category: Optional[str] = None,
    limit: int = 100,
    update_prices: bool = True,
    rate_limit_delay: float = 0.5
) -> dict:
    """
    Update markets for a specific provider.
    
    Args:
        provider_name: Name of the provider
        storage: Storage instance
        category: Optional category filter
        limit: Maximum number of markets to fetch
        update_prices: Whether to update price data
        rate_limit_delay: Delay between API calls
        
    Returns:
        Dictionary with 'markets_updated', 'prices_updated', and 'failed' counts
    """
    logger = logging.getLogger(__name__)
    
    logger.info(f"Starting daily update for {provider_name}...")
    
    # Initialize provider
    provider = get_provider(provider_name, rate_limit_delay=rate_limit_delay)
    
    markets_updated = 0
    prices_updated = 0
    failed = []
    
    # Fetch and update active markets list
    logger.info(f"Fetching active markets from {provider_name}...")
    try:
        markets_df = provider.get_active_markets(category=category, limit=limit)
        
        if markets_df.empty:
            logger.warning(f"No active markets found for {provider_name}")
            return {'markets_updated': 0, 'prices_updated': 0, 'failed': []}
        
        # Save markets list
        storage.save_markets(provider_name, markets_df)
        markets_updated = len(markets_df)
        logger.info(f"Updated {markets_updated} markets from {provider_name}")
        
        # Update price data if requested
        if update_prices:
            logger.info(f"Updating price data for {len(markets_df)} markets...")
            
            market_ids = markets_df['market_id'].tolist()
            
            for i, market_id in enumerate(market_ids):
                if (i + 1) % 10 == 0:
                    logger.info(f"Progress: {i+1}/{len(market_ids)} markets")
                
                try:
                    # Get market price data
                    prices_df = provider.get_market_prices(market_id)
                    
                    if not prices_df.empty:
                        storage.save_market_data(provider_name, market_id, prices_df)
                        prices_updated += 1
                    else:
                        logger.debug(f"No price data for market {market_id}")
                        
                except Exception as e:
                    logger.warning(f"Failed to update prices for market {market_id}: {e}")
                    failed.append(market_id)
            
            logger.info(f"Updated prices for {prices_updated}/{len(market_ids)} markets")
        
    except Exception as e:
        logger.error(f"Failed to update markets from {provider_name}: {e}")
        return {'markets_updated': 0, 'prices_updated': 0, 'failed': []}
    
    return {
        'markets_updated': markets_updated,
        'prices_updated': prices_updated,
        'failed': failed
    }


def save_update_summary(
    summary_file: Path,
    providers: List[str],
    results: dict,
    duration: float
) -> None:
    """
    Save update summary to file.
    
    Args:
        summary_file: Path to summary file
        providers: List of provider names
        results: Results dictionary
        duration: Duration in seconds
    """
    timestamp = datetime.now().isoformat()
    
    total_markets = sum(r['markets_updated'] for r in results.values())
    total_prices = sum(r['prices_updated'] for r in results.values())
    total_failed = sum(len(r['failed']) for r in results.values())
    
    # Load existing summaries if available
    if summary_file.exists():
        try:
            df = pd.read_csv(summary_file)
        except Exception:
            df = pd.DataFrame(columns=[
                'timestamp', 'providers', 'markets_updated', 'prices_updated',
                'failed', 'duration_seconds'
            ])
    else:
        df = pd.DataFrame(columns=[
            'timestamp', 'providers', 'markets_updated', 'prices_updated',
            'failed', 'duration_seconds'
        ])
    
    # Append new summary
    new_row = pd.DataFrame({
        'timestamp': [timestamp],
        'providers': [','.join(providers)],
        'markets_updated': [total_markets],
        'prices_updated': [total_prices],
        'failed': [total_failed],
        'duration_seconds': [duration]
    })
    df = pd.concat([df, new_row], ignore_index=True)
    
    # Save to file
    summary_file.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(summary_file, index=False)


def daily_update_prediction_markets(
    providers: List[str],
    category: Optional[str] = None,
    limit: int = 100,
    update_prices: bool = True,
    storage_type: str = 'csv',
    base_path: str = 'data/prediction_markets',
    db_path: Optional[str] = None,
    rate_limit_delay: float = 0.5
) -> dict:
    """
    Daily update of prediction market data from multiple providers.
    
    Args:
        providers: List of provider names
        category: Optional category filter
        limit: Maximum number of markets per provider
        update_prices: Whether to update price data
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
    
    logger.info(f"Starting daily update for {len(providers)} providers")
    logger.info(f"Storage: {storage_type}")
    logger.info(f"Update prices: {update_prices}")
    
    start_time = datetime.now()
    all_results = {}
    
    # Process each provider
    for provider_name in providers:
        logger.info(f"\n{'='*80}")
        logger.info(f"Processing provider: {provider_name}")
        logger.info(f"{'='*80}")
        
        try:
            result = update_provider_markets(
                provider_name=provider_name,
                storage=storage,
                category=category,
                limit=limit,
                update_prices=update_prices,
                rate_limit_delay=rate_limit_delay
            )
            all_results[provider_name] = result
            
        except Exception as e:
            logger.error(f"Failed to process {provider_name}: {e}")
            all_results[provider_name] = {
                'markets_updated': 0,
                'prices_updated': 0,
                'failed': []
            }
    
    # Calculate overall statistics
    end_time = datetime.now()
    duration = (end_time - start_time).total_seconds()
    
    total_markets = sum(r['markets_updated'] for r in all_results.values())
    total_prices = sum(r['prices_updated'] for r in all_results.values())
    total_failed = sum(len(r['failed']) for r in all_results.values())
    
    # Save summary
    summary_file = Path(base_path) / 'update_summary.csv'
    save_update_summary(summary_file, providers, all_results, duration)
    
    # Print summary
    logger.info("\n" + "="*80)
    logger.info("DAILY UPDATE SUMMARY")
    logger.info("="*80)
    logger.info(f"Update Time: {end_time.strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info(f"Providers: {', '.join(providers)}")
    logger.info(f"Storage Type: {storage_type}")
    logger.info(f"Markets Updated: {total_markets}")
    logger.info(f"Prices Updated: {total_prices}")
    logger.info(f"Failed: {total_failed}")
    logger.info(f"Duration: {duration:.1f} seconds ({duration/60:.1f} minutes)")
    
    logger.info("\nPer-Provider Results:")
    for provider, result in all_results.items():
        logger.info(
            f"  {provider}: {result['markets_updated']} markets, "
            f"{result['prices_updated']} prices, "
            f"{len(result['failed'])} failed"
        )
    
    logger.info(f"\nSummary file: {summary_file}")
    logger.info("="*80)
    
    return all_results


def main():
    """Main entry point for the daily update script."""
    parser = argparse.ArgumentParser(
        description='Daily update for prediction market data',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Standard daily update
  python scripts/daily_update_prediction_markets.py --provider polymarket
  
  # Update multiple providers
  python scripts/daily_update_prediction_markets.py --provider polymarket,kalshi
  
  # Update with category filter
  python scripts/daily_update_prediction_markets.py --provider polymarket --category crypto
  
  # Use SQLite storage
  python scripts/daily_update_prediction_markets.py --provider polymarket --storage sqlite

Cron Job Examples:
  # Run daily at 6:00 AM
  0 6 * * * cd /path/to/copilot_quant && python scripts/daily_update_prediction_markets.py --provider polymarket
  
  # Run every 6 hours
  0 */6 * * * cd /path/to/copilot_quant && python scripts/daily_update_prediction_markets.py --provider polymarket,kalshi
        """
    )
    
    parser.add_argument(
        '--provider',
        required=True,
        help='Comma-separated list of providers (polymarket, kalshi)'
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
        '--no-update-prices',
        action='store_true',
        help='Skip updating price data (only update market lists)'
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
    
    # Run daily update
    try:
        results = daily_update_prediction_markets(
            providers=providers,
            category=args.category,
            limit=args.limit,
            update_prices=not args.no_update_prices,
            storage_type=args.storage,
            base_path=args.base_path,
            db_path=args.db_path,
            rate_limit_delay=args.rate_limit_delay
        )
        
        # Exit with error code if there were failures
        total_failed = sum(len(r['failed']) for r in results.values())
        if total_failed > 0:
            logger.warning(f"Update completed with {total_failed} failures")
            sys.exit(1)
        else:
            logger.info("Daily update completed successfully!")
            sys.exit(0)
            
    except Exception as e:
        logger.error(f"Daily update failed with error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == '__main__':
    main()
