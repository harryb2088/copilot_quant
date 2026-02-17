#!/usr/bin/env python3
"""
S&P500 Historical Data Backfill Script

This script performs a complete historical backfill of market data for all S&P500 
constituent stocks. It fetches historical price data and stores it in the configured
storage backend (CSV or SQLite).

Usage:
    # Backfill all S&P500 stocks from 2020-01-01 to present
    python scripts/backfill_sp500.py --start-date 2020-01-01
    
    # Backfill specific symbols
    python scripts/backfill_sp500.py --symbols AAPL,MSFT,GOOGL --start-date 2020-01-01
    
    # Use SQLite storage
    python scripts/backfill_sp500.py --storage sqlite --start-date 2020-01-01
    
    # Continue on errors
    python scripts/backfill_sp500.py --start-date 2020-01-01 --continue-on-error

Features:
    - Fetches complete historical data for all S&P500 symbols
    - Progress tracking and status reporting
    - Comprehensive error handling and logging
    - Configurable storage backend (CSV/SQLite)
    - Resume capability for interrupted runs
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

from copilot_quant.data.sp500 import get_sp500_tickers
from copilot_quant.data.update_jobs import DataUpdater


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
    log_file = log_path / f'backfill_sp500_{timestamp}.log'
    
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


def load_processed_symbols(status_file: Path) -> set:
    """
    Load previously processed symbols from status file.
    
    Args:
        status_file: Path to status file
        
    Returns:
        Set of successfully processed symbols
    """
    if not status_file.exists():
        return set()
    
    try:
        df = pd.read_csv(status_file)
        return set(df[df['status'] == 'success']['symbol'].tolist())
    except Exception as e:
        logging.getLogger(__name__).warning(f"Could not load status file: {e}")
        return set()


def save_status(
    status_file: Path,
    symbol: str,
    status: str,
    message: str = ''
) -> None:
    """
    Save processing status for a symbol.
    
    Args:
        status_file: Path to status file
        symbol: Stock ticker symbol
        status: 'success' or 'failed'
        message: Optional status message
    """
    timestamp = datetime.now().isoformat()
    
    # Load existing status if available
    if status_file.exists():
        try:
            df = pd.read_csv(status_file)
        except Exception:
            df = pd.DataFrame(columns=['symbol', 'status', 'timestamp', 'message'])
    else:
        df = pd.DataFrame(columns=['symbol', 'status', 'timestamp', 'message'])
    
    # Update or append status
    mask = df['symbol'] == symbol
    if mask.any():
        df.loc[mask, 'status'] = status
        df.loc[mask, 'timestamp'] = timestamp
        df.loc[mask, 'message'] = message
    else:
        new_row = pd.DataFrame({
            'symbol': [symbol],
            'status': [status],
            'timestamp': [timestamp],
            'message': [message]
        })
        df = pd.concat([df, new_row], ignore_index=True)
    
    # Save to file
    status_file.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(status_file, index=False)


def backfill_sp500(
    start_date: str,
    end_date: Optional[str] = None,
    symbols: Optional[List[str]] = None,
    storage_type: str = 'csv',
    data_dir: str = 'data/historical',
    db_path: str = 'data/market_data.db',
    continue_on_error: bool = True,
    resume: bool = True,
    rate_limit_delay: float = 0.5
) -> dict:
    """
    Backfill historical data for S&P500 stocks.
    
    Args:
        start_date: Start date in 'YYYY-MM-DD' format
        end_date: End date in 'YYYY-MM-DD' format (defaults to today)
        symbols: Optional list of specific symbols (defaults to all S&P500)
        storage_type: 'csv' or 'sqlite'
        data_dir: Directory for CSV files
        db_path: Path to SQLite database
        continue_on_error: Continue processing if one symbol fails
        resume: Resume from previous run (skip already processed symbols)
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
    
    # Status tracking
    status_file = Path(data_dir) / 'backfill_status.csv'
    processed_symbols = load_processed_symbols(status_file) if resume else set()
    
    if processed_symbols:
        logger.info(f"Resuming from previous run. {len(processed_symbols)} symbols already processed.")
        symbols = [s for s in symbols if s not in processed_symbols]
        logger.info(f"Remaining symbols to process: {len(symbols)}")
    
    # Start backfill
    logger.info(f"Starting backfill from {start_date} to {end_date or 'present'}")
    logger.info(f"Storage: {storage_type}")
    logger.info(f"Total symbols: {len(symbols)}")
    
    start_time = datetime.now()
    
    # Run batch backfill
    result = updater.batch_backfill(
        symbols=symbols,
        start_date=start_date,
        end_date=end_date,
        continue_on_error=continue_on_error
    )
    
    # Save status for each symbol
    for symbol in result['success']:
        save_status(status_file, symbol, 'success', 'Backfill completed')
    
    for symbol in result['failed']:
        save_status(status_file, symbol, 'failed', 'Backfill failed')
    
    # Calculate statistics
    end_time = datetime.now()
    duration = (end_time - start_time).total_seconds()
    
    total_processed = len(result['success']) + len(result['failed'])
    success_rate = (len(result['success']) / total_processed * 100) if total_processed > 0 else 0
    
    # Print summary
    logger.info("\n" + "="*80)
    logger.info("BACKFILL SUMMARY")
    logger.info("="*80)
    logger.info(f"Start Date: {start_date}")
    logger.info(f"End Date: {end_date or 'present'}")
    logger.info(f"Storage Type: {storage_type}")
    logger.info(f"Total Symbols Processed: {total_processed}")
    logger.info(f"Successful: {len(result['success'])} ({success_rate:.1f}%)")
    logger.info(f"Failed: {len(result['failed'])}")
    logger.info(f"Duration: {duration:.1f} seconds ({duration/60:.1f} minutes)")
    
    if result['failed']:
        logger.warning(f"\nFailed symbols: {', '.join(result['failed'][:20])}")
        if len(result['failed']) > 20:
            logger.warning(f"... and {len(result['failed']) - 20} more")
    
    logger.info(f"\nStatus file: {status_file}")
    logger.info("="*80)
    
    return result


def main():
    """Main entry point for the backfill script."""
    parser = argparse.ArgumentParser(
        description='Backfill historical data for S&P500 stocks',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Backfill all S&P500 from 2020
  python scripts/backfill_sp500.py --start-date 2020-01-01
  
  # Backfill specific symbols
  python scripts/backfill_sp500.py --symbols AAPL,MSFT,GOOGL --start-date 2020-01-01
  
  # Use SQLite storage
  python scripts/backfill_sp500.py --storage sqlite --start-date 2020-01-01 --db-path data/market_data.db
  
  # Resume interrupted backfill
  python scripts/backfill_sp500.py --start-date 2020-01-01 --resume
        """
    )
    
    parser.add_argument(
        '--start-date',
        required=True,
        help='Start date for backfill (YYYY-MM-DD)'
    )
    parser.add_argument(
        '--end-date',
        help='End date for backfill (YYYY-MM-DD). Defaults to today.'
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
        '--continue-on-error',
        action='store_true',
        help='Continue processing if one symbol fails'
    )
    parser.add_argument(
        '--resume',
        action='store_true',
        help='Resume from previous run'
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
    
    # Run backfill
    try:
        result = backfill_sp500(
            start_date=args.start_date,
            end_date=args.end_date,
            symbols=symbols,
            storage_type=args.storage,
            data_dir=args.data_dir,
            db_path=args.db_path,
            continue_on_error=True,  # Always continue on error by default
            resume=True,  # Always resume by default
            rate_limit_delay=args.rate_limit_delay
        )
        
        # Exit with error code if there were failures
        if result['failed']:
            logger.warning(f"Backfill completed with {len(result['failed'])} failures")
            sys.exit(1)
        else:
            logger.info("Backfill completed successfully!")
            sys.exit(0)
            
    except Exception as e:
        logger.error(f"Backfill failed with error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == '__main__':
    main()
