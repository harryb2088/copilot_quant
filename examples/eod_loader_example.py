"""
Example script demonstrating the use of SP500EODLoader

This script shows how to:
1. Fetch historical data for a single symbol
2. Fetch data for multiple symbols from a CSV file
3. Save data to CSV files
4. Save data to SQLite database
5. Load data back from storage
"""

from copilot_quant.data.eod_loader import SP500EODLoader
from datetime import datetime, timedelta


def example_single_symbol_csv():
    """Example 1: Fetch and save a single symbol to CSV"""
    print("=" * 60)
    print("Example 1: Single Symbol to CSV")
    print("=" * 60)
    
    # Initialize loader for CSV storage
    loader = SP500EODLoader(
        symbols=['AAPL'],
        storage_type='csv',
        data_dir='data/historical'
    )
    
    # Define date range (last 30 days)
    end_date = datetime.now().strftime('%Y-%m-%d')
    start_date = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
    
    # Fetch and save data
    print(f"Fetching AAPL data from {start_date} to {end_date}...")
    success = loader.fetch_and_save('AAPL', start_date=start_date, end_date=end_date)
    
    if success:
        print("✓ Data fetched and saved successfully!")
        print("  File: data/historical/equity_AAPL.csv")
        
        # Load and display the data
        df = loader.load_from_csv('AAPL')
        if df is not None:
            print("\nData preview (first 5 rows):")
            print(df.head())
    else:
        print("✗ Failed to fetch data")
    
    print()


def example_multiple_symbols_csv():
    """Example 2: Fetch multiple symbols from CSV file"""
    print("=" * 60)
    print("Example 2: Multiple Symbols from CSV File")
    print("=" * 60)
    
    # Initialize loader with symbols file
    loader = SP500EODLoader(
        symbols_file='data/sp500_symbols.csv',
        storage_type='csv',
        data_dir='data/historical',
        rate_limit_delay=1.0  # 1 second delay between requests
    )
    
    print(f"Loaded {len(loader.symbols)} symbols from file")
    print(f"Symbols: {', '.join(loader.symbols[:5])}...")
    
    # Define date range (last 7 days for faster example)
    end_date = datetime.now().strftime('%Y-%m-%d')
    start_date = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')
    
    # Fetch all symbols
    print(f"\nFetching data from {start_date} to {end_date}...")
    print("(This may take a while with rate limiting...)")
    
    result = loader.fetch_all(
        start_date=start_date,
        end_date=end_date,
        continue_on_error=True
    )
    
    print("\n✓ Complete!")
    print(f"  Successful: {len(result['success'])} symbols")
    print(f"  Failed: {len(result['failed'])} symbols")
    
    if result['success']:
        print(f"  Success examples: {', '.join(result['success'][:3])}")
    if result['failed']:
        print(f"  Failed examples: {', '.join(result['failed'][:3])}")
    
    print()


def example_sqlite_storage():
    """Example 3: Fetch and save to SQLite database"""
    print("=" * 60)
    print("Example 3: SQLite Database Storage")
    print("=" * 60)
    
    # Initialize loader for SQLite storage
    loader = SP500EODLoader(
        symbols=['AAPL', 'MSFT', 'GOOGL'],
        storage_type='sqlite',
        db_path='data/market_data.db',
        rate_limit_delay=1.0
    )
    
    print(f"Symbols to fetch: {', '.join(loader.symbols)}")
    
    # Define date range
    end_date = datetime.now().strftime('%Y-%m-%d')
    start_date = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')
    
    # Fetch all symbols
    print(f"\nFetching data from {start_date} to {end_date}...")
    result = loader.fetch_all(
        start_date=start_date,
        end_date=end_date,
        continue_on_error=True
    )
    
    print("\n✓ Data saved to database: data/market_data.db")
    print(f"  Successful: {len(result['success'])} symbols")
    print(f"  Failed: {len(result['failed'])} symbols")
    
    # Load data back from database
    if result['success']:
        symbol = result['success'][0]
        print(f"\nLoading {symbol} from database...")
        df = loader.load_from_sqlite(symbol)
        if df is not None:
            print(f"Loaded {len(df)} rows")
            print("\nData preview (first 5 rows):")
            print(df.head())
    
    print()


def example_date_range_query():
    """Example 4: Query specific date range from SQLite"""
    print("=" * 60)
    print("Example 4: Date Range Query from SQLite")
    print("=" * 60)
    
    # Initialize loader (assuming database already has data)
    loader = SP500EODLoader(
        storage_type='sqlite',
        db_path='data/market_data.db'
    )
    
    # Query specific date range
    symbol = 'AAPL'
    start_date = '2024-01-01'
    end_date = '2024-01-31'
    
    print(f"Querying {symbol} from {start_date} to {end_date}...")
    df = loader.load_from_sqlite(symbol, start_date=start_date, end_date=end_date)
    
    if df is not None and not df.empty:
        print(f"✓ Found {len(df)} trading days")
        print("\nData summary:")
        print(df[['date', 'open', 'high', 'low', 'close', 'volume']].head(10))
    else:
        print("No data found for this date range")
    
    print()


def example_custom_symbols():
    """Example 5: Fetch custom list of symbols"""
    print("=" * 60)
    print("Example 5: Custom Symbol List")
    print("=" * 60)
    
    # Define custom symbol list
    custom_symbols = ['NVDA', 'AMD', 'INTC', 'TSM']
    
    # Initialize loader
    loader = SP500EODLoader(
        symbols=custom_symbols,
        storage_type='csv',
        data_dir='data/historical',
        rate_limit_delay=1.0
    )
    
    print(f"Fetching semiconductor stocks: {', '.join(custom_symbols)}")
    
    # Fetch recent month
    end_date = datetime.now().strftime('%Y-%m-%d')
    start_date = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
    
    print(f"Date range: {start_date} to {end_date}")
    
    result = loader.fetch_all(
        start_date=start_date,
        end_date=end_date,
        continue_on_error=True
    )
    
    print("\n✓ Complete!")
    print(f"  Successful: {len(result['success'])} symbols")
    print(f"  Failed: {len(result['failed'])} symbols")
    
    print()


if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("SP500 EOD Loader - Usage Examples")
    print("=" * 60 + "\n")
    
    print("Choose an example to run:")
    print("1. Single symbol to CSV")
    print("2. Multiple symbols from CSV file")
    print("3. SQLite database storage")
    print("4. Date range query from SQLite")
    print("5. Custom symbol list")
    print("6. Run all examples")
    
    choice = input("\nEnter choice (1-6): ").strip()
    
    examples = {
        '1': example_single_symbol_csv,
        '2': example_multiple_symbols_csv,
        '3': example_sqlite_storage,
        '4': example_date_range_query,
        '5': example_custom_symbols,
    }
    
    if choice in examples:
        examples[choice]()
    elif choice == '6':
        for func in examples.values():
            func()
    else:
        print("Invalid choice!")
