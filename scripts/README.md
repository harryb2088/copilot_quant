# Data Pipeline Scripts

This directory contains scripts for backfilling and updating market data in the copilot_quant platform.

## Scripts Overview

### S&P500 Market Data

1. **`backfill_sp500.py`** - Historical data backfill
   - One-time execution to populate historical S&P500 data
   - Supports resume capability for interrupted runs
   - Tracks progress with status file
   
2. **`daily_update.py`** - Incremental daily updates
   - Fetches only new data since last update
   - Automatic gap detection and filling
   - Designed for scheduled execution (cron/Task Scheduler)

### Prediction Markets Data

3. **`backfill_prediction_markets.py`** - Historical prediction market backfill
   - Supports multiple providers (Polymarket, Kalshi)
   - Fetches active markets and historical data
   
4. **`daily_update_prediction_markets.py`** - Daily prediction market updates
   - Updates market lists and prices
   - Multi-provider support
   - Designed for frequent execution

## Quick Start

### Initial Setup (One-Time Backfill)

```bash
# Backfill S&P500 data from 2020
python scripts/backfill_sp500.py --start-date 2020-01-01

# Backfill prediction markets
python scripts/backfill_prediction_markets.py --provider polymarket
```

### Daily Updates (Regular Maintenance)

```bash
# Update S&P500 data
python scripts/daily_update.py

# Update prediction markets
python scripts/daily_update_prediction_markets.py --provider polymarket,kalshi
```

## Usage Examples

### Backfill S&P500 Data

```bash
# Basic usage
python scripts/backfill_sp500.py --start-date 2020-01-01

# With specific symbols
python scripts/backfill_sp500.py --symbols AAPL,MSFT,GOOGL --start-date 2020-01-01

# Use SQLite storage
python scripts/backfill_sp500.py --start-date 2020-01-01 --storage sqlite

# With date range
python scripts/backfill_sp500.py --start-date 2020-01-01 --end-date 2023-12-31

# Resume interrupted run
python scripts/backfill_sp500.py --start-date 2020-01-01 --resume

# Verbose logging
python scripts/backfill_sp500.py --start-date 2020-01-01 --verbose
```

### Daily S&P500 Update

```bash
# Standard update (only updates stale data)
python scripts/daily_update.py

# Force update all symbols
python scripts/daily_update.py --force

# Update specific symbols
python scripts/daily_update.py --symbols AAPL,MSFT,GOOGL

# Skip gap filling for faster updates
python scripts/daily_update.py --no-fill-gaps

# Use SQLite storage
python scripts/daily_update.py --storage sqlite

# Custom staleness threshold
python scripts/daily_update.py --max-age-days 2
```

### Backfill Prediction Markets

```bash
# Backfill Polymarket
python scripts/backfill_prediction_markets.py --provider polymarket

# Multiple providers
python scripts/backfill_prediction_markets.py --provider polymarket,kalshi

# With category filter
python scripts/backfill_prediction_markets.py --provider polymarket --category crypto

# Limit number of markets
python scripts/backfill_prediction_markets.py --provider polymarket --limit 50

# Use SQLite
python scripts/backfill_prediction_markets.py --provider polymarket --storage sqlite
```

### Daily Prediction Markets Update

```bash
# Standard update
python scripts/daily_update_prediction_markets.py --provider polymarket

# Multiple providers
python scripts/daily_update_prediction_markets.py --provider polymarket,kalshi

# Update market lists only (skip prices)
python scripts/daily_update_prediction_markets.py --provider polymarket --no-update-prices

# With category filter
python scripts/daily_update_prediction_markets.py --provider polymarket --category politics
```

## Common Options

All scripts support these common options:

- `--storage {csv,sqlite}` - Storage backend (default: csv)
- `--data-dir PATH` - Directory for CSV files (default: data/historical)
- `--db-path PATH` - SQLite database path (default: data/market_data.db)
- `--log-dir PATH` - Log file directory (default: data/logs)
- `--verbose` - Enable verbose (DEBUG) logging
- `--rate-limit-delay SECONDS` - API call delay (default: 0.5)

## Scheduling

For automated execution, see the [Scheduling Guide](../docs/SCHEDULING.md) which covers:

- Setting up cron jobs (Linux/macOS)
- Configuring Task Scheduler (Windows)
- Recommended schedules
- Monitoring and alerts

### Example Cron Jobs

```cron
# Daily S&P500 update at 6 AM (after market close)
0 6 * * 1-5 cd /path/to/copilot_quant && python scripts/daily_update.py

# Prediction markets every 6 hours
0 */6 * * * cd /path/to/copilot_quant && python scripts/daily_update_prediction_markets.py --provider polymarket

# Weekly full refresh on Sundays
0 2 * * 0 cd /path/to/copilot_quant && python scripts/daily_update.py --force
```

## Output and Logs

### Log Files

All scripts generate detailed log files in `data/logs/`:

- `backfill_sp500_YYYYMMDD_HHMMSS.log`
- `daily_update_YYYYMMDD_HHMMSS.log`
- `backfill_prediction_markets_YYYYMMDD_HHMMSS.log`
- `daily_update_prediction_markets_YYYYMMDD_HHMMSS.log`

Sample log files are provided in `data/logs/sample_*.log`.

### Status and Summary Files

**S&P500 Data:**
- `data/historical/backfill_status.csv` - Tracks backfill progress
- `data/historical/update_metadata.csv` - Tracks last update time per symbol
- `data/historical/update_summary.csv` - Daily update history

**Prediction Markets:**
- `data/prediction_markets/update_summary.csv` - Update history

### Data Files

**S&P500 CSV Storage:**
```
data/historical/
├── AAPL.csv
├── MSFT.csv
├── GOOGL.csv
└── ...
```

**S&P500 SQLite Storage:**
```
data/market_data.db
  └── Table: stock_prices
```

**Prediction Markets CSV Storage:**
```
data/prediction_markets/
├── polymarket/
│   ├── markets.csv
│   ├── market_id_1.csv
│   └── market_id_2.csv
└── kalshi/
    ├── markets.csv
    └── ...
```

**Prediction Markets SQLite Storage:**
```
data/prediction_markets/prediction_markets.db
  ├── Table: markets
  └── Table: price_history
```

## Error Handling

All scripts include comprehensive error handling:

1. **Continue on Error**: By default, scripts continue processing even if one symbol/market fails
2. **Resume Capability**: Backfill scripts can resume from interruptions
3. **Retry Logic**: Built into the underlying data providers
4. **Status Tracking**: Failed symbols/markets are logged for review

### Checking for Failures

```bash
# View recent failures in logs
grep "failed" data/logs/daily_update_*.log | tail -20

# Check backfill status
cat data/historical/backfill_status.csv | grep failed

# View update summary
cat data/historical/update_summary.csv
```

## Troubleshooting

### Common Issues

**Issue**: "Module not found" error
```bash
# Solution: Run from project root
cd /path/to/copilot_quant
python scripts/daily_update.py
```

**Issue**: API rate limiting errors
```bash
# Solution: Increase delay between requests
python scripts/daily_update.py --rate-limit-delay 1.0
```

**Issue**: Disk space full
```bash
# Solution: Clean old log files
find data/logs -name "*.log" -mtime +30 -delete
```

**Issue**: Script hangs or takes too long
```bash
# Solution: Process fewer symbols or use SQLite
python scripts/daily_update.py --symbols AAPL,MSFT,GOOGL
python scripts/daily_update.py --storage sqlite
```

### Testing

Test scripts with a small subset before full runs:

```bash
# Test with single symbol
python scripts/daily_update.py --symbols AAPL --verbose

# Test with small date range
python scripts/backfill_sp500.py --symbols AAPL --start-date 2024-01-01 --end-date 2024-01-31

# Test prediction markets with limit
python scripts/daily_update_prediction_markets.py --provider polymarket --limit 5
```

## Performance

### Typical Execution Times

**S&P500 Backfill** (500+ symbols, 3 years):
- CSV Storage: 2-3 hours
- SQLite Storage: 1.5-2.5 hours

**S&P500 Daily Update** (incremental):
- CSV Storage: 10-20 minutes
- SQLite Storage: 8-15 minutes

**Prediction Markets Update** (100 markets):
- Both storage types: 5-10 minutes

### Optimization Tips

1. **Use SQLite for large datasets** - Better query performance
2. **Adjust rate limiting** - Balance speed vs API limits
3. **Run during off-peak hours** - Better API response times
4. **Use parallel processing** (advanced) - Process multiple symbols concurrently

## Support

For questions or issues:

1. Check the [Scheduling Guide](../docs/SCHEDULING.md)
2. Review sample log files in `data/logs/`
3. Run with `--verbose` for detailed debugging
4. Check the main [README](../README.md)
5. Open an issue on GitHub

## Related Documentation

- [Scheduling Guide](../docs/SCHEDULING.md) - Automated execution setup
- [Main README](../README.md) - Platform overview
- [Data Module Documentation](../copilot_quant/data/) - API reference
