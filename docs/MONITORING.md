# Monitoring and Observability Setup Guide

## Overview

Copilot Quant includes comprehensive monitoring and observability features:

- **Structured JSON Logging**: All logs in machine-readable JSON format
- **Prometheus Metrics**: OpenMetrics-compatible metrics export
- **Health Monitoring**: System and application health checks
- **Performance Tracking**: Real-time performance analytics

## Structured Logging

### Configuration

Configure logging in your application:

```python
from copilot_quant.monitoring import configure_logging
from pathlib import Path

# Configure with JSON formatting
configure_logging(
    level=logging.INFO,
    log_dir=Path("/var/log/copilot_quant"),
    json_format=True
)
```

### Using the Logger

```python
from copilot_quant.monitoring import get_logger

logger = get_logger(__name__)

# Simple logging
logger.info("Order executed")

# Structured logging with fields
logger.info(
    "Order executed successfully",
    order_id=1234,
    symbol="AAPL",
    quantity=100,
    price=175.50
)

# Error logging with context
logger.error(
    "Order execution failed",
    order_id=1234,
    error_code="INSUFFICIENT_FUNDS",
    retry_count=3
)
```

### Log Format

JSON logs include standard fields:

```json
{
  "timestamp": "2026-02-19T05:38:55.484209Z",
  "level": "INFO",
  "logger": "copilot_quant.brokers.order_execution_handler",
  "message": "Order executed successfully",
  "module": "order_execution_handler",
  "function": "execute_order",
  "line": 123,
  "order_id": 1234,
  "symbol": "AAPL",
  "quantity": 100,
  "price": 175.50
}
```

### Log Aggregation

#### ELK Stack (Elasticsearch, Logstash, Kibana)

**Filebeat configuration** (`filebeat.yml`):

```yaml
filebeat.inputs:
  - type: log
    enabled: true
    paths:
      - /var/log/copilot_quant/*.log
    json.keys_under_root: true
    json.add_error_key: true

output.elasticsearch:
  hosts: ["localhost:9200"]
  index: "copilot-quant-%{+yyyy.MM.dd}"

setup.kibana:
  host: "localhost:5601"
```

#### Splunk

Configure Splunk to ingest JSON logs:

```conf
[copilot_quant]
sourcetype = _json
index = copilot_quant
```

#### CloudWatch Logs

Use the AWS CloudWatch Logs agent or SDK:

```python
import boto3
import json
from datetime import datetime

logs_client = boto3.client('logs')

def send_to_cloudwatch(log_entry):
    logs_client.put_log_events(
        logGroupName='/copilot-quant/app',
        logStreamName=f'api-{datetime.now().strftime("%Y-%m-%d")}',
        logEvents=[{
            'timestamp': int(datetime.now().timestamp() * 1000),
            'message': json.dumps(log_entry)
        }]
    )
```

## Prometheus Metrics

### Exporting Metrics

Metrics are automatically exported at `/metrics/prometheus`:

```bash
curl http://localhost:8000/metrics/prometheus
```

### Custom Metrics

Track custom application metrics:

```python
from copilot_quant.monitoring import increment_counter, set_gauge, observe_histogram

# Counter: Increments only
increment_counter(
    'orders_executed',
    labels={'status': 'filled', 'symbol': 'AAPL'}
)

# Gauge: Can go up or down
set_gauge(
    'portfolio_value',
    value=1000000.0,
    labels={'account': 'paper'}
)

# Histogram: Track distributions
observe_histogram(
    'order_execution_time_seconds',
    value=0.125,
    labels={'order_type': 'market'}
)
```

### Prometheus Configuration

Add to your `prometheus.yml`:

```yaml
global:
  scrape_interval: 15s
  evaluation_interval: 15s

scrape_configs:
  - job_name: 'copilot-quant-api'
    static_configs:
      - targets: ['localhost:8000']
    metrics_path: '/metrics/prometheus'
    scrape_interval: 10s
    scrape_timeout: 5s
```

### Running Prometheus

```bash
# Download and run Prometheus
wget https://github.com/prometheus/prometheus/releases/download/v2.45.0/prometheus-2.45.0.linux-amd64.tar.gz
tar xvfz prometheus-2.45.0.linux-amd64.tar.gz
cd prometheus-2.45.0.linux-amd64/

# Start Prometheus
./prometheus --config.file=prometheus.yml
```

Access Prometheus UI at http://localhost:9090

### Example Queries

```promql
# Portfolio value over time
copilot_quant_portfolio_value

# Order execution rate
rate(copilot_quant_orders_executed_total[5m])

# Average order execution time
histogram_quantile(0.95, rate(copilot_quant_order_execution_time_seconds_bucket[5m]))

# System CPU usage
copilot_quant_system_resources{resource="cpu_percent"}
```

## Grafana Dashboards

### Setup

1. Install Grafana:

```bash
# Using Docker
docker run -d -p 3000:3000 --name=grafana grafana/grafana

# Or download from https://grafana.com/grafana/download
```

2. Add Prometheus as a data source:
   - Navigate to Configuration → Data Sources
   - Add Prometheus
   - URL: http://localhost:9090

### Dashboard Panels

#### Portfolio Metrics

```json
{
  "title": "Portfolio Value",
  "targets": [
    {
      "expr": "copilot_quant_portfolio_value",
      "legendFormat": "Portfolio Value"
    }
  ],
  "type": "graph"
}
```

#### Performance Metrics

```json
{
  "title": "Sharpe Ratio",
  "targets": [
    {
      "expr": "copilot_quant_sharpe_ratio",
      "legendFormat": "Sharpe Ratio"
    }
  ],
  "type": "gauge"
}
```

#### System Health

```json
{
  "title": "System Resources",
  "targets": [
    {
      "expr": "copilot_quant_system_resources{resource=\"cpu_percent\"}",
      "legendFormat": "CPU %"
    },
    {
      "expr": "copilot_quant_system_resources{resource=\"memory_percent\"}",
      "legendFormat": "Memory %"
    }
  ],
  "type": "graph"
}
```

## Health Monitoring

### Health Checks

The health monitor tracks:

- System resources (CPU, memory, disk)
- Database connectivity
- Broker connection status
- Data freshness

```python
from copilot_quant.monitoring import get_health_monitor

monitor = get_health_monitor()

# Register custom health checks
def check_database():
    # Check database connection
    # Return HealthCheck object
    pass

monitor.register_check('database', check_database)

# Get health status
status = monitor.get_health_status()
print(status['overall_status'])  # 'healthy', 'degraded', or 'unhealthy'
```

### Health Endpoints

- `GET /health/` - Basic health check
- `GET /health/detailed` - Detailed health with all checks
- `GET /health/ready` - Kubernetes readiness probe
- `GET /health/live` - Kubernetes liveness probe

### Alerting

#### Prometheus Alertmanager

Create alert rules in `alerts.yml`:

```yaml
groups:
  - name: copilot_quant
    interval: 30s
    rules:
      - alert: HighCPUUsage
        expr: copilot_quant_system_resources{resource="cpu_percent"} > 80
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High CPU usage detected"
          description: "CPU usage is {{ $value }}%"
      
      - alert: PortfolioDrawdown
        expr: copilot_quant_max_drawdown < -0.15
        for: 1m
        labels:
          severity: critical
        annotations:
          summary: "Large drawdown detected"
          description: "Max drawdown is {{ $value }}"
      
      - alert: APIDown
        expr: up{job="copilot-quant-api"} == 0
        for: 1m
        labels:
          severity: critical
        annotations:
          summary: "API is down"
```

Configure Alertmanager to send notifications:

```yaml
global:
  slack_api_url: 'YOUR_SLACK_WEBHOOK_URL'

route:
  receiver: 'slack-notifications'
  group_by: ['alertname']
  group_wait: 10s
  group_interval: 5m
  repeat_interval: 3h

receivers:
  - name: 'slack-notifications'
    slack_configs:
      - channel: '#alerts'
        title: 'Copilot Quant Alert'
        text: '{{ range .Alerts }}{{ .Annotations.description }}{{ end }}'
```

## Best Practices

### Logging

1. **Use structured logging** with relevant context fields
2. **Log at appropriate levels**:
   - DEBUG: Detailed diagnostic information
   - INFO: General informational messages
   - WARNING: Warning messages for potentially harmful situations
   - ERROR: Error messages
   - CRITICAL: Critical errors requiring immediate attention

3. **Avoid logging sensitive data** (API keys, passwords, PII)
4. **Include correlation IDs** for tracing requests across services
5. **Rotate logs** to manage disk space

### Metrics

1. **Follow naming conventions**:
   - Use `_total` suffix for counters
   - Use base units (seconds, bytes, not milliseconds or megabytes)
   - Use descriptive names

2. **Use labels wisely**:
   - Keep cardinality low
   - Avoid user IDs or high-cardinality values as labels

3. **Track what matters**:
   - Request rates and latencies
   - Error rates
   - Resource utilization
   - Business metrics (portfolio value, number of trades)

### Health Checks

1. **Make health checks fast** (< 1 second)
2. **Check critical dependencies**
3. **Differentiate between liveness and readiness**
4. **Include useful metadata** in health check responses

## Production Deployment

### Docker Compose Stack

```yaml
version: '3.8'

services:
  api:
    build: .
    ports:
      - "8000:8000"
    environment:
      - LOG_LEVEL=INFO
    volumes:
      - ./logs:/var/log/copilot_quant
  
  prometheus:
    image: prom/prometheus:latest
    ports:
      - "9090:9090"
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml
      - prometheus-data:/prometheus
  
  grafana:
    image: grafana/grafana:latest
    ports:
      - "3000:3000"
    volumes:
      - grafana-data:/var/lib/grafana
    depends_on:
      - prometheus

volumes:
  prometheus-data:
  grafana-data:
```

### Kubernetes

```yaml
apiVersion: v1
kind: Service
metadata:
  name: copilot-quant-api
  annotations:
    prometheus.io/scrape: "true"
    prometheus.io/path: "/metrics/prometheus"
    prometheus.io/port: "8000"
spec:
  selector:
    app: copilot-quant-api
  ports:
    - port: 8000
      targetPort: 8000

---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: copilot-quant-api
spec:
  replicas: 3
  selector:
    matchLabels:
      app: copilot-quant-api
  template:
    metadata:
      labels:
        app: copilot-quant-api
    spec:
      containers:
        - name: api
          image: copilot-quant:latest
          ports:
            - containerPort: 8000
          livenessProbe:
            httpGet:
              path: /health/live
              port: 8000
            initialDelaySeconds: 30
            periodSeconds: 10
          readinessProbe:
            httpGet:
              path: /health/ready
              port: 8000
            initialDelaySeconds: 5
            periodSeconds: 5
```

## Troubleshooting

### Check Logs

```bash
# View recent logs
tail -f /var/log/copilot_quant/copilot_quant_*.log

# Search for errors
grep -r "\"level\": \"ERROR\"" /var/log/copilot_quant/

# View logs with jq
tail -f /var/log/copilot_quant/copilot_quant_*.log | jq '.'
```

### Check Metrics

```bash
# Test metrics endpoint
curl http://localhost:8000/metrics/json | jq

# Check specific metric in Prometheus
curl 'http://localhost:9090/api/v1/query?query=copilot_quant_portfolio_value'
```

### Check Health

```bash
# Basic health check
curl http://localhost:8000/health/

# Detailed health
curl http://localhost:8000/health/detailed | jq
```
