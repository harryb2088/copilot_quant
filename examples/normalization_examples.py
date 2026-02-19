"""
Data Normalization and Quality Examples

This script demonstrates how to use the data normalization utilities
for cleaning, standardizing, and validating market data.

Run this script to see normalization examples:
    python examples/normalization_examples.py
"""

import pandas as pd
import numpy as np

from copilot_quant.data.normalization import (
    normalize_symbol,
    validate_symbol,
    normalize_timestamps,
    adjust_for_contract_roll,
    standardize_column_names,
    adjust_for_splits,
    detect_missing_data,
    validate_data_quality,
    fill_missing_data,
    remove_outliers,
    resample_data,
)


def example_symbol_normalization():
    """Example: Normalize stock symbols for different data sources."""
    print("\n" + "="*80)
    print("SYMBOL NORMALIZATION")
    print("="*80)
    
    # Symbols with different formats
    symbols = ['BRK.B', 'BRK-B', 'aapl', 'MSFT ', ' googl']
    
    print("\nNormalizing symbols for Yahoo Finance:")
    for symbol in symbols:
        normalized = normalize_symbol(symbol, source='yahoo')
        print(f"  {symbol!r:15s} -> {normalized!r}")
    
    print("\nNormalizing symbols for Alpha Vantage:")
    for symbol in symbols:
        normalized = normalize_symbol(symbol, source='alpha_vantage')
        print(f"  {symbol!r:15s} -> {normalized!r}")
    
    print("\nNormalizing symbols for Interactive Brokers:")
    for symbol in ['BRK.B', 'BRK-B']:
        normalized = normalize_symbol(symbol, source='ib')
        print(f"  {symbol!r:15s} -> {normalized!r}")
    
    print("\nNormalizing symbols for Quandl:")
    for symbol in ['BRK/B', 'BRK.B']:
        normalized = normalize_symbol(symbol, source='quandl')
        print(f"  {symbol!r:15s} -> {normalized!r}")
    
    # Symbol validation
    print("\n" + "-"*80)
    print("SYMBOL VALIDATION")
    print("-"*80)
    
    test_symbols = ['AAPL', 'BRK-B', '', 'MSFT', None]
    print("\nValidating symbols:")
    for symbol in test_symbols:
        valid = validate_symbol(symbol, source='yahoo')
        status = "✓ Valid" if valid else "✗ Invalid"
        print(f"  {str(symbol)!r:15s} -> {status}")


def example_column_standardization():
    """Example: Standardize DataFrame column names."""
    print("\n" + "="*80)
    print("COLUMN NAME STANDARDIZATION")
    print("="*80)
    
    # Create DataFrame with various column name formats
    df = pd.DataFrame({
        'Open': [100, 101, 102],
        'High': [105, 106, 107],
        'Low': [99, 100, 101],
        'Close': [104, 105, 106],
        'Adj Close': [103, 104, 105],
        'Volume': [1000000, 1100000, 1200000],
        'Stock Splits': [0, 0, 0],
    })
    
    print("\nOriginal columns:")
    print(f"  {df.columns.tolist()}")
    
    # Standardize column names
    standardized = standardize_column_names(df)
    
    print("\nStandardized columns:")
    print(f"  {standardized.columns.tolist()}")
    
    print("\nFirst few rows:")
    print(standardized.head())


def example_timestamp_normalization():
    """Example: Normalize timestamps to appropriate timezones."""
    print("\n" + "="*80)
    print("TIMESTAMP NORMALIZATION")
    print("="*80)
    
    # Create sample data with UTC timestamps
    dates = pd.date_range('2024-01-01', periods=5, tz='UTC')
    df = pd.DataFrame({
        'date': dates,
        'close': [100, 101, 102, 103, 104],
    })
    
    print("\nOriginal data (UTC):")
    print(df[['date', 'close']].head())
    
    # Normalize to NYSE timezone for equity data
    equity_df = normalize_timestamps(df.copy(), market_type='equity')
    print("\nNormalized to NYSE timezone (US/Eastern) for equities:")
    print(equity_df[['date', 'close']].head())
    
    # Normalize to UTC for prediction markets
    prediction_df = normalize_timestamps(df.copy(), market_type='prediction')
    print("\nNormalized to UTC for prediction markets:")
    print(prediction_df[['date', 'close']].head())
    
    # Normalize to custom timezone
    custom_df = normalize_timestamps(df.copy(), target_timezone='Asia/Tokyo')
    print("\nNormalized to custom timezone (Asia/Tokyo):")
    print(custom_df[['date', 'close']].head())


def example_contract_roll_adjustment():
    """Example: Adjust futures prices for contract rolls."""
    print("\n" + "="*80)
    print("CONTRACT ROLL ADJUSTMENT")
    print("="*80)
    
    # Create sample futures data
    df = pd.DataFrame({
        'date': pd.date_range('2024-01-01', periods=10),
        'close': [100.0, 101.0, 102.0, 103.0, 104.0, 
                  105.25, 106.25, 107.25, 108.25, 109.25],
    })
    
    print("\nOriginal futures prices:")
    print(df[['date', 'close']].head(8))
    
    # Apply manual contract roll adjustment
    # Roll happened on 2024-01-06, front contract was $0.25 cheaper
    adjusted = adjust_for_contract_roll(
        df,
        roll_date='2024-01-06',
        adjustment=-0.25,
        front_contract_column='close',
        method='difference'
    )
    
    print("\nAfter contract roll adjustment (difference method):")
    print(adjusted[['date', 'close']].head(8))
    
    print("\nNote: Prices before the roll date are adjusted by -0.25 to maintain continuity.")
    
    # Example with front and back contract data
    df_auto = pd.DataFrame({
        'date': pd.date_range('2024-01-01', periods=10),
        'front_close': [100.0, 101.0, 102.0, 103.0, 104.0,
                        105.0, 106.0, 107.0, 108.0, 109.0],
        'back_close': [100.5, 101.5, 102.5, 103.5, 104.5,
                       105.5, 106.5, 107.5, 108.5, 109.5],
    })
    
    # Auto-calculate adjustment from spread
    auto_adjusted = adjust_for_contract_roll(
        df_auto,
        roll_date='2024-01-06',
        front_contract_column='front_close',
        back_contract_column='back_close',
        method='difference'
    )
    
    print("\nWith automatic adjustment calculation from contract spread:")
    print(auto_adjusted[['date', 'front_close', 'back_close']].head(8))


def example_split_adjustment():
    """Example: Adjust prices for stock splits."""
    print("\n" + "="*80)
    print("STOCK SPLIT ADJUSTMENT")
    print("="*80)
    
    # Create sample data
    df = pd.DataFrame({
        'date': pd.date_range('2024-01-01', periods=10),
        'open': [100, 101, 102, 103, 104, 105, 106, 107, 108, 109],
        'high': [105, 106, 107, 108, 109, 110, 111, 112, 113, 114],
        'low': [99, 100, 101, 102, 103, 104, 105, 106, 107, 108],
        'close': [104, 105, 106, 107, 108, 109, 110, 111, 112, 113],
        'volume': [1000000] * 10,
    })
    
    print("\nOriginal prices (before split):")
    print(df[['date', 'close']].head())
    
    # Apply 2-for-1 split on day 5
    split_date = '2024-01-05'
    adjusted = adjust_for_splits(df, split_ratio=2.0, split_date=split_date)
    
    print(f"\nAfter 2-for-1 split on {split_date}:")
    print(adjusted[['date', 'close']].head())
    
    print("\nNote: Prices before the split date are halved to maintain continuity.")


def example_missing_data_detection():
    """Example: Detect missing data and gaps."""
    print("\n" + "="*80)
    print("MISSING DATA DETECTION")
    print("="*80)
    
    # Create data with various issues
    df = pd.DataFrame({
        'date': pd.date_range('2024-01-01', periods=10),
        'open': [100, np.nan, 102, 103, 104, 105, 106, 107, 108, 109],
        'close': [104, 105, np.nan, 107, 108, 109, 110, 111, 112, 113],
        'volume': [1000000, 0, 1200000, 1300000, 1400000, 0, 1600000, 1700000, 1800000, 1900000],
    })
    
    print("\nDetecting issues in the data...")
    issues = detect_missing_data(df)
    
    print(f"\nMissing values: {len(issues['missing_values'])}")
    for issue in issues['missing_values'][:5]:  # Show first 5
        print(f"  Column '{issue['column']}' at index {issue['index']}")
    
    print(f"\nZero volume days: {len(issues['zero_volume'])}")
    print(f"  Indices: {issues['zero_volume']}")
    
    print(f"\nDate gaps: {len(issues['date_gaps'])}")
    print(f"Price anomalies: {len(issues['price_anomalies'])}")


def example_data_validation():
    """Example: Validate data quality."""
    print("\n" + "="*80)
    print("DATA QUALITY VALIDATION")
    print("="*80)
    
    # Create data with quality issues
    df_bad = pd.DataFrame({
        'open': [100, 101, 102],
        'high': [95, 106, 107],  # First row: High < Open (invalid)
        'low': [99, 100, 101],
        'close': [-5, 105, 106],  # First row: Negative close (invalid)
        'volume': [1000000, 1100000, 1200000],
    })
    
    print("\nValidating data with issues...")
    errors = validate_data_quality(df_bad)
    
    if errors:
        print(f"\nFound {len(errors)} validation errors:")
        for i, error in enumerate(errors, 1):
            print(f"  {i}. {error}")
    
    # Create valid data
    df_good = pd.DataFrame({
        'open': [100, 101, 102],
        'high': [105, 106, 107],
        'low': [99, 100, 101],
        'close': [104, 105, 106],
        'volume': [1000000, 1100000, 1200000],
    })
    
    print("\nValidating clean data...")
    errors = validate_data_quality(df_good)
    
    if not errors:
        print("  ✓ No validation errors - data is clean!")
    else:
        print(f"  Found {len(errors)} errors")


def example_fill_missing():
    """Example: Fill missing data using various methods."""
    print("\n" + "="*80)
    print("FILLING MISSING DATA")
    print("="*80)
    
    # Create data with missing values
    df = pd.DataFrame({
        'close': [100, np.nan, np.nan, 103, 104, np.nan, 106],
    })
    
    print("\nOriginal data with missing values:")
    print(df)
    
    # Forward fill
    filled_ffill = fill_missing_data(df.copy(), method='ffill')
    print("\nForward fill (ffill):")
    print(filled_ffill)
    
    # Backward fill
    filled_bfill = fill_missing_data(df.copy(), method='bfill')
    print("\nBackward fill (bfill):")
    print(filled_bfill)
    
    # Interpolation
    filled_interp = fill_missing_data(df.copy(), method='interpolate')
    print("\nLinear interpolation:")
    print(filled_interp)


def example_outlier_removal():
    """Example: Remove outliers from data."""
    print("\n" + "="*80)
    print("OUTLIER REMOVAL")
    print("="*80)
    
    # Create data with outliers
    df = pd.DataFrame({
        'close': [100, 101, 102, 103, 104, 105, 200, 106, 107, 108],  # 200 is outlier
    })
    
    print("\nOriginal data with outlier (200):")
    print(df['close'].tolist())
    
    # Remove outliers using IQR method
    cleaned = remove_outliers(df, column='close', method='iqr', threshold=1.5)
    
    print("\nAfter removing outliers (IQR method):")
    print(f"  Original: {len(df)} rows")
    print(f"  Cleaned: {len(cleaned)} rows")
    print(f"  Values: {cleaned['close'].tolist()}")


def example_data_resampling():
    """Example: Resample time series data."""
    print("\n" + "="*80)
    print("DATA RESAMPLING")
    print("="*80)
    
    # Create daily data
    dates = pd.date_range('2024-01-01', periods=14, freq='D')
    df = pd.DataFrame({
        'open': range(100, 114),
        'high': range(105, 119),
        'low': range(99, 113),
        'close': range(104, 118),
        'volume': [1000000] * 14,
    }, index=dates)
    
    print("\nDaily data (14 days):")
    print(df[['open', 'close', 'volume']].head())
    print(f"  Total rows: {len(df)}")
    
    # Resample to weekly
    weekly = resample_data(df, freq='W')
    
    print("\nResampled to weekly:")
    print(weekly[['open', 'close', 'volume']].head())
    print(f"  Total rows: {len(weekly)}")
    
    print("\nNote: Open uses first value, Close uses last value, Volume is summed")


def main():
    """Run all examples."""
    print("\n" + "#"*80)
    print("# DATA NORMALIZATION AND QUALITY EXAMPLES")
    print("#"*80)
    
    example_symbol_normalization()
    example_column_standardization()
    example_timestamp_normalization()
    example_contract_roll_adjustment()
    example_split_adjustment()
    example_missing_data_detection()
    example_data_validation()
    example_fill_missing()
    example_outlier_removal()
    example_data_resampling()
    
    print("\n" + "#"*80)
    print("# EXAMPLES COMPLETE")
    print("#"*80)
    print("\nThese normalization utilities help ensure data quality for backtesting.")
    print("\nKey takeaways:")
    print("  • Always validate data quality before use")
    print("  • Normalize symbols and timestamps for consistency across data sources")
    print("  • Handle missing data appropriately for your use case")
    print("  • Adjust for corporate actions (splits, dividends, contract rolls)")
    print("  • Standardize column names across different data sources")
    print("  • Remove outliers carefully to avoid losing valid data")
    print("  • Use appropriate timezones for different market types")
    print("    - Equities: NYSE timezone (US/Eastern)")
    print("    - Prediction Markets: UTC")
    print("    - Futures: Depends on exchange (e.g., CME uses US/Central)")


if __name__ == "__main__":
    main()
