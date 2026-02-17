# Data Pipeline Scheduling Guide

This guide explains how to schedule the data backfill and incremental update jobs for automated execution.

## Table of Contents

- [Overview](#overview)
- [Scripts Available](#scripts-available)
- [Scheduling on Linux/macOS (cron)](#scheduling-on-linuxmacos-cron)
- [Scheduling on Windows (Task Scheduler)](#scheduling-on-windows-task-scheduler)
- [Monitoring and Alerts](#monitoring-and-alerts)
- [Troubleshooting](#troubleshooting)

## Overview

The copilot_quant data pipeline includes four main scripts:

1. **Backfill Scripts** (one-time execution):
   - `backfill_sp500.py` - Historical S&P500 market data
   - `backfill_prediction_markets.py` - Historical prediction market data

2. **Daily Update Scripts** (recurring execution):
   - `daily_update.py` - Incremental S&P500 updates
   - `daily_update_prediction_markets.py` - Incremental prediction market updates

## Scripts Available

### S&P500 Backfill (`backfill_sp500.py`)

Complete historical data backfill for all S&P500 stocks.

```bash
# Basic usage - backfill from 2020
python scripts/backfill_sp500.py --start-date 2020-01-01

# With all options
python scripts/backfill_sp500.py \
  --start-date 2020-01-01 \
  --storage csv \
  --data-dir data/historical \
  --rate-limit-delay 0.5 \
  --log-dir data/logs \
  --resume
```

**When to run**: Once initially, or when adding new symbols to track.

### S&P500 Daily Update (`daily_update.py`)

Incremental daily updates for S&P500 stocks.

```bash
# Basic usage - update all S&P500 stocks
python scripts/daily_update.py

# With options
python scripts/daily_update.py \
  --storage csv \
  --data-dir data/historical \
  --max-age-days 1 \
  --rate-limit-delay 0.5 \
  --log-dir data/logs
```

**When to run**: Daily, preferably after market close (e.g., 6:00 AM ET).

### Prediction Markets Backfill (`backfill_prediction_markets.py`)

Complete historical data backfill for prediction markets.

```bash
# Backfill Polymarket data
python scripts/backfill_prediction_markets.py --provider polymarket

# Backfill multiple providers
python scripts/backfill_prediction_markets.py --provider polymarket,kalshi

# With category filter
python scripts/backfill_prediction_markets.py \
  --provider polymarket \
  --category crypto \
  --limit 100 \
  --storage csv \
  --log-dir data/logs
```

**When to run**: Once initially, or when adding new markets to track.

### Prediction Markets Daily Update (`daily_update_prediction_markets.py`)

Incremental daily updates for prediction markets.

```bash
# Basic usage
python scripts/daily_update_prediction_markets.py --provider polymarket

# Multiple providers
python scripts/daily_update_prediction_markets.py --provider polymarket,kalshi

# With options
python scripts/daily_update_prediction_markets.py \
  --provider polymarket,kalshi \
  --storage csv \
  --limit 100 \
  --rate-limit-delay 0.5 \
  --log-dir data/logs
```

**When to run**: Daily or multiple times per day (prediction markets update frequently).

## Scheduling on Linux/macOS (cron)

### Setting Up Cron Jobs

1. Open your crontab file:
```bash
crontab -e
```

2. Add the following entries (adjust paths as needed):

```cron
# Data Pipeline Scheduled Jobs
# Format: minute hour day month weekday command

# S&P500 daily update - runs at 6:00 AM ET every weekday
0 6 * * 1-5 cd /path/to/copilot_quant && /usr/bin/python3 scripts/daily_update.py >> data/logs/cron_daily_update.log 2>&1

# Prediction markets update - runs every 6 hours
0 */6 * * * cd /path/to/copilot_quant && /usr/bin/python3 scripts/daily_update_prediction_markets.py --provider polymarket >> data/logs/cron_pm_update.log 2>&1

# Weekly gap filling - runs at 2:00 AM every Sunday
0 2 * * 0 cd /path/to/copilot_quant && /usr/bin/python3 scripts/daily_update.py --force >> data/logs/cron_weekly_update.log 2>&1
```

### Cron Schedule Examples

```cron
# Every day at 6:00 AM
0 6 * * * command

# Every weekday at 6:00 AM
0 6 * * 1-5 command

# Every 6 hours
0 */6 * * * command

# Every hour during market hours (9 AM - 4 PM ET, weekdays)
0 9-16 * * 1-5 command

# First day of every month at 1:00 AM
0 1 1 * * command
```

### Best Practices for Cron

1. **Use absolute paths**: Always use full paths for Python and script files
2. **Redirect output**: Capture both stdout and stderr (`>> log.log 2>&1`)
3. **Set environment**: Include `cd` to the project directory before running scripts
4. **Test commands**: Run commands manually first to ensure they work
5. **Monitor logs**: Regularly check log files for errors

### Viewing Cron Logs

```bash
# View your crontab
crontab -l

# Check system cron logs
tail -f /var/log/syslog | grep CRON

# View script logs
tail -f data/logs/cron_daily_update.log
```

## Scheduling on Windows (Task Scheduler)

### Creating a Scheduled Task

1. **Open Task Scheduler**:
   - Press `Win + R`, type `taskschd.msc`, press Enter

2. **Create Basic Task**:
   - Click "Create Basic Task" in the right panel
   - Name: "Copilot Quant - Daily S&P500 Update"
   - Description: "Daily incremental update of S&P500 market data"

3. **Set Trigger**:
   - Trigger: Daily
   - Start time: 6:00 AM
   - Recur every: 1 days

4. **Set Action**:
   - Action: Start a program
   - Program/script: `C:\Python39\python.exe` (adjust to your Python path)
   - Add arguments: `scripts\daily_update.py --log-dir data\logs`
   - Start in: `C:\path\to\copilot_quant`

5. **Configure Settings**:
   - Check "Run whether user is logged on or not"
   - Check "Run with highest privileges"
   - Configure for: Windows 10

### PowerShell Script Wrapper (Recommended)

Create a wrapper script `run_daily_update.ps1`:

```powershell
# Set working directory
Set-Location "C:\path\to\copilot_quant"

# Activate virtual environment if using one
# .\venv\Scripts\Activate.ps1

# Run the update script
python scripts\daily_update.py --log-dir data\logs

# Check exit code
if ($LASTEXITCODE -ne 0) {
    Write-Error "Daily update failed with exit code $LASTEXITCODE"
    exit $LASTEXITCODE
}

Write-Output "Daily update completed successfully"
```

Then schedule this PowerShell script instead:
- Program/script: `powershell.exe`
- Arguments: `-ExecutionPolicy Bypass -File "C:\path\to\copilot_quant\run_daily_update.ps1"`

### Task Scheduler Schedule Examples

**Daily at 6:00 AM**:
- Trigger: Daily
- Start time: 6:00 AM
- Recur every: 1 days

**Weekdays only**:
- Trigger: Weekly
- Start time: 6:00 AM
- Recur every: 1 week on: Monday, Tuesday, Wednesday, Thursday, Friday

**Every 6 hours**:
- Trigger: Daily
- Start time: 12:00 AM
- Repeat task every: 6 hours
- Duration: 1 day

## Monitoring and Alerts

### Log File Monitoring

All scripts generate log files in the `data/logs/` directory:

```
data/logs/
├── backfill_sp500_20260217_060000.log
├── daily_update_20260217_060000.log
├── backfill_prediction_markets_20260217_080000.log
└── daily_update_prediction_markets_20260217_080000.log
```

### Summary Files

Daily update scripts maintain summary CSV files:

```
data/historical/update_summary.csv
data/prediction_markets/update_summary.csv
```

These files track:
- Timestamp of each update
- Number of symbols/markets processed
- Success/failure counts
- Duration
- Gaps filled (for S&P500)

### Example Monitoring Script

Create `scripts/check_updates.py` to monitor recent updates:

```python
#!/usr/bin/env python3
"""Check status of recent data updates."""

import pandas as pd
from datetime import datetime, timedelta
from pathlib import Path

def check_update_status():
    # Check S&P500 updates
    summary_file = Path('data/historical/update_summary.csv')
    if summary_file.exists():
        df = pd.read_csv(summary_file)
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        
        # Get latest update
        latest = df.iloc[-1]
        age = datetime.now() - latest['timestamp']
        
        print(f"Latest S&P500 update: {latest['timestamp']}")
        print(f"Age: {age.total_seconds() / 3600:.1f} hours")
        print(f"Success rate: {latest['success_rate']:.1f}%")
        
        # Alert if update is too old
        if age > timedelta(days=2):
            print("⚠️  WARNING: S&P500 data is stale!")
    
    # Check prediction markets updates
    pm_summary = Path('data/prediction_markets/update_summary.csv')
    if pm_summary.exists():
        df = pd.read_csv(pm_summary)
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        
        latest = df.iloc[-1]
        age = datetime.now() - latest['timestamp']
        
        print(f"\nLatest prediction markets update: {latest['timestamp']}")
        print(f"Age: {age.total_seconds() / 3600:.1f} hours")
        print(f"Markets updated: {latest['markets_updated']}")

if __name__ == '__main__':
    check_update_status()
```

Run this script to check update status:
```bash
python scripts/check_updates.py
```

### Email Alerts (Optional)

Add email notifications to wrapper scripts when updates fail:

```python
import smtplib
from email.message import EmailMessage

def send_alert(subject, body):
    msg = EmailMessage()
    msg['Subject'] = subject
    msg['From'] = 'alerts@yourdomain.com'
    msg['To'] = 'admin@yourdomain.com'
    msg.set_content(body)
    
    with smtplib.SMTP('smtp.gmail.com', 587) as smtp:
        smtp.starttls()
        smtp.login('your_email@gmail.com', 'your_password')
        smtp.send_message(msg)

# Use in exception handlers
try:
    result = daily_update(...)
    if result['failed']:
        send_alert(
            'Data Update Warning',
            f"Daily update completed with {len(result['failed'])} failures"
        )
except Exception as e:
    send_alert('Data Update Failed', f"Error: {str(e)}")
```

## Troubleshooting

### Common Issues

**Issue**: Cron job doesn't run
- **Solution**: Check cron daemon is running: `systemctl status cron`
- **Solution**: Verify cron syntax: Use a cron validator online
- **Solution**: Check user permissions: Ensure the user has execute permissions

**Issue**: Python module not found in cron
- **Solution**: Use absolute Python path in crontab
- **Solution**: Set PYTHONPATH in crontab: `PYTHONPATH=/path/to/copilot_quant`
- **Solution**: Use a wrapper script that activates virtual environment

**Issue**: Script runs but data isn't updated
- **Solution**: Check log files in `data/logs/`
- **Solution**: Verify network connectivity
- **Solution**: Check API rate limits
- **Solution**: Ensure sufficient disk space

**Issue**: High failure rate
- **Solution**: Increase `rate_limit_delay` to avoid API throttling
- **Solution**: Run backfill with `--resume` to skip completed symbols
- **Solution**: Check for network issues or API changes

### Debugging Tips

1. **Test manually first**:
```bash
python scripts/daily_update.py --verbose --symbols AAPL
```

2. **Check log files**:
```bash
tail -50 data/logs/daily_update_*.log
```

3. **Verify cron environment**:
```bash
# Add to crontab to debug environment
* * * * * env > /tmp/cron_env.txt
```

4. **Test with single symbol**:
```bash
python scripts/daily_update.py --symbols AAPL --verbose
```

5. **Monitor resource usage**:
```bash
# Check disk space
df -h

# Check memory
free -h

# Monitor process
top -p $(pgrep -f daily_update)
```

## Recommended Schedule

Here's a complete recommended schedule for production use:

```cron
# S&P500 Data Updates
# Daily incremental update (weekdays after market close)
0 6 * * 1-5 cd /path/to/copilot_quant && python3 scripts/daily_update.py >> data/logs/cron.log 2>&1

# Weekly full refresh (Sundays)
0 2 * * 0 cd /path/to/copilot_quant && python3 scripts/daily_update.py --force >> data/logs/cron.log 2>&1

# Monthly gap check (1st of month)
0 3 1 * * cd /path/to/copilot_quant && python3 scripts/daily_update.py --force >> data/logs/cron.log 2>&1

# Prediction Markets Updates
# Every 6 hours (markets update frequently)
0 */6 * * * cd /path/to/copilot_quant && python3 scripts/daily_update_prediction_markets.py --provider polymarket,kalshi >> data/logs/cron_pm.log 2>&1
```

## Environment Variables

You can set environment variables for configuration:

```bash
# Add to ~/.bashrc or crontab
export COPILOT_QUANT_DATA_DIR=/path/to/data
export COPILOT_QUANT_LOG_DIR=/path/to/logs
export COPILOT_QUANT_STORAGE=sqlite
export COPILOT_QUANT_RATE_LIMIT=0.5
```

Then use in scripts:
```python
import os
data_dir = os.environ.get('COPILOT_QUANT_DATA_DIR', 'data/historical')
```

## Conclusion

Following this guide, you should be able to:
1. Schedule one-time backfill jobs to populate historical data
2. Set up automated daily updates for ongoing data maintenance
3. Monitor update status and handle failures
4. Troubleshoot common issues

For questions or issues, refer to the main README or open an issue on GitHub.
