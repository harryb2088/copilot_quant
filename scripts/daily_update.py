#!/usr/bin/env python3
"""
Daily S&P500 Data Update Script

This script performs incremental updates of market data for S&P500 stocks.
It only fetches new data since the last update, making it efficient for
daily/regular maintenance.

Usage:
    # Update all S&P500 stocks
    python scripts/daily_update.py
    
    # Update specific symbols
    python scripts/daily_update.py --symbols AAPL,MSFT,GOOGL
    
    # Force update (ignore freshness check)
    python scripts/daily_update.py --force
    
    # Use SQLite storage
    python scripts/daily_update.py --storage sqlite

Features:
    - Incremental updates (only fetches new data)
    - Automatic gap detection and filling
    - Progress tracking and status reporting
    - Comprehensive error handling and logging
    - Email/alert notifications on failures (optional)
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

from copilot_quant.data.sp500 import get_sp500_tickers
from copilot_quant.data.update_jobs import DataUpdater


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
    log_file = log_path / f'daily_update_{timestamp}.log'
    
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


def save_summary(
    summary_file: Path,
    result: dict,
    duration: float,
    total_symbols: int,
    gaps_filled: int = 0
) -> None:
    """
    Save update summary to file.
    
    Args:
        summary_file: Path to summary file
        result: Dictionary with 'success' and 'failed' lists
        duration: Duration in seconds
        total_symbols: Total number of symbols processed
        gaps_filled: Number of gaps filled
    """
    timestamp = datetime.now().isoformat()
    success_count = len(result['success'])
    failed_count = len(result['failed'])
    success_rate = (success_count / total_symbols * 100) if total_symbols > 0 else 0
    
    # Load existing summaries if available
    if summary_file.exists():
        try:
            df = pd.read_csv(summary_file)
        except Exception:
            df = pd.DataFrame(columns=[
                'timestamp', 'total_symbols', 'success', 'failed',
                'success_rate', 'duration_seconds', 'gaps_filled'
            ])
    else:
        df = pd.DataFrame(columns=[
            'timestamp', 'total_symbols', 'success', 'failed',
            'success_rate', 'duration_seconds', 'gaps_filled'
        ])
    
    # Append new summary
    new_row = pd.DataFrame({
        'timestamp': [timestamp],
        'total_symbols': [total_symbols],
        'success': [success_count],
        'failed': [failed_count],
        'success_rate': [success_rate],
        'duration_seconds': [duration],
        'gaps_filled': [gaps_filled]
    })
    df = pd.concat([df, new_row], ignore_index=True)
    
    # Save to file
    summary_file.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(summary_file, index=False)


def fill_data_gaps(
    updater: DataUpdater,
    symbols: List[str],
    max_symbols: int = 10
) -> int:
    """
    Find and fill data gaps for symbols.
    
    Args:
        updater: DataUpdater instance
        symbols: List of symbols to check
        max_symbols: Maximum number of symbols to process for gaps
        
    Returns:
        Number of symbols with gaps filled
    """
    logger = logging.getLogger(__name__)
    
    logger.info("Checking for data gaps...")
    
    gaps_filled = 0
    symbols_checked = symbols[:max_symbols]  # Limit to avoid long runs
    
    for symbol in symbols_checked:
        try:
            gaps = updater.find_gaps(symbol)
            if gaps:
                logger.info(f"{symbol}: Found {len(gaps)} gaps, filling...")
                if updater.fill_gaps(symbol):
                    gaps_filled += 1
        except Exception as e:
            logger.warning(f"{symbol}: Error checking gaps: {e}")
    
    if gaps_filled > 0:
        logger.info(f"Filled gaps for {gaps_filled} symbols")
    
    return gaps_filled


def daily_update(
    symbols: Optional[List[str]] = None,
    storage_type: str = 'csv',
    data_dir: str = 'data/historical',
    db_path: str = 'data/market_data.db',
    force: bool = False,
    max_age_days: int = 1,
    fill_gaps: bool = True,
    continue_on_error: bool = True,
    rate_limit_delay: float = 0.5
) -> dict:
    """
    Perform daily incremental update of market data.
    
    Args:
        symbols: Optional list of specific symbols (defaults to all S&P500)
        storage_type: 'csv' or 'sqlite'
        data_dir: Directory for CSV files
        db_path: Path to SQLite database
        force: Force update even if data is fresh
        max_age_days: Maximum age in days before update is needed
        fill_gaps: Whether to check and fill data gaps
        continue_on_error: Continue processing if one symbol fails
        rate_limit_delay: Delay between API calls in seconds
        
    Returns:
        Dictionary with 'success' and 'failed' symbol lists
    """
    logger = logging.getLogger(__name__)
    
    # Get symbols to process
    if symbols is None:
        logger.info("Fetching S&P500 constituent list...")
        try:
            symbols = get_sp500_tickers()
            logger.info(f"Found {len(symbols)} S&P500 stocks")
        except Exception as e:
            logger.error(f"Failed to fetch S&P500 list: {e}")
            return {'success': [], 'failed': []}
    else:
        logger.info(f"Processing {len(symbols)} specified symbols")
    
    # Initialize updater
    updater = DataUpdater(
        storage_type=storage_type,
        data_dir=data_dir,
        db_path=db_path,
        rate_limit_delay=rate_limit_delay
    )
    
    # Start update
    logger.info(f"Starting daily update for {len(symbols)} symbols")
    logger.info(f"Storage: {storage_type}")
    logger.info(f"Max age: {max_age_days} days")
    logger.info(f"Force update: {force}")
    
    start_time = datetime.now()
    
    # Run batch update
    result = updater.batch_update(
        symbols=symbols,
        force=force,
        max_age_days=max_age_days,
        continue_on_error=continue_on_error
    )
    
    # Fill gaps if requested
    gaps_filled = 0
    if fill_gaps and result['success']:
        gaps_filled = fill_data_gaps(updater, result['success'])
    
    # Calculate statistics
    end_time = datetime.now()
    duration = (end_time - start_time).total_seconds()
    
    total_processed = len(result['success']) + len(result['failed'])
    success_rate = (len(result['success']) / total_processed * 100) if total_processed > 0 else 0
    
    # Save summary
    summary_file = Path(data_dir) / 'update_summary.csv'
    save_summary(summary_file, result, duration, total_processed, gaps_filled)
    
    # Print summary
    logger.info("\n" + "="*80)
    logger.info("DAILY UPDATE SUMMARY")
    logger.info("="*80)
    logger.info(f"Update Time: {end_time.strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info(f"Storage Type: {storage_type}")
    logger.info(f"Total Symbols Processed: {total_processed}")
    logger.info(f"Successfully Updated: {len(result['success'])} ({success_rate:.1f}%)")
    logger.info(f"Failed: {len(result['failed'])}")
    if gaps_filled > 0:
        logger.info(f"Gaps Filled: {gaps_filled} symbols")
    logger.info(f"Duration: {duration:.1f} seconds ({duration/60:.1f} minutes)")
    
    if result['failed']:
        logger.warning(f"\nFailed symbols: {', '.join(result['failed'][:20])}")
        if len(result['failed']) > 20:
            logger.warning(f"... and {len(result['failed']) - 20} more")
    
    logger.info(f"\nSummary file: {summary_file}")
    logger.info("="*80)
    
    return result


def main():
    """Main entry point for the daily update script."""
    parser = argparse.ArgumentParser(
        description='Daily incremental update for S&P500 market data',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Standard daily update
  python scripts/daily_update.py
  
  # Update specific symbols
  python scripts/daily_update.py --symbols AAPL,MSFT,GOOGL
  
  # Force update (ignore freshness)
  python scripts/daily_update.py --force
  
  # Use SQLite storage
  python scripts/daily_update.py --storage sqlite --db-path data/market_data.db
  
  # Skip gap filling for faster updates
  python scripts/daily_update.py --no-fill-gaps

Cron Job Examples:
  # Run daily at 6:00 AM
  0 6 * * * cd /path/to/copilot_quant && python scripts/daily_update.py
  
  # Run Monday-Friday at 6:00 AM
  0 6 * * 1-5 cd /path/to/copilot_quant && python scripts/daily_update.py
        """
    )
    
    parser.add_argument(
        '--symbols',
        help='Comma-separated list of symbols (defaults to all S&P500)'
    )
    parser.add_argument(
        '--storage',
        choices=['csv', 'sqlite'],
        default='csv',
        help='Storage backend (default: csv)'
    )
    parser.add_argument(
        '--data-dir',
        default='data/historical',
        help='Directory for CSV files (default: data/historical)'
    )
    parser.add_argument(
        '--db-path',
        default='data/market_data.db',
        help='Path to SQLite database (default: data/market_data.db)'
    )
    parser.add_argument(
        '--force',
        action='store_true',
        help='Force update even if data is fresh'
    )
    parser.add_argument(
        '--max-age-days',
        type=int,
        default=1,
        help='Maximum age in days before update is needed (default: 1)'
    )
    parser.add_argument(
        '--no-fill-gaps',
        action='store_true',
        help='Skip gap detection and filling'
    )
    parser.add_argument(
        '--continue-on-error',
        action='store_true',
        default=True,
        help='Continue processing if one symbol fails (default: True)'
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
    
    # Parse symbols if provided
    symbols = None
    if args.symbols:
        symbols = [s.strip() for s in args.symbols.split(',')]
    
    # Run daily update
    try:
        result = daily_update(
            symbols=symbols,
            storage_type=args.storage,
            data_dir=args.data_dir,
            db_path=args.db_path,
            force=args.force,
            max_age_days=args.max_age_days,
            fill_gaps=not args.no_fill_gaps,
            continue_on_error=args.continue_on_error,
            rate_limit_delay=args.rate_limit_delay
        )
        
        # Exit with error code if there were failures
        if result['failed']:
            logger.warning(f"Update completed with {len(result['failed'])} failures")
            sys.exit(1)
        else:
            logger.info("Daily update completed successfully!")
            sys.exit(0)
            
    except Exception as e:
        logger.error(f"Daily update failed with error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == '__main__':
    main()
