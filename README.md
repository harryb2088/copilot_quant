# Copilot Quant Platform

A comprehensive algorithmic trading platform for strategy development, backtesting, and paper trading.

## 🚀 Features

- **Strategy Development**: Create and manage custom trading strategies
- **Backtesting Engine**: Test strategies against historical market data
- **Performance Analytics**: Comprehensive metrics, charts, and visualizations
- **Paper Trading**: Safe testing environment with real market data
- **Risk Management**: Comprehensive risk controls with circuit breaker protection
- **Multi-Page UI**: Clean, intuitive Streamlit web interface

## 📋 Prerequisites

- Python 3.8 or higher
- pip (Python package installer)

## 🛠️ Installation

1. Clone the repository:
```bash
git clone https://github.com/harryb2088/copilot_quant.git
cd copilot_quant
```

2. Install dependencies:
```bash
pip install -r requirements.in
```

Or if using pip-tools:
```bash
pip install pip-tools
pip-compile requirements.in
pip install -r requirements.txt
```

## 🚀 Running the Application

Start the Streamlit web application:

```bash
streamlit run src/ui/app.py
```

The application will launch in your default web browser at `http://localhost:8501`

## ☁️ Cloud Deployment on Vercel

The Copilot Quant Platform can be deployed to Vercel with built-in authentication to keep your trading platform private.

### Prerequisites for Vercel Deployment

1. A [Vercel account](https://vercel.com/signup) (free tier works)
2. [Vercel CLI](https://vercel.com/docs/cli) installed (optional, but recommended)
   ```bash
   npm install -g vercel
   ```

### Deployment Steps

#### Option 1: Deploy with Vercel CLI (Recommended)

1. **Install Vercel CLI** (if not already installed):
   ```bash
   npm install -g vercel
   ```

2. **Login to Vercel**:
   ```bash
   vercel login
   ```

3. **Deploy the application**:
   ```bash
   vercel
   ```
   
   Follow the prompts to:
   - Link to an existing project or create a new one
   - Confirm the project settings
   - Deploy to production

4. **Set environment variables for authentication**:
   ```bash
   vercel env add AUTH_EMAIL
   # Enter your login email when prompted (e.g., user@example.com)
   
   vercel env add AUTH_PASSWORD
   # Enter your desired password when prompted
   
   vercel env add AUTH_NAME
   # Enter the display name when prompted (e.g., "Admin User")
   ```
   
   For each variable, select:
   - Environment: `Production`, `Preview`, and `Development` (select all)
   - Press Enter to confirm

5. **Redeploy with environment variables**:
   ```bash
   vercel --prod
   ```

#### Option 2: Deploy via Vercel Dashboard

1. Go to [Vercel Dashboard](https://vercel.com/dashboard)
2. Click "Add New Project"
3. Import your GitHub repository
4. Configure the project:
   - Framework Preset: `Other`
   - Build Command: (leave empty)
   - Output Directory: (leave empty)
5. Add environment variables in the "Environment Variables" section:
   - `AUTH_EMAIL`: Your login email (e.g., `user@example.com`)
   - `AUTH_PASSWORD`: Your desired password
   - `AUTH_NAME`: Display name (e.g., `Admin User`)
6. Click "Deploy"

### Authentication Configuration

The platform uses **streamlit-authenticator** to protect the UI with email/password login.

#### Required Environment Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `AUTH_EMAIL` | Login email/username | `admin@copilotquant.com` |
| `AUTH_PASSWORD` | Login password (stored as hash) | `SecurePassword123!` |
| `AUTH_NAME` | Display name for the user | `Admin User` |

#### Managing User Credentials

**To change credentials after deployment:**

Using Vercel CLI:
```bash
# Update password
vercel env rm AUTH_PASSWORD
vercel env add AUTH_PASSWORD
# Enter new password when prompted

# Redeploy
vercel --prod
```

Using Vercel Dashboard:
1. Go to your project settings
2. Navigate to "Environment Variables"
3. Edit or remove existing variables
4. Add new values
5. Redeploy the application

**To add multiple users:** Currently supports single-user authentication. For multi-user support, modify `src/ui/utils/auth.py` to accept multiple credentials.

### Switching Between Private and Public Access

#### Making the App Public (Disable Authentication)

To disable authentication and make the app publicly accessible:

1. **Remove authentication environment variables:**
   ```bash
   vercel env rm AUTH_EMAIL
   vercel env rm AUTH_PASSWORD
   vercel env rm AUTH_NAME
   ```

2. **Redeploy:**
   ```bash
   vercel --prod
   ```

When no authentication variables are set, the app will display a warning banner but allow access without login.

#### Making the App Private (Enable Authentication)

To re-enable authentication:

1. **Set authentication environment variables** (see steps above)
2. **Redeploy the application**

### Vercel Configuration Files

The repository includes these Vercel-specific files:

- **`vercel.json`**: Deployment configuration
  - Defines Python runtime and Streamlit entry point
  - Configures routing and environment settings

- **`.vercelignore`**: Files excluded from deployment
  - Excludes tests, docs, examples, and development files
  - Reduces deployment size and build time

### Troubleshooting Vercel Deployment

**App won't start:**
- Check Vercel build logs in the dashboard
- Verify all required dependencies are in `requirements.txt`
- Ensure Python version compatibility (configured in `vercel.json`)

**Authentication not working:**
- Verify environment variables are set correctly
- Check variable names match exactly: `AUTH_EMAIL`, `AUTH_PASSWORD`, `AUTH_NAME`
- Ensure you've redeployed after setting environment variables

**Slow loading:**
- Vercel cold starts can take a few seconds
- Consider upgrading to Vercel Pro for better performance
- Large dependencies (like pandas, numpy) may increase initial load time

**Build fails:**
- Check the build logs for specific errors
- Verify `requirements.txt` is properly formatted
- Ensure no conflicting dependencies

### Security Best Practices

1. **Use strong passwords** for `AUTH_PASSWORD`
2. **Never commit** environment variables to git
3. **Rotate credentials** periodically
4. **Use Vercel secrets** for sensitive data
5. **Enable HTTPS** (Vercel provides this by default)
6. **Monitor access logs** in Vercel dashboard

### Custom Domain (Optional)

To use a custom domain:

1. Go to your project in Vercel Dashboard
2. Navigate to "Settings" → "Domains"
3. Add your custom domain
4. Update DNS records as instructed
5. Vercel will automatically provision SSL certificate

### Limitations and Considerations

- **Serverless environment**: Vercel uses serverless functions with execution time limits
- **State management**: Session state may be lost between requests in some cases
- **WebSocket support**: Limited compared to traditional servers
- **For production trading**: Consider dedicated hosting for mission-critical live trading

For advanced deployment needs or enterprise features, consider:
- Self-hosted deployment on AWS/GCP/Azure
- Container-based deployment with Docker
- Dedicated server with full control

## 📱 Application Structure

```
src/
├── ui/
│   ├── app.py                      # Main entry point (Home page)
│   ├── pages/                      # Multi-page application
│   │   ├── 1_📊_Strategies.py     # Strategy management
│   │   ├── 2_🔬_Backtests.py      # Backtest configuration
│   │   ├── 3_📈_Results.py        # Results analysis
│   │   ├── 4_🔴_Live_Trading.py   # Paper trading interface
│   │   └── 5_🛡️_Risk_Management.py # Risk controls configuration
│   ├── components/                 # Shared UI components
│   │   ├── sidebar.py             # Navigation sidebar
│   │   ├── charts.py              # Chart components
│   │   └── tables.py              # Table components
│   └── utils/                      # Utility functions
│       ├── session.py             # Session state management
│       └── mock_data.py           # Mock data generators
└── risk/                           # Risk management framework
    ├── settings.py                 # Risk settings configuration
    └── portfolio_risk.py           # RiskManager class
```

## 🎯 Quick Start Guide

1. **Home Page**: Overview and quick stats dashboard
2. **Strategies**: Browse and create trading strategies
3. **Backtests**: Configure and run historical simulations
4. **Results**: Analyze performance metrics and charts
5. **Live Trading**: Deploy strategies in paper trading mode
6. **Risk Management**: Configure risk controls and circuit breakers

## ⚠️ Safety Notice

**This platform currently operates in PAPER TRADING ONLY mode.**

- No real money is at risk
- All trades are simulated
- Uses real market data for realistic testing
- Safe environment for learning and testing strategies

## 🔧 Development

Current Status: **v0.1.0-alpha**

This is a development version with UI skeleton and mock data.
Backend integration and live data feeds are in progress.

## 📝 License

Copyright © 2024 Copilot Quant Platform

## 🤝 Contributing

This is a personal project. Contributions are welcome!

## 📧 Contact

For questions or support, please open an issue on GitHub.
# copilot_quant 📈

A quantitative trading platform built with modern Python tools for backtesting, strategy development, and automated trading.

## 🎯 Project Goals

copilot_quant aims to provide a comprehensive, modular platform for:
- **Backtesting** trading strategies with historical data
- **Live trading** through broker integrations (Interactive Brokers)
- **Strategy development** with a clean, testable architecture
- **Data management** for market data (S&P 500 via Yahoo Finance)
- **Visualization** through an intuitive Streamlit UI

## ⚠️ Safety Notice

**ALWAYS START WITH PAPER TRADING**
- This platform supports live trading through Interactive Brokers
- Test all strategies thoroughly in paper trading mode before using real capital
- Trading involves risk of loss - never trade with money you cannot afford to lose

## 🚀 Quick Start

### Prerequisites
- Python 3.10 or higher
- pip package manager

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/harryb2088/copilot_quant.git
   cd copilot_quant
   ```

2. **Create a virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

## 📁 Project Structure

```
copilot_quant/
├── copilot_quant/           # Source code
│   ├── data/               # Data ingestion & storage
│   ├── backtest/           # Backtesting engine
│   ├── strategies/         # Trading strategies
│   ├── brokers/            # Broker connectors (IBKR, etc.)
│   ├── ui/                 # Streamlit UI components
│   └── utils/              # Shared utilities
├── tests/                  # Test suite (mirrors copilot_quant structure)
├── data/                   # Local data storage (CSV/SQLite)
├── notebooks/              # Jupyter notebooks for analysis
├── docs/                   # Documentation
├── .github/workflows/      # CI/CD pipelines
├── requirements.in         # Dependency specification
├── requirements.txt        # Pinned dependencies (pip-tools)
└── README.md              # This file
```

## 🧪 Running Tests

Run the full test suite:
```bash
pytest tests/
```

Run tests with coverage:
```bash
pytest tests/ -v --cov=src --cov-report=term-missing
```

## 🔍 Linting

We use **ruff** for fast Python linting:

```bash
# Check for issues
ruff check src/ tests/

# Auto-fix issues
ruff check --fix src/ tests/
```

## 📊 Running Backtests

*(Coming soon - backtesting functionality will be added in future releases)*

Example usage (pseudocode):
```python
# PSEUDOCODE EXAMPLE – BacktestEngine and SampleStrategy are not yet implemented
# from copilot_quant.backtest import BacktestEngine
# from copilot_quant.strategies import SampleStrategy

# Initialize backtest
# engine = BacktestEngine(
#     strategy=SampleStrategy(),
#     start_date='2023-01-01',
#     end_date='2024-01-01'
# )

# Run backtest
# results = engine.run()
# print(results.summary())
```

## 📊 Data Ingestion - S&P500 EOD Data Loader

The platform includes a comprehensive End-of-Day (EOD) data loader for S&P500 equities using Yahoo Finance.

### Features

- **Flexible Symbol Input**: Load from list or CSV file
- **Date Range Configuration**: Specify start and end dates
- **Split/Dividend Handling**: Automatic adjustment via yfinance
- **Multiple Storage Options**: Save to CSV files or SQLite database
- **Robust Error Handling**: Continue on errors with detailed logging
- **Rate Limiting**: Compliant with API usage guidelines

### Quick Start

**Example 1: Fetch Single Symbol to CSV**

```python
from copilot_quant.data.eod_loader import SP500EODLoader

# Initialize loader
loader = SP500EODLoader(
    symbols=['AAPL'],
    storage_type='csv',
    data_dir='data/historical'
)

# Fetch and save data
loader.fetch_and_save('AAPL', start_date='2023-01-01', end_date='2024-01-01')

# Load data back
df = loader.load_from_csv('AAPL')
print(df.head())
```

**Example 2: Fetch Multiple Symbols from CSV File**

```python
# Load symbols from CSV file (must have 'Symbol' column)
loader = SP500EODLoader(
    symbols_file='data/sp500_symbols.csv',
    storage_type='csv',
    data_dir='data/historical',
    rate_limit_delay=1.0  # 1 second delay between requests
)

# Fetch all symbols
result = loader.fetch_all(
    start_date='2023-01-01',
    end_date='2024-01-01',
    continue_on_error=True
)

print(f"Success: {len(result['success'])} symbols")
print(f"Failed: {len(result['failed'])} symbols")
```

**Example 3: SQLite Database Storage**

```python
# Initialize with SQLite storage
loader = SP500EODLoader(
    symbols=['AAPL', 'MSFT', 'GOOGL'],
    storage_type='sqlite',
    db_path='data/market_data.db',
    rate_limit_delay=1.0
)

# Fetch all symbols
loader.fetch_all(start_date='2023-01-01', end_date='2024-01-01')

# Query with date range filter
df = loader.load_from_sqlite('AAPL', start_date='2023-06-01', end_date='2023-12-31')
```

### Sample Data Files

A sample S&P500 symbols file is provided at `data/sp500_symbols.csv` containing 25 major stocks. You can expand this list or create your own.

### CSV Output Format

CSV files are saved as `data/historical/equity_<SYMBOL>.csv` with the following columns:

- `Date`: Trading date
- `open`: Opening price
- `high`: High price
- `low`: Low price
- `close`: Closing price
- `adj_close`: Adjusted closing price
- `volume`: Trading volume
- `dividends`: Dividend amount (if any)
- `stock_splits`: Stock split ratio (if any)
- `Symbol`: Stock ticker symbol

### SQLite Schema

The SQLite database uses the following schema:

```sql
CREATE TABLE equity_data (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    symbol TEXT NOT NULL,
    date TEXT NOT NULL,
    open REAL,
    high REAL,
    low REAL,
    close REAL,
    adj_close REAL,
    volume INTEGER,
    dividends REAL,
    stock_splits REAL,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(symbol, date)
);
```

### Running the Examples

Try the interactive example scripts:

```bash
# S&P500 EOD data loader
python examples/eod_loader_example.py

# Prediction market data
python examples/prediction_market_examples.py

# Data normalization and quality
python examples/normalization_examples.py

# Data updates and backfilling
python examples/update_examples.py
```

## 🔮 Prediction Market Data

The platform now supports fetching data from prediction market platforms for use in trading strategies.

### Supported Platforms

- **Polymarket**: Decentralized prediction market on Polygon
- **Kalshi**: CFTC-regulated prediction market exchange

### Quick Start

```python
from copilot_quant.data.prediction_markets import (
    PolymarketProvider,
    KalshiProvider,
    get_prediction_market_provider
)

# Fetch Polymarket data
polymarket = PolymarketProvider()
markets = polymarket.get_active_markets(category='crypto', limit=10)
print(markets[['question', 'volume', 'end_date']])

# Fetch Kalshi data
kalshi = KalshiProvider()
markets = kalshi.get_active_markets(limit=10)
print(markets[['question', 'yes_bid', 'yes_ask']])
```

See [Prediction Markets Guide](docs/prediction_markets_guide.md) for detailed documentation.

## 🧹 Data Normalization & Quality

Comprehensive utilities for cleaning, standardizing, and validating market data.

### Key Features

- **Symbol Normalization**: Standardize ticker symbols across different data sources
- **Column Standardization**: Consistent column naming (lowercase, underscores)
- **Split/Dividend Adjustment**: Automatic price adjustment for corporate actions
- **Missing Data Detection**: Identify gaps, NaN values, and anomalies
- **Data Quality Validation**: Comprehensive validation checks
- **Outlier Removal**: Statistical outlier detection and removal
- **Data Resampling**: Convert between different time frequencies

### Quick Start

```python
from copilot_quant.data.normalization import (
    normalize_symbol,
    standardize_column_names,
    detect_missing_data,
    validate_data_quality,
    fill_missing_data,
    resample_data
)

# Normalize symbols
symbol = normalize_symbol('BRK.B', source='yahoo')  # Returns 'BRK-B'

# Standardize column names
df = standardize_column_names(df)

# Detect issues
issues = detect_missing_data(df)
print(f"Found {len(issues['missing_values'])} missing values")

# Validate quality
errors = validate_data_quality(df)
if not errors:
    print("✓ Data is clean!")

# Fill missing data
df = fill_missing_data(df, method='ffill')

# Resample to weekly
weekly_df = resample_data(df, freq='W')
```

See [Data Management Guide](docs/data_management_guide.md) for detailed documentation.

## ⚡ Data Updates & Backfilling

Efficient data management with incremental updates and gap filling.

### Key Features

- **Incremental Updates**: Fetch only new data since last update
- **Backfill Jobs**: Fill in historical data gaps
- **Gap Detection**: Automatically find missing dates
- **Update Metadata**: Track last update times
- **Batch Operations**: Process multiple symbols efficiently
- **SQLite Support**: Fast queries with database storage

### Quick Start

```python
from copilot_quant.data.update_jobs import DataUpdater

# Initialize updater
updater = DataUpdater(
    storage_type='csv',
    data_dir='data/historical',
    rate_limit_delay=1.0
)

# Incremental update (fetch only new data)
updater.update_symbol('AAPL')

# Batch update multiple symbols
result = updater.batch_update(['AAPL', 'MSFT', 'GOOGL'])
print(f"Updated: {len(result['success'])} symbols")

# Backfill historical data
updater.backfill_symbol('NVDA', start_date='2020-01-01')

# Find and fill gaps
gaps = updater.find_gaps('AAPL')
if gaps:
    updater.fill_gaps('AAPL')

# Check update status
status = updater.get_update_status(['AAPL', 'MSFT'])
print(status)
```

See [Data Management Guide](docs/data_management_guide.md) for detailed documentation.
---

## 📈 Prediction Market Data Fetchers

Fetch, parse, and save time series data from major prediction markets including **Polymarket**, **Kalshi**, **PredictIt**, and **Metaculus**.

### Supported Platforms

| Platform | Markets Available | Historical Data | API Authentication | Notes |
|----------|------------------|-----------------|-------------------|-------|
| **Polymarket** | Yes/No contracts | Limited | Not required | Uses public CLOB API |
| **Kalshi** | Binary events | Yes | Optional | Enhanced features with API key |
| **PredictIt** | Political markets | No (snapshot only) | Not required | Public API limited to current prices |
| **Metaculus** | Forecasting questions | Yes | Not required | Community predictions over time |

### Quick Start

**Example 1: List markets from Polymarket**

```python
from copilot_quant.data.prediction_markets import PolymarketProvider

# Initialize provider
provider = PolymarketProvider()

# List available markets
markets = provider.list_markets(limit=20)
print(markets)

# Get market details
details = provider.get_market_details('market_id_here')
print(f"Market: {details['title']}")
print(f"Volume: ${details['volume']:,.2f}")
```

**Example 2: Fetch historical price data**

```python
from copilot_quant.data.prediction_markets import PolymarketProvider

provider = PolymarketProvider()

# Fetch price history for a specific market
data = provider.get_market_data(
    market_id='market_id_here',
    start_date='2024-01-01',
    end_date='2024-12-31'
)

print(data.tail())  # Show latest prices
```

**Example 3: Save data to CSV or SQLite**

```python
from copilot_quant.data.prediction_markets import (
    PolymarketProvider,
    PredictionMarketStorage
)

provider = PolymarketProvider()
storage = PredictionMarketStorage(storage_type='sqlite', db_path='data/markets.db')

# Fetch and save markets
markets = provider.list_markets(limit=50)
storage.save_markets('polymarket', markets)

# Fetch and save price data
data = provider.get_market_data('market_id_here')
storage.save_market_data('polymarket', 'market_id_here', data)

# Load data later
loaded_markets = storage.load_markets('polymarket')
loaded_data = storage.load_market_data('polymarket', 'market_id_here')
```

**Example 4: Using other providers**

```python
from copilot_quant.data.prediction_markets import (
    KalshiProvider,
    PredictItProvider,
    MetaculusProvider,
)

# Kalshi (optionally with API key)
kalshi = KalshiProvider(api_key=os.environ.get('KALSHI_API_KEY'))
kalshi_markets = kalshi.list_markets(limit=10)

# PredictIt
predictit = PredictItProvider()
predictit_markets = predictit.list_markets(limit=10)

# Metaculus
metaculus = MetaculusProvider()
metaculus_questions = metaculus.list_markets(limit=10)
```

### CLI Tools

Each platform has a dedicated CLI tool for easy data fetching:

```bash
# Polymarket
python examples/prediction_markets/polymarket_cli.py list --limit 10
python examples/prediction_markets/polymarket_cli.py fetch --market-id <ID> --output data.csv

# Kalshi
python examples/prediction_markets/kalshi_cli.py list --limit 10
python examples/prediction_markets/kalshi_cli.py fetch --market-id <TICKER> --sqlite

# PredictIt
python examples/prediction_markets/predictit_cli.py list --limit 10
python examples/prediction_markets/predictit_cli.py fetch --market-id <ID> --output data.csv

# Metaculus
python examples/prediction_markets/metaculus_cli.py list --limit 10
python examples/prediction_markets/metaculus_cli.py fetch --market-id <ID> --sqlite
```

### Field Mappings

The prediction market providers normalize data into a consistent format. Here's how platform-specific fields map to the standardized schema:

#### Market List Fields

| Standard Field | Polymarket | Kalshi | PredictIt | Metaculus |
|---------------|-----------|--------|-----------|-----------|
| `market_id` | `condition_id` | `ticker` | `id` | `id` |
| `title` | `question` | `title` | `name` | `title` |
| `category` | `category` | `category` | URL-derived | `category` |
| `close_time` | `end_date_iso` | `close_time` | `dateEnd` | `close_time` |
| `status` | `active` → "active"/"closed" | `status` | `status` | `status` |
| `volume` | `volume` | `volume` | N/A | N/A |
| `liquidity` | `liquidity` | `liquidity` | N/A | N/A |

#### Price/Prediction Data Fields

| Standard Field | Polymarket | Kalshi | PredictIt | Metaculus |
|---------------|-----------|--------|-----------|-----------|
| `timestamp` | Price time | History `ts` | Snapshot time | Prediction time `t` |
| `price` | Token price (0-1) | `yes_price` / 100 | `lastTradePrice` | Community median `q2` |
| `volume` | Trade volume | `volume` | N/A | N/A |

**Notes:**
- All prices are normalized to 0-1 range (0% to 100% probability)
- Timestamps are converted to pandas DatetimeIndex
- Missing fields are filled with appropriate defaults (0.0 for numeric, empty string for text)

### Data Storage Formats

**CSV Format:**
- Markets: `data/prediction_markets/{provider}/markets.csv`
- Price data: `data/prediction_markets/{provider}/{market_id}.csv`

**SQLite Schema:**

```sql
-- Markets table
CREATE TABLE markets (
    provider TEXT NOT NULL,
    market_id TEXT NOT NULL,
    title TEXT,
    category TEXT,
    close_time TEXT,
    status TEXT,
    volume REAL,
    liquidity REAL,
    last_updated TEXT,
    PRIMARY KEY (provider, market_id)
);

-- Price history table
CREATE TABLE price_history (
    provider TEXT NOT NULL,
    market_id TEXT NOT NULL,
    timestamp TEXT NOT NULL,
    price REAL,
    volume REAL,
    PRIMARY KEY (provider, market_id, timestamp)
);
```

### Error Handling

All providers gracefully handle:
- Network failures (returns empty DataFrame with error log)
- Missing data (fills with defaults)
- API rate limits (providers use session management)
- Invalid market IDs (logs error and returns empty result)

### Running Tests

```bash
# Run all prediction market tests
python -m pytest tests/test_data/test_prediction_markets.py -v

# Run specific test class
python -m pytest tests/test_data/test_prediction_markets.py::TestPolymarketProvider -v
```

---

## 🖥️ Running the Streamlit UI

*(Coming soon - UI functionality will be added in future releases)*

The Streamlit-based web interface is not yet available in this version of the project, and no UI entrypoint script is currently provided.

Once the UI is implemented, this section will be updated with the exact command (for example, a `streamlit run` invocation) and entrypoint path to launch the app.

The planned UI will provide:
- Strategy configuration
- Backtest visualization
- Live trading dashboard
- Performance metrics

## 🔧 Development

### Adding Dependencies

We use **pip-tools** for dependency management:

1. Add your dependency to `requirements.in`
2. Compile the requirements:
   ```bash
   pip-compile requirements.in
   ```
3. Install updated dependencies:
   ```bash
   pip install -r requirements.txt
   ```

### Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for development guidelines, code style, and pull request process.

## 📚 Documentation

- [Contributing Guidelines](CONTRIBUTING.md)
- [License](LICENSE) - MIT License

## 📊 Market Data Sources

### Primary Data Source: yfinance (Yahoo Finance)

We use **yfinance** as our primary source for S&P500 historical market data.

**Why yfinance?**
- ✅ **Free & Unlimited**: No API keys, no rate limits
- ✅ **Complete Coverage**: All S&P500 stocks + index data
- ✅ **Historical Depth**: 20+ years of data
- ✅ **Corporate Actions**: Dividends, splits, and adjusted prices included
- ✅ **Easy Setup**: No authentication required
- ✅ **Well Maintained**: Active Python library with good community support
- ✅ **Sufficient Quality**: Appropriate for backtesting and research

**Data Available:**
- OHLCV (Open, High, Low, Close, Volume)
- Adjusted close prices
- Dividends and stock splits
- Historical data back to ~1970s for most stocks
- S&P500 index (^GSPC)

**Usage Example:**
```python
import yfinance as yf

# Download single stock
ticker = yf.Ticker("AAPL")
hist = ticker.history(period="1y")  # 1 year of daily data

# Download multiple stocks
data = yf.download(["AAPL", "MSFT", "GOOGL"], start="2020-01-01", end="2024-01-01")

# Get S&P500 index
sp500 = yf.Ticker("^GSPC")
sp500_data = sp500.history(period="max")
```

**Limitations:**
- Not suitable for high-frequency trading (HFT)
- Occasional API instability (Yahoo's infrastructure)
- Limited to end-of-day data (no intraday on free tier)
- Terms of use: personal/research/educational purposes

### Alternative/Future Data Sources

**For Production Trading:**
- **Polygon.io** ($29-199/month): Excellent data quality, real-time feeds, production-grade
- **IEX Cloud**: Good balance of cost and quality, 15 years of history

**For Real-time Validation:**
- **Alpha Vantage** (Free: 25 calls/day): Suitable for small-scale real-time needs
- Can be added as secondary source for paper trading validation

### Data Storage Strategy

Market data is cached locally to minimize API calls and improve performance:
- SQLite database for structured storage
- CSV exports for backup and portability
- Automatic update mechanism for recent data
- S&P500 constituent list management

See `copilot_quant/data/` module for implementation details.

## 🛡️ Risk Management Framework

The platform includes a comprehensive risk management system designed to protect capital and prevent catastrophic losses.

### Key Features

**Portfolio-Level Controls:**
- Maximum portfolio drawdown cap (default: 12%)
- Minimum/maximum cash allocation (default: 20% min, 80% max)
- Circuit breaker - automatic liquidation if drawdown threshold exceeded
- Volatility targeting - auto-scale position sizes to target portfolio volatility

**Position-Level Controls:**
- Maximum position size as % of portfolio (default: 10%)
- Per-position stop loss (default: 5%)
- Correlation filter - prevent >2 positions with correlation > 0.8
- Maximum number of concurrent positions (default: 10)

### Quick Start

```python
from src.risk.portfolio_risk import RiskManager
from src.risk.settings import RiskSettings

# Use conservative defaults
risk_manager = RiskManager()

# Or customize settings
settings = RiskSettings(
    max_portfolio_drawdown=0.15,  # 15%
    max_position_size=0.12,  # 12%
    enable_circuit_breaker=True
)
risk_manager = RiskManager(settings)

# Check portfolio risk
result = risk_manager.check_portfolio_risk(
    portfolio_value=95000,
    peak_value=100000,
    cash=25000
)

if result.approved:
    print("✅ Portfolio risk acceptable")
else:
    print(f"❌ Risk check failed: {result.reason}")
```

### Risk Profiles

Three built-in risk profiles are available:

| Profile | Max Drawdown | Max Position | Min Cash | Stop Loss |
|---------|--------------|--------------|----------|-----------|
| Conservative | 12% | 10% | 20% | 5% |
| Balanced | 15% | 15% | 15% | 7% |
| Aggressive | 20% | 20% | 10% | 10% |

```python
# Load a preset profile
conservative = RiskSettings.get_conservative_profile()
balanced = RiskSettings.get_balanced_profile()
aggressive = RiskSettings.get_aggressive_profile()
```

### Streamlit UI

Configure risk parameters through the interactive UI:

```bash
streamlit run src/ui/app.py
# Navigate to "Risk Management" page
```

Features:
- Interactive sliders for all risk parameters
- Real-time risk status dashboard
- Quick profile switching (Conservative/Balanced/Aggressive)
- Risk breach history log
- Settings persistence across sessions

### Demo Notebook

Explore the risk framework with the interactive demo:

```bash
jupyter notebook notebooks/risk_framework_demo.ipynb
```

The notebook includes:
- Portfolio and position risk checks
- Volatility-based position sizing
- Circuit breaker simulation
- Strategy comparison with/without risk controls
- Correlation filtering examples

### Testing

Run the comprehensive test suite:

```bash
pytest tests/test_risk/ -v --cov=src/risk
```

**Test Coverage: 97%** (51 tests covering all risk controls)

## 🛠️ Technology Stack

- **Data Processing**: pandas, numpy
- **Market Data**: yfinance
- **Broker Integration**: ib_insync
- **Database**: SQLAlchemy
- **UI**: Streamlit
- **Testing**: pytest
- **Linting**: ruff

## 📈 Features Roadmap

- [x] Project structure and infrastructure
- [x] Data source research and selection (yfinance chosen)
- [x] Data ingestion module (Yahoo Finance, CSV import)
  - [x] S&P500 EOD data loader with yfinance
  - [x] CSV and SQLite storage options
  - [x] Rate limiting and error handling
  - [x] Prediction market data providers (Polymarket, Kalshi)
  - [x] Data normalization and quality validation utilities
  - [x] Incremental updates and backfill jobs
  - [x] Gap detection and filling
- [ ] Backtesting engine core
- [ ] Basic trading strategies (Moving Average, Mean Reversion)
- [ ] Performance metrics and reporting
- [ ] Streamlit UI for strategy configuration
- [ ] Interactive Brokers integration (paper trading)
- [ ] Live trading capabilities
- [x] Advanced risk management
  - [x] RiskManager class with portfolio and position-level controls
  - [x] Circuit breaker for automatic liquidation
  - [x] Volatility-based position sizing
  - [x] Correlation filters for diversification
  - [x] Streamlit UI for risk configuration
  - [x] Comprehensive test suite (97% coverage)

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🤝 Acknowledgments

Built with modern Python tools and best practices for quantitative trading.
