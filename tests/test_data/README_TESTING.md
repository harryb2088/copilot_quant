# Prediction Market Testing Strategy

## Overview

This directory contains comprehensive tests for data pipeline modules, including prediction market data providers, S&P500 data loaders, normalization utilities, and update/backfill jobs. All tests use a **mock-first approach** to ensure they run reliably in CI/CD environments without requiring external API access.

## Test Coverage

### Data Pipeline Test Modules

1. **`test_eod_loader.py`** (11 tests)
   - S&P500 EOD data loader initialization
   - Daily fetch functionality
   - Missing symbol error handling
   - Split and dividend data capture
   - CSV and SQLite storage operations
   - Batch fetch with error handling

2. **`test_prediction_markets.py`** (39 tests)
   - Provider initialization (Polymarket, Kalshi, PredictIt, Metaculus)
   - Market listing and data fetching
   - Schema validation for all providers
   - Bad data handling (malformed JSON, missing fields, API errors)
   - Timeout and error handling
   - Provider factory pattern
   - Data storage (CSV and SQLite)

3. **`test_normalization.py`** (62 tests)
   - Symbol normalization across providers
   - Timestamp normalization with timezone handling
   - Column name standardization
   - Split and dividend adjustments
   - Data quality validation
   - Outlier detection and removal
   - Data resampling
   - Idempotence tests (applying operations twice)
   - Edge cases (empty DataFrames, single rows, extreme values)

4. **`test_update_jobs.py`** (24 tests)
   - Data updater initialization
   - Incremental updates
   - Backfill operations
   - Gap detection and filling
   - Metadata management and corruption recovery
   - Batch update with partial failures
   - Log file validation

5. **`test_providers.py`** (9 tests)
   - yfinance provider functionality
   - Historical data fetching
   - Multi-symbol operations

6. **`test_sp500.py`** (11 tests)
   - S&P500 ticker list retrieval
   - Predefined portfolios (FAANG, Magnificent 7, DOW 30)

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

### Test Organization

Tests are organized into logical test classes:

**S&P500 Loader Tests:**
- `TestSP500EODLoader`: Basic functionality, initialization, storage
- Enhanced tests for daily fetch, split handling, dividend capture, error handling

**Prediction Market Tests:**
- `TestPolymarketProvider`: Polymarket API integration
- `TestKalshiProvider`: Kalshi API integration
- `TestPredictItProvider`: PredictIt API integration
- `TestMetaculusProvider`: Metaculus API integration
- `TestSchemaValidation`: Schema validation across all providers
- `TestBadDataHandling`: Error handling for malformed data
- `TestPredictionMarketStorage`: Data storage operations
- `TestProviderFactory`: Provider factory pattern

**Normalization Tests:**
- `TestSymbolNormalization`: Symbol format normalization
- `TestTimestampNormalization`: Timezone handling
- `TestColumnNameStandardization`: Column naming
- `TestSplitAdjustment`: Stock split adjustments
- `TestDataQualityValidation`: Data quality checks
- `TestNormalizationIdempotence`: Idempotence verification
- `TestNormalizationEdgeCases`: Edge case handling

**Update Jobs Tests:**
- `TestDataUpdater`: Core update functionality
- `TestLogFileValidation`: Log file creation and validation
- `TestMetadataManagement`: Metadata tracking and recovery
- `TestPartialFailureRecovery`: Batch failure handling

### Running Specific Test Suites

Run all data pipeline tests:
```bash
pytest tests/test_data/
```

Run only S&P500 tests:
```bash
pytest tests/test_data/test_eod_loader.py tests/test_data/test_sp500.py -v
```

Run only prediction market tests:
```bash
pytest tests/test_data/test_prediction_markets.py -v
```

Run only normalization tests:
```bash
pytest tests/test_data/test_normalization.py -v
```

Run only update job tests:
```bash
pytest tests/test_data/test_update_jobs.py -v
```

Run with specific test class:
```bash
pytest tests/test_data/test_prediction_markets.py::TestSchemaValidation -v
```

Run specific test:
```bash
pytest tests/test_data/test_normalization.py::TestNormalizationIdempotence::test_normalize_symbol_idempotent -v
```

All tests use comprehensive mocks and will pass without any network access.

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
