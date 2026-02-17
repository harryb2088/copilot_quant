# Prediction Market Testing Strategy

## Overview

This directory contains tests for prediction market data providers. All tests use a **mock-first approach** to ensure they run reliably in CI/CD environments without requiring external API access.

## Why Mock-First?

The following prediction market APIs are blocked by firewall rules in CI/CD:
- `gamma-api.polymarket.com` (Polymarket)
- `api.elections.kalshi.com` (Kalshi)
- `www.predictit.org` (PredictIt)
- `www.metaculus.com` (Metaculus)

By using mocks, we ensure:
1. ✅ Tests pass in CI/CD without API access
2. ✅ Tests are fast and deterministic
3. ✅ Tests don't depend on external service availability
4. ✅ MVP can be deployed without API reliability concerns

## Running Tests

### Standard Tests (Mock-based)

Run all tests using mocks (default):
```bash
pytest tests/test_data/test_prediction_markets.py
```

All 22 tests use comprehensive mocks and will pass without any network access.

### Live API Tests (Optional)

To test against live APIs locally (when implementing new features):

1. Mark your test with the `@pytest.mark.live_api` decorator:
```python
@pytest.mark.live_api
def test_live_polymarket_api(self, provider):
    """Test real Polymarket API (requires network access)."""
    markets = provider.list_markets(limit=5)
    assert isinstance(markets, pd.DataFrame)
```

2. Run live API tests:
```bash
pytest -m live_api tests/test_data/test_prediction_markets.py
```

3. Run everything except live API tests (CI/CD default):
```bash
pytest -m "not live_api" tests/test_data/test_prediction_markets.py
```

## Mock Data

Comprehensive mock data generators are available in:
```
tests/test_data/mock_prediction_markets/mock_data.py
```

These generators provide realistic data for:
- Market listings
- Price history
- Contract data
- Prediction data

## Future Work

As API reliability improves, live API tests can be added incrementally:

1. Add tests with `@pytest.mark.live_api` decorator
2. Keep mock-based tests as the primary strategy
3. Use live tests for periodic validation only
4. Never require live tests in CI/CD pipeline

## Configuration

Pytest configuration is in `pytest.ini`:
- `live_api` marker is registered
- Live API tests are skipped by default
- Use `-m live_api` to run them explicitly
