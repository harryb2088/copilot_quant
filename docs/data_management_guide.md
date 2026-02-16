# Data Management Guide

## Overview

This guide covers the data normalization, quality validation, and update utilities available in Copilot Quant. These tools help ensure clean, consistent, and up-to-date market data for backtesting and live trading.

---

## Table of Contents

1. [Data Normalization](#data-normalization)
2. [Data Quality Validation](#data-quality-validation)
3. [Data Updates & Backfilling](#data-updates--backfilling)
4. [Best Practices](#best-practices)

---

## Data Normalization

### Symbol Normalization

Different data sources use different ticker symbol formats. Normalize them for consistency:

```python
from copilot_quant.data.normalization import normalize_symbol

# Yahoo Finance format (uses hyphens)
symbol = normalize_symbol('BRK.B', source='yahoo')  # Returns 'BRK-B'

# Alpha Vantage format (uses dots)
symbol = normalize_symbol('BRK-B', source='alpha_vantage')  # Returns 'BRK.B'
```

### Column Name Standardization

Standardize DataFrame column names to lowercase with underscores:

```python
from copilot_quant.data.normalization import standardize_column_names

# Before: ['Open', 'High', 'Low', 'Close', 'Adj Close']
# After:  ['open', 'high', 'low', 'close', 'adj_close']
df = standardize_column_names(df)
```

### Stock Split Adjustment

Adjust historical prices for stock splits:

```python
from copilot_quant.data.normalization import adjust_for_splits

# Manual split adjustment (2-for-1 split on specific date)
df = adjust_for_splits(df, split_ratio=2.0, split_date='2024-01-15')

# Automatic adjustment using split column
df = adjust_for_splits(df, split_column='stock_splits')
```

**How it works:**
- Prices before the split date are divided by the split ratio
- Volume is multiplied by the split ratio
- Maintains price continuity for analysis

### Adjusted Close Calculation

Calculate adjusted close prices accounting for dividends and splits:

```python
from copilot_quant.data.normalization import calculate_adjusted_close

df = calculate_adjusted_close(df, use_dividends=True, use_splits=True)
```

### Data Resampling

Convert time series data to different frequencies:

```python
from copilot_quant.data.normalization import resample_data

# Resample daily data to weekly
weekly_df = resample_data(df, freq='W')

# Resample to monthly
monthly_df = resample_data(df, freq='M')

# Custom aggregation rules
custom_df = resample_data(df, freq='W', aggregation={
    'open': 'first',
    'high': 'max',
    'low': 'min',
    'close': 'last',
    'volume': 'sum'
})
```

**Common frequencies:**
- `'D'` - Daily
- `'W'` - Weekly
- `'M'` - Monthly
- `'Q'` - Quarterly
- `'Y'` - Yearly

---

## Data Quality Validation

### Detecting Missing Data

Identify missing values, gaps, and anomalies:

```python
from copilot_quant.data.normalization import detect_missing_data

issues = detect_missing_data(df)

print(f"Missing values: {len(issues['missing_values'])}")
print(f"Date gaps: {len(issues['date_gaps'])}")
print(f"Zero volume days: {len(issues['zero_volume'])}")
print(f"Price anomalies: {len(issues['price_anomalies'])}")
```

### Validating Data Quality

Check for data quality issues:

```python
from copilot_quant.data.normalization import validate_data_quality

errors = validate_data_quality(df)

if errors:
    print("Data quality issues found:")
    for error in errors:
        print(f"  - {error}")
else:
    print("✓ Data is clean!")
```

**Validation checks:**
- Required columns present (OHLCV)
- Price relationships (High ≥ Low, etc.)
- No negative prices or volumes
- Reasonable missing data percentage

### Filling Missing Data

Handle missing values using various methods:

```python
from copilot_quant.data.normalization import fill_missing_data

# Forward fill (use previous value)
df = fill_missing_data(df, method='ffill')

# Backward fill (use next value)
df = fill_missing_data(df, method='bfill')

# Linear interpolation
df = fill_missing_data(df, method='interpolate')

# Drop rows with missing values
df = fill_missing_data(df, method='drop')

# Limit consecutive fills
df = fill_missing_data(df, method='ffill', limit=5)
```

### Removing Outliers

Remove anomalous data points:

```python
from copilot_quant.data.normalization import remove_outliers

# IQR method (Interquartile Range)
df = remove_outliers(df, column='close', method='iqr', threshold=1.5)

# Z-score method
df = remove_outliers(df, column='close', method='zscore', threshold=3.0)
```

---

## Data Updates & Backfilling

### Incremental Updates

Fetch only new data since the last update:

```python
from copilot_quant.data.update_jobs import DataUpdater

updater = DataUpdater(
    storage_type='csv',
    data_dir='data/historical',
    rate_limit_delay=1.0
)

# Update single symbol (fetches only new data)
updater.update_symbol('AAPL')

# Force update (refresh all data)
updater.update_symbol('AAPL', force=True)

# Batch update multiple symbols
symbols = ['AAPL', 'MSFT', 'GOOGL']
result = updater.batch_update(symbols)

print(f"Updated: {len(result['success'])} symbols")
print(f"Failed: {len(result['failed'])} symbols")
```

### Backfilling Historical Data

Fill in historical data from a start date:

```python
# Backfill single symbol
updater.backfill_symbol('NVDA', start_date='2020-01-01')

# Backfill with specific end date
updater.backfill_symbol('NVDA', start_date='2020-01-01', end_date='2023-12-31')

# Batch backfill
symbols = ['NVDA', 'AMD', 'INTC']
result = updater.batch_backfill(symbols, start_date='2020-01-01')
```

### Checking Update Status

Monitor data freshness:

```python
# Check if symbol needs updating
needs_update = updater.needs_update('AAPL', max_age_days=1)

# Get detailed status for multiple symbols
status = updater.get_update_status(['AAPL', 'MSFT', 'GOOGL'])
print(status)
# Columns: symbol, last_date, last_update, needs_update, days_old
```

### Gap Detection and Filling

Find and fill date gaps in historical data:

```python
# Find gaps (returns list of (start_date, end_date) tuples)
gaps = updater.find_gaps('AAPL')

if gaps:
    print(f"Found {len(gaps)} gaps:")
    for start, end in gaps:
        print(f"  Gap from {start} to {end}")
    
    # Fill all gaps
    updater.fill_gaps('AAPL')
```

### SQLite Storage

Use SQLite for better performance with large datasets:

```python
# Initialize with SQLite
updater = DataUpdater(
    storage_type='sqlite',
    db_path='data/market_data.db',
    rate_limit_delay=1.0
)

# All operations work the same
updater.update_symbol('AAPL')
updater.backfill_symbol('MSFT', start_date='2020-01-01')
```

**Benefits of SQLite:**
- Faster queries with indexing
- Efficient storage
- ACID compliance
- No duplicate dates (enforced by schema)

---

## Best Practices

### 1. Always Validate Data Before Use

```python
# Load data
from copilot_quant.data.eod_loader import SP500EODLoader

loader = SP500EODLoader(storage_type='csv', data_dir='data/historical')
df = loader.load_from_csv('AAPL')

# Validate quality
from copilot_quant.data.normalization import validate_data_quality

errors = validate_data_quality(df)
if errors:
    print("⚠️ Data quality issues found - review before use")
    for error in errors:
        print(f"  {error}")
```

### 2. Standardize Data Pipeline

```python
def prepare_data(symbol):
    """Standard data preparation pipeline."""
    from copilot_quant.data.eod_loader import SP500EODLoader
    from copilot_quant.data.normalization import (
        standardize_column_names,
        fill_missing_data,
        validate_data_quality
    )
    
    # Load data
    loader = SP500EODLoader(storage_type='csv', data_dir='data/historical')
    df = loader.load_from_csv(symbol)
    
    # Standardize columns
    df = standardize_column_names(df)
    
    # Fill missing values
    df = fill_missing_data(df, method='ffill', limit=5)
    
    # Validate
    errors = validate_data_quality(df)
    if errors:
        raise ValueError(f"Data quality issues: {errors}")
    
    return df
```

### 3. Implement Scheduled Updates

Create a daily update script:

```python
# daily_update.py
from copilot_quant.data.update_jobs import DataUpdater
from copilot_quant.data.sp500 import get_sp500_tickers

def daily_update():
    """Update all S&P500 symbols daily."""
    updater = DataUpdater(
        storage_type='sqlite',
        db_path='data/market_data.db',
        rate_limit_delay=1.0
    )
    
    # Get S&P500 constituents
    symbols = get_sp500_tickers(source='manual')
    
    # Update (only fetches if data is >1 day old)
    result = updater.batch_update(
        symbols,
        max_age_days=1,
        continue_on_error=True
    )
    
    print(f"Updated: {len(result['success'])} symbols")
    
    if result['failed']:
        print(f"⚠️ Failed: {result['failed']}")
        # Send alert or log for review

if __name__ == '__main__':
    daily_update()
```

**Schedule with cron (Linux/Mac):**
```bash
# Run at 6 AM daily
0 6 * * * cd /path/to/copilot_quant && python daily_update.py
```

**Schedule with Task Scheduler (Windows):**
- Create a new task
- Trigger: Daily at 6:00 AM
- Action: Start program `python.exe` with argument `daily_update.py`

### 4. Handle Corporate Actions

Always adjust for splits and dividends in backtesting:

```python
from copilot_quant.data.normalization import adjust_for_splits

# Load data
df = loader.load_from_csv('AAPL')

# Adjust for splits (if split column exists)
if 'stock_splits' in df.columns:
    df = adjust_for_splits(df, split_column='stock_splits')

# Or use adjusted close prices
df['returns'] = df['adj_close'].pct_change()
```

### 5. Monitor Data Quality Continuously

```python
def data_health_check(symbols):
    """Check data health for a list of symbols."""
    from copilot_quant.data.update_jobs import DataUpdater
    from copilot_quant.data.normalization import validate_data_quality
    
    updater = DataUpdater(storage_type='csv', data_dir='data/historical')
    
    report = []
    for symbol in symbols:
        # Check freshness
        needs_update = updater.needs_update(symbol, max_age_days=1)
        
        # Check for gaps
        gaps = updater.find_gaps(symbol)
        
        # Load and validate
        df = updater.loader.load_from_csv(symbol)
        errors = validate_data_quality(df) if df is not None else ['No data']
        
        report.append({
            'symbol': symbol,
            'needs_update': needs_update,
            'gaps': len(gaps),
            'quality_issues': len(errors)
        })
    
    return pd.DataFrame(report)

# Run health check
import pandas as pd
health = data_health_check(['AAPL', 'MSFT', 'GOOGL'])
print(health)
```

### 6. Error Recovery

Implement retry logic for failed updates:

```python
def update_with_retry(symbol, max_retries=3):
    """Update symbol with retry logic."""
    from time import sleep
    
    updater = DataUpdater(storage_type='csv', data_dir='data/historical')
    
    for attempt in range(max_retries):
        try:
            success = updater.update_symbol(symbol)
            if success:
                return True
            
            # Wait before retry (exponential backoff)
            sleep(2 ** attempt)
            
        except Exception as e:
            print(f"Attempt {attempt + 1} failed: {e}")
            if attempt < max_retries - 1:
                sleep(2 ** attempt)
            else:
                print(f"❌ Failed to update {symbol} after {max_retries} attempts")
                return False
    
    return False
```

---

## Performance Tips

### 1. Use SQLite for Large Datasets
- Faster queries with indexing
- Lower memory footprint
- Better for 500+ symbols

### 2. Batch Operations
- Use `batch_update()` instead of looping `update_symbol()`
- Process in chunks if memory is limited

### 3. Cache Frequently Used Data
```python
# Load once, use multiple times
df_aapl = loader.load_from_csv('AAPL')
# ... perform multiple analyses ...
```

### 4. Minimize API Calls
- Use incremental updates (`max_age_days` parameter)
- Set appropriate `rate_limit_delay`
- Cache results when possible

---

## Examples

See the following example scripts for detailed usage:
- `examples/normalization_examples.py` - Data normalization and quality
- `examples/update_examples.py` - Data updates and backfilling
- `examples/data_pipeline_examples.py` - Complete data pipeline

---

## Troubleshooting

### Issue: Missing Data After Update
**Solution:** Check for gaps and fill them
```python
gaps = updater.find_gaps('AAPL')
if gaps:
    updater.fill_gaps('AAPL')
```

### Issue: Data Validation Failures
**Solution:** Review specific errors and handle appropriately
```python
errors = validate_data_quality(df)
for error in errors:
    if 'negative' in error.lower():
        # Handle negative values
        df = df[df['close'] > 0]
```

### Issue: Slow Update Performance
**Solution:** 
1. Switch to SQLite storage
2. Increase `rate_limit_delay` if hitting API limits
3. Use batch operations
4. Process in parallel (carefully with rate limits)

---

**Last Updated**: 2026-02-16  
**Module Version**: 1.0
