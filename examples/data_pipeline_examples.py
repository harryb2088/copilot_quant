#!/usr/bin/env python3
"""
Example: Using the data pipeline to download S&P500 data

This script demonstrates how to:
1. Get S&P500 constituent list
2. Download historical data for stocks
3. Save data to CSV for backtesting
"""

import logging
from datetime import datetime, timedelta

import pandas as pd

from copilot_quant.data import (
    FAANG,
    MAGNIFICENT_7,
    get_data_provider,
    get_sp500_tickers,
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def example_single_stock():
    """Example: Download data for a single stock."""
    print("\n" + "="*60)
    print("EXAMPLE 1: Single Stock Data")
    print("="*60)

    # Create data provider
    provider = get_data_provider("yfinance")

    # Download 1 year of daily data for Apple
    data = provider.get_historical_data(
        symbol="AAPL",
        start_date="2023-01-01",
        end_date="2024-01-01",
    )

    print(f"\nDownloaded {len(data)} days of data for AAPL")
    print("\nFirst 5 rows:")
    print(data.head())

    print("\nData summary:")
    print(data.describe())

    # Calculate returns
    data['Daily_Return'] = data['Close'].pct_change()
    print(f"\nAverage daily return: {data['Daily_Return'].mean():.4%}")
    print(f"Volatility (std dev): {data['Daily_Return'].std():.4%}")

    return data


def example_multiple_stocks():
    """Example: Download data for multiple stocks."""
    print("\n" + "="*60)
    print("EXAMPLE 2: Multiple Stocks (FAANG)")
    print("="*60)

    provider = get_data_provider("yfinance")

    # Download data for FAANG stocks
    print(f"\nDownloading data for: {FAANG}")
    data = provider.get_multiple_symbols(
        symbols=FAANG,
        start_date="2023-01-01",
        end_date="2024-01-01",
    )

    print(f"\nData shape: {data.shape}")
    print("\nClose prices (first 5 days):")
    print(data['Close'].head())

    # Calculate correlation between stocks
    close_prices = data['Close']
    correlation = close_prices.corr()
    print("\nPrice correlation matrix:")
    print(correlation)

    return data


def example_sp500_index():
    """Example: Download S&P500 index data."""
    print("\n" + "="*60)
    print("EXAMPLE 3: S&P500 Index Data")
    print("="*60)

    provider = get_data_provider("yfinance")

    # Download S&P500 index
    sp500 = provider.get_sp500_index(
        start_date="2020-01-01",
        end_date="2024-01-01",
    )

    print(f"\nDownloaded {len(sp500)} days of S&P500 index data")
    print("\nRecent prices:")
    print(sp500.tail())

    if sp500.empty:
        print("No data available for S&P500 index")
        return sp500

    # Calculate performance
    start_price = sp500['Close'].iloc[0]
    end_price = sp500['Close'].iloc[-1]
    total_return = (end_price - start_price) / start_price

    print("\nS&P500 Performance (2020-2024):")
    print(f"  Start: ${start_price:.2f}")
    print(f"  End: ${end_price:.2f}")
    print(f"  Total Return: {total_return:.2%}")

    return sp500


def example_get_ticker_list():
    """Example: Get S&P500 constituent list."""
    print("\n" + "="*60)
    print("EXAMPLE 4: S&P500 Constituent List")
    print("="*60)

    # Use manual list (faster, no network required)
    tickers = get_sp500_tickers(source="manual")
    print(f"\nManual list contains {len(tickers)} major S&P500 stocks")
    print(f"First 20: {tickers[:20]}")

    print("\nPredefined lists:")
    print(f"  FAANG: {FAANG}")
    print(f"  Magnificent 7: {MAGNIFICENT_7}")

    return tickers


def example_save_to_csv():
    """Example: Download and save data to CSV."""
    print("\n" + "="*60)
    print("EXAMPLE 5: Save Data to CSV")
    print("="*60)

    provider = get_data_provider("yfinance")

    # Download Magnificent 7 stocks
    data = provider.get_multiple_symbols(
        symbols=MAGNIFICENT_7,
        start_date="2023-01-01",
        end_date="2024-01-01",
    )

    # Save to CSV
    output_file = "/tmp/magnificent7_2023.csv"
    data.to_csv(output_file)
    print(f"\nSaved data to: {output_file}")

    # Load it back to verify
    loaded_data = pd.read_csv(output_file, index_col=0, parse_dates=True)
    print(f"Loaded {len(loaded_data)} rows from CSV")
    print(loaded_data.head())

    return output_file


def example_backtesting_data_prep():
    """Example: Prepare data for backtesting."""
    print("\n" + "="*60)
    print("EXAMPLE 6: Backtesting Data Preparation")
    print("="*60)

    provider = get_data_provider("yfinance")

    # Get 5 years of data for backtesting
    end_date = datetime.now()
    start_date = end_date - timedelta(days=5*365)

    symbols = ["AAPL", "MSFT", "GOOGL"]
    print(f"\nPreparing backtest data for {symbols}")
    print(f"Period: {start_date.date()} to {end_date.date()}")

    data = provider.get_multiple_symbols(
        symbols=symbols,
        start_date=start_date,
        end_date=end_date,
    )

    # Extract close prices and calculate returns
    close_prices = data['Close']
    returns = close_prices.pct_change()

    print(f"\nData shape: {close_prices.shape}")
    print("\nSummary statistics:")
    print(returns.describe())

    # Check for missing data
    missing_days = close_prices.isnull().sum()
    print("\nMissing data points:")
    print(missing_days)

    return close_prices


if __name__ == "__main__":
    print("\n" + "="*70)
    print(" DATA PIPELINE EXAMPLES - COPILOT QUANT")
    print("="*70)

    try:
        # Run examples
        example_single_stock()
        example_multiple_stocks()
        example_sp500_index()
        example_get_ticker_list()
        example_save_to_csv()
        example_backtesting_data_prep()

        print("\n" + "="*70)
        print(" ALL EXAMPLES COMPLETED SUCCESSFULLY")
        print("="*70)

    except Exception as e:
        logger.error(f"Example failed: {e}", exc_info=True)
        print("\nNote: Some examples may fail without internet access")
