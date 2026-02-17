# Sample Log Files

This directory contains sample log files demonstrating the output from the data backfill and update scripts.

## Log Files

- `sample_backfill_sp500.log` - Example output from running the S&P500 backfill script
- `sample_daily_update.log` - Example output from running the daily S&P500 update script  
- `sample_daily_update_prediction_markets.log` - Example output from running the prediction markets update script

## Actual Logs

When you run the scripts, actual log files will be created with timestamps:

- `backfill_sp500_YYYYMMDD_HHMMSS.log`
- `daily_update_YYYYMMDD_HHMMSS.log`
- `backfill_prediction_markets_YYYYMMDD_HHMMSS.log`
- `daily_update_prediction_markets_YYYYMMDD_HHMMSS.log`

## Log Retention

Consider implementing a log rotation policy to prevent log files from consuming too much disk space:

```bash
# Keep only logs from the last 30 days
find data/logs -name "*.log" -mtime +30 -delete

# Or keep only the most recent 100 log files
ls -t data/logs/*.log | tail -n +101 | xargs rm -f
```

Add this to a cron job for automated cleanup:

```cron
# Clean old logs daily at 1 AM
0 1 * * * find /path/to/copilot_quant/data/logs -name "*.log" -mtime +30 -delete
```
