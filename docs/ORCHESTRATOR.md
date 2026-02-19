# Trading Orchestrator Documentation

## Overview

The Trading Orchestrator is a robust daemon service that manages the entire trading lifecycle for the `copilot_quant` platform. It provides automated trading based on market hours, health monitoring, configuration management, and multi-channel notifications.

## Components

### 1. Trading Orchestrator (`trading_orchestrator.py`)

The main orchestrator daemon that manages trading operations.

**Features:**
- Automatic start/stop based on NYSE market hours
- State machine (PRE_MARKET, TRADING, POST_MARKET, STOPPED, ERROR)
- Health monitoring and heartbeat logging
- Auto-restart on errors/deadlocks
- Integration with live trading engine
- Graceful shutdown handling

**Usage:**

```python
from copilot_quant.orchestrator import TradingOrchestrator

# Initialize orchestrator with config file
orchestrator = TradingOrchestrator("config.paper.yaml")

# Start the daemon (runs indefinitely)
orchestrator.start()

# In another thread or signal handler:
orchestrator.stop()
```

**Command Line:**

```bash
# Run orchestrator (foreground)
python -m copilot_quant.orchestrator.trading_orchestrator --config config.paper.yaml

# Run as background service (using systemd, Docker, or process manager)
```

### 2. Market Calendar (`market_calendar.py`)

NYSE market hours and US holiday detection.

**Features:**
- Detect if market is currently open
- Get current market state (PRE_MARKET, TRADING, POST_MARKET, CLOSED)
- US holiday calendar (NYSE observance)
- Market session times (9:30 AM - 4:00 PM ET)
- Calculate next market open/close

**Usage:**

```python
from copilot_quant.orchestrator import MarketCalendar, MarketState
from datetime import datetime

calendar = MarketCalendar()

# Check if market is open
if calendar.is_market_open():
    print("Market is open for trading")

# Get current market state
state = calendar.get_market_state()
if state == MarketState.TRADING:
    print("Regular trading hours")

# Check if today is a trading day
if calendar.is_trading_day():
    print("Market is open today")

# Get next market open
next_open = calendar.get_next_market_open()
print(f"Next market open: {next_open}")
```

**NYSE Holidays Supported:**
- New Year's Day
- Martin Luther King Jr. Day
- Presidents' Day
- Good Friday
- Memorial Day
- Juneteenth
- Independence Day
- Labor Day
- Thanksgiving
- Christmas

### 3. Configuration Manager (`config_manager.py`)

Unified YAML/TOML configuration management with validation and versioning.

**Features:**
- Load/save configuration from YAML or JSON files
- Runtime validation
- Hot reload without restart
- Configuration versioning and history
- Type-safe configuration access

**Configuration Schema:**

See `config.paper.yaml` for a complete example. The configuration includes:

- **Trading Schedule**: Timezone, auto-start/stop, pre/post-market
- **Strategy**: Symbols, position sizing, rebalancing
- **Risk Management**: Drawdown limits, circuit breaker, position limits
- **Broker**: Connection settings, commission, slippage
- **Data**: Data source, update interval, caching
- **Notifications**: Alert channels and settings

**Usage:**

```python
from copilot_quant.orchestrator import ConfigManager

# Load configuration
manager = ConfigManager("config.paper.yaml")
config = manager.load()

# Access configuration
print(f"Trading mode: {config.mode}")
print(f"Symbols: {config.strategy.symbols}")

# Modify and save
config.strategy.max_positions = 15
manager.save(config)

# Hot reload
updated_config = manager.reload()

# View version history
versions = manager.list_versions()
for version in versions:
    print(f"Version: {version}")
```

### 4. Notification System (`notifiers/`)

Multi-channel notification and alerting system.

**Supported Channels:**
- **Slack**: Via webhook
- **Discord**: Via webhook
- **Email**: Via SMTP
- **Webhook**: Custom HTTP endpoint

**Alert Levels:**
- **INFO**: Informational (signals, trades)
- **WARNING**: Warning (position limit breach)
- **CRITICAL**: Critical (risk breach, circuit breaker)

**Usage:**

```python
from copilot_quant.orchestrator.notifiers import (
    SlackNotifier,
    DiscordNotifier,
    EmailNotifier,
    NotificationMessage,
    AlertLevel
)

# Setup notifiers
slack = SlackNotifier(
    webhook_url="https://hooks.slack.com/services/YOUR/WEBHOOK/URL",
    channel="#trading-alerts",
    min_level=AlertLevel.WARNING  # Only send WARNING and CRITICAL
)

discord = DiscordNotifier(
    webhook_url="https://discord.com/api/webhooks/YOUR/WEBHOOK",
    min_level=AlertLevel.INFO  # Send all levels
)

email = EmailNotifier(
    smtp_host="smtp.gmail.com",
    smtp_port=587,
    username="your-email@gmail.com",
    password="your-app-password",
    from_email="trading-bot@example.com",
    to_emails=["trader@example.com"]
)

# Send notification
message = NotificationMessage(
    title="Order Filled",
    message="Bought 100 shares of AAPL at $150.00",
    level=AlertLevel.INFO,
    metadata={
        'symbol': 'AAPL',
        'quantity': 100,
        'price': 150.00
    }
)

slack.notify(message)
discord.notify(message)
email.notify(message)
```

**Integration with Trading Events:**

```python
from copilot_quant.orchestrator.notification_integration import (
    OrderNotificationAdapter,
    RiskNotificationAdapter
)

# Setup notifiers
notifiers = [slack, discord, email]

# Create adapters
order_adapter = OrderNotificationAdapter(
    notifiers,
    notify_on_fills=True,
    notify_on_partial_fills=False,
    notify_on_errors=True
)

risk_adapter = RiskNotificationAdapter(notifiers)

# Register with order handler
order_handler.register_fill_callback(order_adapter.on_order_filled)
order_handler.register_error_callback(order_adapter.on_order_error)

# Send risk alerts
risk_adapter.on_circuit_breaker_triggered(
    reason="Portfolio drawdown exceeded 10%",
    drawdown=0.12,
    threshold=0.10
)
```

## Configuration File

The `config.paper.yaml` file contains all settings for the trading system. Here's a minimal example:

```yaml
version: "1.0.0"
mode: paper

schedule:
  timezone: "America/New_York"
  auto_start: true
  auto_stop: true

strategy:
  symbols:
    - AAPL
    - MSFT
  max_positions: 10
  position_size_pct: 0.10

risk:
  max_portfolio_drawdown: 0.12
  enable_circuit_breaker: true
  circuit_breaker_threshold: 0.10

broker:
  broker_type: ibkr
  host: 127.0.0.1
  port: 7497
  paper_trading: true

notifications:
  enabled: true
  channels:
    - slack
  alert_levels:
    - warning
    - critical
  slack_webhook_url: "https://hooks.slack.com/services/YOUR/WEBHOOK/URL"
```

## Running as a Service

### Systemd (Linux)

Create `/etc/systemd/system/trading-orchestrator.service`:

```ini
[Unit]
Description=Trading Orchestrator Service
After=network.target

[Service]
Type=simple
User=trader
WorkingDirectory=/path/to/copilot_quant
ExecStart=/usr/bin/python -m copilot_quant.orchestrator.trading_orchestrator --config config.paper.yaml
Restart=on-failure
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Then:

```bash
sudo systemctl daemon-reload
sudo systemctl enable trading-orchestrator
sudo systemctl start trading-orchestrator
sudo systemctl status trading-orchestrator
```

### Docker

Create `Dockerfile`:

```dockerfile
FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

CMD ["python", "-m", "copilot_quant.orchestrator.trading_orchestrator", "--config", "config.paper.yaml"]
```

Run:

```bash
docker build -t trading-orchestrator .
docker run -d --name orchestrator --restart unless-stopped trading-orchestrator
```

## Monitoring and Logs

The orchestrator provides comprehensive logging:

```python
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('orchestrator.log'),
        logging.StreamHandler()
    ]
)
```

**Key Log Messages:**
- Heartbeat logs every 5 minutes
- State transitions
- Market open/close events
- Trading engine start/stop
- Errors and restart attempts
- Health check failures

## Best Practices

1. **Always test in paper trading mode first**
   - Set `mode: paper` in config
   - Set `broker.paper_trading: true`

2. **Start with conservative risk limits**
   - Low position sizes (5-10%)
   - Strict drawdown limits (10-15%)
   - Enable circuit breaker

3. **Configure notifications properly**
   - Use WARNING level for important alerts
   - Test all notification channels before going live
   - Set up multiple channels for redundancy

4. **Monitor the orchestrator**
   - Check logs regularly
   - Set up alerting for orchestrator errors
   - Monitor heartbeat messages

5. **Use configuration versioning**
   - Enable versioning in ConfigManager
   - Review configuration history periodically
   - Keep backups of working configurations

6. **Test market calendar edge cases**
   - Verify holiday detection
   - Test weekend behavior
   - Check timezone handling

## Troubleshooting

### Orchestrator won't start

- Check configuration file path
- Verify YAML syntax is valid
- Check broker connection settings
- Review logs for error messages

### Notifications not sending

- Verify webhook URLs are correct
- Check network connectivity
- Test individual notifiers separately
- Review notification level filtering

### Trading engine not starting

- Check IBKR connection (TWS/Gateway running?)
- Verify port numbers are correct
- Check client ID conflicts
- Review broker logs

### Market calendar issues

- Verify timezone is correct
- Check system clock is synchronized
- Review holiday calendar for the current year

## API Reference

See the docstrings in each module for detailed API documentation:

- `TradingOrchestrator`: Main orchestrator class
- `MarketCalendar`: Market hours and holiday detection
- `ConfigManager`: Configuration management
- `Notifier`: Base notifier class
- `OrderNotificationAdapter`: Order event notifications
- `RiskNotificationAdapter`: Risk event notifications
