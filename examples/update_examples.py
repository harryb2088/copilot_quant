"""
Data Update and Backfill Examples

This script demonstrates how to use the DataUpdater for incremental updates
and backfilling historical data.

Run this script to see update/backfill examples:
    python examples/update_examples.py
"""

import logging
from datetime import datetime, timedelta
from copilot_quant.data.update_jobs import DataUpdater

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def example_incremental_update():
    """Example: Incrementally update a single symbol."""
    print("\n" + "="*80)
    print("INCREMENTAL UPDATE - Single Symbol")
    print("="*80)
    
    # Initialize updater
    updater = DataUpdater(
        storage_type='csv',
        data_dir='data/historical',
        rate_limit_delay=1.0
    )
    
    print("\nUpdating AAPL...")
    print("This will fetch only new data since the last update.")
    
    # Update single symbol
    success = updater.update_symbol('AAPL')
    
    if success:
        print("✓ Update successful!")
    else:
        print("✗ Update failed")


def example_force_update():
    """Example: Force update even if data is fresh."""
    print("\n" + "="*80)
    print("FORCE UPDATE - Refresh All Data")
    print("="*80)
    
    updater = DataUpdater(
        storage_type='csv',
        data_dir='data/historical',
        rate_limit_delay=1.0
    )
    
    print("\nForce updating MSFT (ignores freshness check)...")
    
    # Force update
    success = updater.update_symbol('MSFT', force=True)
    
    if success:
        print("✓ Force update successful!")
    else:
        print("✗ Force update failed")


def example_batch_update():
    """Example: Update multiple symbols in batch."""
    print("\n" + "="*80)
    print("BATCH UPDATE - Multiple Symbols")
    print("="*80)
    
    updater = DataUpdater(
        storage_type='csv',
        data_dir='data/historical',
        rate_limit_delay=1.0
    )
    
    symbols = ['AAPL', 'MSFT', 'GOOGL']
    
    print(f"\nUpdating {len(symbols)} symbols: {symbols}")
    
    # Batch update
    result = updater.batch_update(symbols, max_age_days=1)
    
    print(f"\nResults:")
    print(f"  ✓ Successful: {len(result['success'])} symbols")
    print(f"    {result['success']}")
    
    if result['failed']:
        print(f"  ✗ Failed: {len(result['failed'])} symbols")
        print(f"    {result['failed']}")


def example_backfill():
    """Example: Backfill historical data."""
    print("\n" + "="*80)
    print("BACKFILL - Historical Data")
    print("="*80)
    
    updater = DataUpdater(
        storage_type='csv',
        data_dir='data/historical',
        rate_limit_delay=1.0
    )
    
    symbol = 'NVDA'
    start_date = '2023-01-01'
    
    print(f"\nBackfilling {symbol} from {start_date}...")
    print("This fetches all historical data from the start date.")
    
    # Backfill
    success = updater.backfill_symbol(symbol, start_date=start_date)
    
    if success:
        print("✓ Backfill successful!")
    else:
        print("✗ Backfill failed")


def example_batch_backfill():
    """Example: Backfill multiple symbols."""
    print("\n" + "="*80)
    print("BATCH BACKFILL - Multiple Symbols")
    print("="*80)
    
    updater = DataUpdater(
        storage_type='csv',
        data_dir='data/historical',
        rate_limit_delay=1.0
    )
    
    symbols = ['TSLA', 'NVDA']
    start_date = '2023-01-01'
    
    print(f"\nBackfilling {len(symbols)} symbols from {start_date}...")
    
    # Batch backfill
    result = updater.batch_backfill(symbols, start_date=start_date)
    
    print(f"\nResults:")
    print(f"  ✓ Successful: {len(result['success'])} symbols")
    if result['failed']:
        print(f"  ✗ Failed: {len(result['failed'])} symbols")


def example_check_status():
    """Example: Check update status of symbols."""
    print("\n" + "="*80)
    print("UPDATE STATUS - Check Freshness")
    print("="*80)
    
    updater = DataUpdater(
        storage_type='csv',
        data_dir='data/historical',
        rate_limit_delay=1.0
    )
    
    symbols = ['AAPL', 'MSFT', 'GOOGL']
    
    print(f"\nChecking status for {len(symbols)} symbols...")
    
    # Get status
    status = updater.get_update_status(symbols)
    
    print("\nStatus Report:")
    print(status.to_string(index=False))


def example_find_and_fill_gaps():
    """Example: Find and fill date gaps in data."""
    print("\n" + "="*80)
    print("GAP DETECTION AND FILLING")
    print("="*80)
    
    updater = DataUpdater(
        storage_type='csv',
        data_dir='data/historical',
        rate_limit_delay=1.0
    )
    
    symbol = 'AAPL'
    
    print(f"\nFinding gaps in {symbol} data...")
    
    # Find gaps
    gaps = updater.find_gaps(symbol)
    
    if gaps:
        print(f"\nFound {len(gaps)} date gaps:")
        for start, end in gaps:
            print(f"  Gap: {start} to {end}")
        
        print("\nFilling gaps...")
        success = updater.fill_gaps(symbol)
        
        if success:
            print("✓ All gaps filled successfully!")
        else:
            print("✗ Failed to fill some gaps")
    else:
        print(f"✓ No gaps found in {symbol} data")


def example_needs_update():
    """Example: Check if symbols need updating."""
    print("\n" + "="*80)
    print("UPDATE CHECK - Determine Freshness")
    print("="*80)
    
    updater = DataUpdater(
        storage_type='csv',
        data_dir='data/historical',
        rate_limit_delay=1.0
    )
    
    symbols = ['AAPL', 'MSFT', 'GOOGL']
    
    print("\nChecking which symbols need updating (max age: 1 day)...")
    
    for symbol in symbols:
        needs_update = updater.needs_update(symbol, max_age_days=1)
        status = "needs update" if needs_update else "is fresh"
        print(f"  {symbol}: {status}")


def example_sqlite_storage():
    """Example: Use SQLite storage instead of CSV."""
    print("\n" + "="*80)
    print("SQLITE STORAGE - Database Updates")
    print("="*80)
    
    # Initialize with SQLite storage
    updater = DataUpdater(
        storage_type='sqlite',
        db_path='data/market_data.db',
        rate_limit_delay=1.0
    )
    
    print("\nUsing SQLite database for storage...")
    print("Database path: data/market_data.db")
    
    symbol = 'AAPL'
    
    print(f"\nUpdating {symbol} in SQLite database...")
    
    success = updater.update_symbol(symbol)
    
    if success:
        print("✓ SQLite update successful!")
        print("\nData is now stored in the database and can be queried efficiently.")
    else:
        print("✗ SQLite update failed")


def example_scheduled_updates():
    """Example: Simulate scheduled daily updates."""
    print("\n" + "="*80)
    print("SCHEDULED UPDATES - Daily Maintenance")
    print("="*80)
    
    updater = DataUpdater(
        storage_type='csv',
        data_dir='data/historical',
        rate_limit_delay=1.0
    )
    
    # Simulate a daily update routine
    symbols = ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA']
    
    print(f"\nRunning daily update for {len(symbols)} symbols...")
    print("This would typically be run as a cron job or scheduled task.")
    
    result = updater.batch_update(
        symbols,
        max_age_days=1,  # Only update if data is >1 day old
        continue_on_error=True  # Don't stop on individual failures
    )
    
    print(f"\nDaily update complete:")
    print(f"  ✓ Updated: {len(result['success'])} symbols")
    
    if result['failed']:
        print(f"  ✗ Failed: {len(result['failed'])} symbols")
        print(f"    {result['failed']}")
    
    print("\nTip: Add this to a cron job for automated daily updates:")
    print("  0 6 * * * python examples/update_examples.py --scheduled")


def main():
    """Run all examples."""
    print("\n" + "#"*80)
    print("# DATA UPDATE AND BACKFILL EXAMPLES")
    print("#"*80)
    
    print("\nThese examples demonstrate efficient data management:")
    print("  • Incremental updates (fetch only new data)")
    print("  • Backfilling historical data")
    print("  • Gap detection and filling")
    print("  • Status checking and monitoring")
    
    # Run examples (commented out to avoid actual API calls)
    # Uncomment individual examples to test:
    
    # example_incremental_update()
    # example_force_update()
    # example_batch_update()
    # example_backfill()
    # example_batch_backfill()
    # example_check_status()
    # example_find_and_fill_gaps()
    # example_needs_update()
    # example_sqlite_storage()
    # example_scheduled_updates()
    
    print("\n" + "#"*80)
    print("# EXAMPLES (Commented Out)")
    print("#"*80)
    print("\nTo run these examples:")
    print("1. Uncomment the example you want to run in the main() function")
    print("2. Ensure you have internet connection for API calls")
    print("3. Run: python examples/update_examples.py")
    
    print("\n" + "#"*80)
    print("# BEST PRACTICES")
    print("#"*80)
    print("\n1. Use incremental updates for regular maintenance")
    print("2. Backfill when adding new symbols or recovering from gaps")
    print("3. Check update status before running expensive operations")
    print("4. Use SQLite for better query performance on large datasets")
    print("5. Set up scheduled updates (cron/Task Scheduler) for automation")
    print("6. Monitor failed updates and retry with error handling")


if __name__ == "__main__":
    main()
