# Data Pipeline Quick Start Guide

This guide shows you how to use the Copilot Quant data pipeline to download and work with S&P500 market data.

---

## Installation

The data pipeline is included in the main package:

```bash
pip install -r requirements.txt
```

---

## Basic Usage

### 1. Get a Data Provider

```python
from copilot_quant.data import get_data_provider

# Create yfinance provider (default)
provider = get_data_provider("yfinance")
```

### 2. Download Single Stock Data

```python
# Get 1 year of daily data for Apple
data = provider.get_historical_data(
    symbol="AAPL",
    start_date="2023-01-01",
    end_date="2024-01-01"
)

print(data.head())
print(f"Downloaded {len(data)} days of data")
```

### 3. Download Multiple Stocks

```python
from copilot_quant.data import FAANG

# Download FAANG stocks (Facebook/Meta, Apple, Amazon, Netflix, Google)
data = provider.get_multiple_symbols(
    symbols=FAANG,
    start_date="2023-01-01",
    end_date="2024-01-01"
)

# Access close prices for all stocks
close_prices = data['Close']
print(close_prices.head())
```

### 4. Get S&P500 Index

```python
# Download S&P500 index data
sp500 = provider.get_sp500_index(
    start_date="2020-01-01",
    end_date="2024-01-01"
)

print(f"S&P500 closing price: ${sp500['Close'].iloc[-1]:.2f}")
```

### 5. Working with S&P500 Constituents

```python
from copilot_quant.data import get_sp500_tickers, get_sp500_by_sector

# Get all S&P500 ticker symbols
tickers = get_sp500_tickers(source="manual")  # Fast, no network needed
print(f"Found {len(tickers)} stocks")

# Get S&P500 grouped by sector
sectors = get_sp500_by_sector()
for sector, stocks in sectors.items():
    print(f"{sector}: {len(stocks)} stocks")
```

---

## Common Tasks

### Calculate Daily Returns

```python
data = provider.get_historical_data("AAPL", start_date="2023-01-01")
data['Returns'] = data['Close'].pct_change()
print(f"Average daily return: {data['Returns'].mean():.4%}")
```

### Save Data to CSV

```python
import pandas as pd

data = provider.get_multiple_symbols(
    ["AAPL", "MSFT", "GOOGL"],
    start_date="2023-01-01"
)

# Save to CSV
data.to_csv("stocks_data.csv")

# Load back
loaded = pd.read_csv("stocks_data.csv", index_col=0, parse_dates=True)
```

### Prepare Backtest Data

```python
from datetime import datetime, timedelta

# Get 5 years of data
end_date = datetime.now()
start_date = end_date - timedelta(days=5*365)

symbols = ["AAPL", "MSFT", "GOOGL"]
data = provider.get_multiple_symbols(symbols, start_date=start_date, end_date=end_date)

# Get close prices
close_prices = data['Close']

# Calculate returns
returns = close_prices.pct_change()

# Check for missing data
print("Missing data points:")
print(returns.isnull().sum())
```

---

## Predefined Stock Lists

The package includes several predefined stock lists:

```python
from copilot_quant.data import FAANG, MAGNIFICENT_7, DOW_30_TICKERS

print(f"FAANG: {FAANG}")
# ['META', 'AAPL', 'AMZN', 'NFLX', 'GOOGL']

print(f"Magnificent 7: {MAGNIFICENT_7}")
# ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'NVDA', 'META', 'TSLA']

print(f"Dow 30: {len(DOW_30_TICKERS)} stocks")
```

---

## Advanced Usage

### Get Ticker Information

```python
info = provider.get_ticker_info("AAPL")
print(f"Company: {info['longName']}")
print(f"Sector: {info['sector']}")
print(f"Market Cap: ${info['marketCap']:,.0f}")
```

### Different Time Intervals

```python
# Weekly data
data = provider.get_historical_data("AAPL", interval="1wk", start_date="2020-01-01")

# Monthly data
data = provider.get_historical_data("AAPL", interval="1mo", start_date="2020-01-01")
```

### Access Dividends and Splits

```python
data = provider.get_historical_data("AAPL", start_date="2020-01-01")

# Check if dividends are present
if 'Dividends' in data.columns:
    dividends = data[data['Dividends'] > 0]
    print(f"Found {len(dividends)} dividend payments")

# Check for stock splits
if 'Stock Splits' in data.columns:
    splits = data[data['Stock Splits'] > 0]
    print(f"Found {len(splits)} stock splits")
```

---

## Performance Tips

1. **Batch Downloads**: Use `get_multiple_symbols()` instead of downloading stocks one by one
2. **Cache Data**: Save downloaded data to avoid repeated API calls
3. **Use Manual Lists**: For S&P500 constituents, use `source="manual"` for faster loading
4. **Adjust Date Ranges**: Only download the data you need

---

## Error Handling

```python
try:
    data = provider.get_historical_data("AAPL", start_date="2023-01-01")
except Exception as e:
    print(f"Error downloading data: {e}")
    # Implement retry logic or fallback
```

---

## Complete Example

```python
from copilot_quant.data import get_data_provider, get_sp500_tickers
import pandas as pd

# Setup
provider = get_data_provider("yfinance")

# Get top 10 S&P500 stocks
tickers = get_sp500_tickers(source="manual")[:10]

# Download data
print(f"Downloading data for {len(tickers)} stocks...")
data = provider.get_multiple_symbols(
    tickers,
    start_date="2023-01-01",
    end_date="2024-01-01"
)

# Analyze
close_prices = data['Close']
returns = close_prices.pct_change()

print("\nSummary Statistics:")
print(returns.describe())

print("\nCorrelation Matrix:")
print(close_prices.corr())

# Save
output_file = "sp500_top10.csv"
data.to_csv(output_file)
print(f"\nSaved to {output_file}")
```

---

## Next Steps

- Run the examples in `examples/data_pipeline_examples.py`
- Explore the full API documentation
- Integrate data pipeline with backtesting engine

---

## Troubleshooting

**Problem**: Network errors or timeouts  
**Solution**: Check internet connection, retry with shorter date range

**Problem**: Empty DataFrame returned  
**Solution**: Verify ticker symbol is correct, check date range is valid

**Problem**: Missing data points  
**Solution**: Use `data.fillna()` or `data.dropna()` to handle missing values

---

For more information, see `docs/data_source_research.md`
