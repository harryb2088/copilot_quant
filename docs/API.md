# Copilot Quant REST API Documentation

## Overview

The Copilot Quant REST API provides programmatic access to portfolio data, positions, orders, and performance metrics. The API is built with FastAPI and supports both REST and WebSocket connections.

## Base URL

- **Development**: `http://localhost:8000`
- **Production**: Configure via environment variables

## Authentication

API endpoints can be protected with API key authentication. Include the API key in the request header:

```
X-API-Key: your-api-key-here
```

### Generating API Keys

```python
from copilot_quant.api.auth import get_api_key_manager

manager = get_api_key_manager()
api_key = manager.generate_key("my-app", expiry_days=30)
print(f"API Key: {api_key}")
```

## Endpoints

### Health & Monitoring

#### `GET /health/`
Basic health check.

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2026-02-19T05:38:55.484209",
  "service": "copilot-quant-api"
}
```

#### `GET /health/detailed`
Detailed health information including system resources.

**Response:**
```json
{
  "overall_status": "healthy",
  "timestamp": "2026-02-19T05:39:04.211028",
  "uptime_seconds": 8,
  "uptime_formatted": "0:00:08",
  "checks": {
    "system_resources": {
      "status": "healthy",
      "message": "System resources normal",
      "metadata": {
        "cpu_percent": 22.5,
        "memory_percent": 12.1,
        "disk_percent": 37.4
      }
    }
  }
}
```

#### `GET /metrics/json`
Metrics in JSON format.

#### `GET /metrics/prometheus`
Metrics in Prometheus format for scraping.

### Portfolio

#### `GET /api/v1/portfolio/`
Get current portfolio summary.

**Response:**
```json
{
  "portfolio_value": 1000000.0,
  "cash": 250000.0,
  "positions_value": 750000.0,
  "total_return": 0.15,
  "total_return_pct": 15.0,
  "num_positions": 8,
  "timestamp": "2026-02-19"
}
```

#### `GET /api/v1/portfolio/metrics`
Get comprehensive portfolio metrics.

**Response includes:**
- Value metrics (portfolio value, cash, positions value)
- Return metrics (total return, realized/unrealized PnL)
- Risk metrics (Sharpe, Sortino, max drawdown)
- Exposure metrics (net/gross exposure, leverage)
- Position metrics (number of positions, concentration)

#### `GET /api/v1/portfolio/attribution?by=symbol`
Get performance attribution.

**Query Parameters:**
- `by`: Attribution type (`symbol`, `strategy`, `sector`)
- `start_date`: Optional start date (YYYY-MM-DD)
- `end_date`: Optional end date (YYYY-MM-DD)

### Positions

#### `GET /api/v1/positions/`
Get all current positions.

**Response:**
```json
[
  {
    "symbol": "AAPL",
    "quantity": 150,
    "avg_cost": 175.5,
    "current_price": 182.3,
    "market_value": 27345.0,
    "unrealized_pnl": 1020.0,
    "unrealized_pnl_pct": 3.87,
    "weight": 0.027
  }
]
```

#### `GET /api/v1/positions/{symbol}`
Get position for a specific symbol.

#### `GET /api/v1/positions/summary/by-sector`
Get positions grouped by sector.

#### `GET /api/v1/positions/summary/concentration`
Get position concentration metrics.

### Orders

#### `GET /api/v1/orders/`
Get orders with optional filtering.

**Query Parameters:**
- `status`: Filter by order status
- `symbol`: Filter by symbol
- `start_date`: Start date (YYYY-MM-DD)
- `end_date`: End date (YYYY-MM-DD)
- `limit`: Max results (1-1000, default: 100)

#### `GET /api/v1/orders/{order_id}`
Get details for a specific order including fills.

#### `GET /api/v1/orders/fills/`
Get all fills with optional filtering.

#### `GET /api/v1/orders/statistics/`
Get order execution statistics.

### Performance

#### `GET /api/v1/performance/`
Get current performance snapshot.

**Response:**
```json
{
  "timestamp": "2026-02-19",
  "portfolio_value": 1000000.0,
  "total_pnl": 150000.0,
  "realized_pnl": 85000.0,
  "unrealized_pnl": 65000.0,
  "total_return": 0.176,
  "sharpe_ratio": 1.85,
  "sortino_ratio": 2.12,
  "max_drawdown": -0.087,
  "win_rate": 0.625,
  "profit_factor": 1.85,
  "num_trades": 245
}
```

#### `GET /api/v1/performance/equity-curve`
Get equity curve data.

**Query Parameters:**
- `start_date`: Start date (YYYY-MM-DD)
- `end_date`: End date (YYYY-MM-DD)
- `frequency`: Data frequency (`daily`, `weekly`, `monthly`)

#### `GET /api/v1/performance/risk-metrics?lookback_days=30`
Get risk metrics with rolling window.

#### `GET /api/v1/performance/benchmark-comparison?benchmark=SPY`
Compare portfolio performance to benchmark.

**Supported benchmarks:** SPY, QQQ, DIA, IWM, VTI

#### `GET /api/v1/performance/export?start_date=2024-01-01&end_date=2024-12-31&format=json`
Export performance report.

**Query Parameters:**
- `start_date`: Required start date
- `end_date`: Required end date
- `format`: Export format (`json` or `csv`)

## WebSocket Endpoints

Real-time data streaming via WebSocket.

### `WS /ws/portfolio`
Real-time portfolio updates.

### `WS /ws/positions`
Real-time position updates.

### `WS /ws/orders`
Real-time order updates and fills.

### `WS /ws/performance`
Real-time performance metrics updates.

### Example WebSocket Client

```python
import websockets
import asyncio
import json

async def subscribe_to_portfolio():
    uri = "ws://localhost:8000/ws/portfolio"
    
    async with websockets.connect(uri) as websocket:
        while True:
            message = await websocket.recv()
            data = json.loads(message)
            print(f"Portfolio Update: {data}")

asyncio.run(subscribe_to_portfolio())
```

## Interactive Documentation

FastAPI provides interactive API documentation:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## Error Handling

All endpoints return standard HTTP status codes:

- `200 OK`: Successful request
- `400 Bad Request`: Invalid parameters
- `401 Unauthorized`: Missing API key
- `403 Forbidden`: Invalid API key
- `404 Not Found`: Resource not found
- `500 Internal Server Error`: Server error

Error responses include a detail message:

```json
{
  "detail": "Order 9999 not found"
}
```

## Rate Limiting

(To be implemented based on deployment requirements)

## Examples

### Python

```python
import requests

BASE_URL = "http://localhost:8000"

# Get portfolio summary
response = requests.get(f"{BASE_URL}/api/v1/portfolio/")
portfolio = response.json()
print(f"Portfolio Value: ${portfolio['portfolio_value']:,.2f}")

# Get current positions
response = requests.get(f"{BASE_URL}/api/v1/positions/")
positions = response.json()
for pos in positions:
    print(f"{pos['symbol']}: {pos['quantity']} shares @ ${pos['current_price']}")

# Get performance metrics
response = requests.get(f"{BASE_URL}/api/v1/performance/")
perf = response.json()
print(f"Sharpe Ratio: {perf['sharpe_ratio']:.2f}")
print(f"Win Rate: {perf['win_rate']:.1%}")
```

### cURL

```bash
# Health check
curl http://localhost:8000/health/

# Get portfolio
curl http://localhost:8000/api/v1/portfolio/

# Get positions
curl http://localhost:8000/api/v1/positions/

# Get performance with authentication
curl -H "X-API-Key: your-api-key" http://localhost:8000/api/v1/performance/

# Export performance report
curl "http://localhost:8000/api/v1/performance/export?start_date=2024-01-01&end_date=2024-12-31&format=json"
```

### JavaScript

```javascript
// Fetch portfolio data
fetch('http://localhost:8000/api/v1/portfolio/')
  .then(response => response.json())
  .then(data => {
    console.log('Portfolio Value:', data.portfolio_value);
  });

// WebSocket subscription
const ws = new WebSocket('ws://localhost:8000/ws/portfolio');

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log('Portfolio Update:', data);
};
```

## Running the API Server

### Development

```bash
# Without authentication
python scripts/run_api.py

# With authentication
python scripts/run_api.py --auth

# Custom host/port
python scripts/run_api.py --host 0.0.0.0 --port 8080

# With auto-reload
python scripts/run_api.py --reload
```

### Production

```bash
# Using Gunicorn with Uvicorn workers
gunicorn copilot_quant.api.main:create_app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

### Docker

```dockerfile
FROM python:3.12-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

CMD ["uvicorn", "copilot_quant.api.main:create_app", "--host", "0.0.0.0", "--port", "8000"]
```

## Monitoring

### Prometheus Integration

Add the metrics endpoint to your Prometheus configuration:

```yaml
scrape_configs:
  - job_name: 'copilot-quant-api'
    static_configs:
      - targets: ['localhost:8000']
    metrics_path: '/metrics/prometheus'
    scrape_interval: 15s
```

### Grafana Dashboard

Import metrics from Prometheus to create dashboards for:
- Request rate and latency
- Error rates
- System resources (CPU, memory, disk)
- Application metrics (portfolio value, number of positions, etc.)

## Support

For issues and questions:
- GitHub Issues: https://github.com/harryb2088/copilot_quant/issues
- Documentation: See README.md
