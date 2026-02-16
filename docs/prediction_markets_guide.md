# Prediction Market Data Guide

## Overview

The Copilot Quant platform now supports fetching data from prediction market platforms, enabling you to incorporate prediction market probabilities into your trading strategies.

**Supported Platforms:**
- **Polymarket**: Decentralized prediction market on Polygon
- **Kalshi**: CFTC-regulated prediction market exchange

---

## Quick Start

### Basic Usage

```python
from copilot_quant.data.prediction_markets import (
    PolymarketProvider,
    KalshiProvider,
    get_prediction_market_provider,
)

# Get Polymarket data
polymarket = PolymarketProvider()
markets = polymarket.get_active_markets(limit=10)
print(markets[['question', 'volume', 'end_date']])

# Get Kalshi data
kalshi = KalshiProvider()
markets = kalshi.get_active_markets(limit=10)
print(markets[['question', 'yes_bid', 'yes_ask']])
```

### Using the Provider Factory

```python
# Create providers using the factory function
polymarket = get_prediction_market_provider('polymarket')
kalshi = get_prediction_market_provider('kalshi', api_key='your_key')
```

---

## Polymarket Provider

### Fetching Active Markets

```python
provider = PolymarketProvider(rate_limit_delay=1.0)

# Get all active markets
markets = provider.get_active_markets(limit=100)

# Filter by category
crypto_markets = provider.get_active_markets(category='crypto', limit=50)
```

**Returned DataFrame columns:**
- `market_id`: Unique market identifier
- `question`: Market question/description
- `category`: Market category
- `end_date`: Market close date
- `volume`: Trading volume
- `liquidity`: Available liquidity
- `created_at`: Market creation date
- `active`: Market status

### Getting Market Prices

```python
# Get current price for a specific market
market_id = 'some-market-id'
prices = provider.get_market_prices(market_id)

# DataFrame with timestamp, price, volume, liquidity
print(prices[['timestamp', 'price']])
```

### Getting Market Details

```python
# Get detailed information about a market
info = provider.get_market_info(market_id)
print(f"Question: {info['question']}")
print(f"Current Price: {info['price']}")
```

---

## Kalshi Provider

### Authentication (Optional)

For public market data, authentication is typically not required. For authenticated endpoints:

```python
provider = KalshiProvider(
    api_key='your_api_key',
    api_secret='your_api_secret',
    rate_limit_delay=1.0
)
```

### Fetching Active Markets

```python
provider = KalshiProvider()

# Get all active markets
markets = provider.get_active_markets(limit=100)

# Filter by category
econ_markets = provider.get_active_markets(category='economics')
```

**Returned DataFrame columns:**
- `market_id`: Market ticker
- `question`: Market title/question
- `category`: Market category
- `end_date`: Market close time
- `volume`: Trading volume
- `liquidity`: Available liquidity
- `yes_bid`: Current Yes bid price
- `yes_ask`: Current Yes ask price
- `no_bid`: Current No bid price
- `no_ask`: Current No ask price

### Getting Historical Prices

```python
# Get price history for a market
ticker = 'SOME-TICKER'
prices = provider.get_market_prices(
    ticker,
    start_date='2024-01-01',
    end_date='2024-02-01'
)

print(prices[['timestamp', 'yes_bid', 'yes_ask']])
```

---

## Use Cases

### 1. Market Sentiment Analysis

```python
# Get crypto-related markets
polymarket = PolymarketProvider()
crypto_markets = polymarket.get_active_markets(category='crypto')

# Analyze sentiment based on probabilities
for idx, market in crypto_markets.iterrows():
    print(f"Q: {market['question']}")
    print(f"Volume: ${market['volume']:,.0f}")
    print()
```

### 2. Cross-Platform Comparison

```python
# Compare similar markets across platforms
polymarket = PolymarketProvider()
kalshi = KalshiProvider()

poly_markets = polymarket.get_active_markets()
kalshi_markets = kalshi.get_active_markets()

print(f"Polymarket: {len(poly_markets)} markets")
print(f"Kalshi: {len(kalshi_markets)} markets")
```

### 3. Integration with Trading Strategies

```python
# Example: Use prediction market data as a signal
def check_market_sentiment(symbol):
    """Check if prediction markets are bullish on a sector."""
    polymarket = PolymarketProvider()
    
    # Search for relevant markets
    markets = polymarket.get_active_markets(category='crypto')
    
    # Analyze sentiment (simplified example)
    for market in markets.itertuples():
        if symbol.lower() in market.question.lower():
            print(f"Found relevant market: {market.question}")
            # Use market data in your strategy logic
```

---

## API Limitations & Best Practices

### Rate Limiting

Both platforms have rate limits. Always use the `rate_limit_delay` parameter:

```python
# Add delay between API calls
provider = PolymarketProvider(rate_limit_delay=1.0)  # 1 second delay
```

### Error Handling

```python
try:
    markets = provider.get_active_markets()
    if markets.empty:
        print("No markets returned")
except Exception as e:
    print(f"Error fetching markets: {e}")
```

### Caching Results

For production use, cache API responses to minimize requests:

```python
import pickle
from datetime import datetime, timedelta

# Cache markets data
cache_file = 'markets_cache.pkl'
cache_age = timedelta(hours=1)

# Try to load from cache
try:
    with open(cache_file, 'rb') as f:
        cached = pickle.load(f)
        if datetime.now() - cached['timestamp'] < cache_age:
            markets = cached['data']
        else:
            # Cache expired, fetch new data
            markets = provider.get_active_markets()
            with open(cache_file, 'wb') as f:
                pickle.dump({'timestamp': datetime.now(), 'data': markets}, f)
except FileNotFoundError:
    # No cache, fetch fresh data
    markets = provider.get_active_markets()
```

---

## Important Notes

### API Status

⚠️ **Prediction market APIs are subject to change**
- Public APIs may be modified or deprecated
- Some endpoints may require authentication
- Always check the platform's official documentation

### Data Availability

- **Polymarket**: Public API may have limited endpoints
- **Kalshi**: Some endpoints require authentication
- Real-time data may require paid subscriptions

### Terms of Service

Always review and comply with each platform's terms of service:
- **Polymarket**: https://polymarket.com/terms-of-use
- **Kalshi**: https://kalshi.com/terms-of-service

---

## Getting API Keys

### Polymarket
1. Currently uses public endpoints (no key required for basic data)
2. For advanced features, check Polymarket's developer portal

### Kalshi
1. Sign up at https://kalshi.com/
2. Navigate to API settings in your account
3. Generate API credentials
4. Store credentials securely:
   ```bash
   export KALSHI_API_KEY="your_key"
   export KALSHI_API_SECRET="your_secret"
   ```

---

## Troubleshooting

### "No data returned"
- API endpoint may have changed
- Network issues or rate limiting
- Check platform status and documentation

### Authentication Errors
- Verify API credentials
- Check if endpoint requires authentication
- Ensure proper header formatting

### Data Format Issues
- API response structure may have changed
- Update provider implementation
- Check for API version updates

---

## Advanced Usage

### Custom Provider Implementation

You can create your own prediction market provider:

```python
from copilot_quant.data.prediction_markets import PredictionMarketProvider

class CustomProvider(PredictionMarketProvider):
    def get_active_markets(self, category=None, limit=None):
        # Implement custom logic
        pass
    
    def get_market_prices(self, market_id, start_date=None, end_date=None):
        # Implement custom logic
        pass
    
    def get_market_info(self, market_id):
        # Implement custom logic
        pass
```

---

## Examples

See `examples/prediction_market_examples.py` for comprehensive usage examples.

---

## Support

For questions or issues:
1. Check the official platform documentation
2. Review example scripts
3. Open an issue on GitHub

---

**Last Updated**: 2026-02-16  
**API Versions**: Subject to change - always verify with official docs
