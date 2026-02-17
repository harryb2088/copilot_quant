# Example Scripts for Fetching Prediction Market Data

These CLI tools demonstrate how to fetch data from various prediction market platforms.

## Usage

Run these scripts from the project root directory with Python module syntax:

```bash
# From the project root directory
export PYTHONPATH=/path/to/copilot_quant

# Polymarket
python -m examples.prediction_markets.polymarket_cli list --limit 10

# Kalshi
python -m examples.prediction_markets.kalshi_cli list --limit 10

# PredictIt
python -m examples.prediction_markets.predictit_cli list --limit 10

# Metaculus
python -m examples.prediction_markets.metaculus_cli list --limit 10
```

Alternatively, install the package in development mode:

```bash
pip install -e .
```

Then run the scripts directly:

```bash
python examples/prediction_markets/polymarket_cli.py list --limit 10
```

## Available Commands

Each CLI supports two main commands:

### list
List available markets/questions from the platform

Options:
- `--limit N`: Maximum number of markets to return
- `--save`: Save markets to storage
- `--sqlite`: Use SQLite instead of CSV
- `--db-path PATH`: SQLite database path

### fetch
Fetch price/prediction data for a specific market

Options:
- `--market-id ID`: Market/question identifier (required)
- `--start-date YYYY-MM-DD`: Start date for historical data
- `--end-date YYYY-MM-DD`: End date for historical data
- `--output PATH`: Output CSV file path
- `--sqlite`: Save to SQLite database
- `--db-path PATH`: SQLite database path

## Examples

```bash
# List top 20 Polymarket markets
python -m examples.prediction_markets.polymarket_cli list --limit 20

# Fetch and save to CSV
python -m examples.prediction_markets.polymarket_cli fetch \\
    --market-id <ID> --output /tmp/market_data.csv

# Fetch and save to SQLite
python -m examples.prediction_markets.kalshi_cli fetch \\
    --market-id <TICKER> --sqlite --db-path data/markets.db

# With date range
python -m examples.prediction_markets.metaculus_cli fetch \\
    --market-id <ID> --start-date 2024-01-01 --end-date 2024-12-31
```
