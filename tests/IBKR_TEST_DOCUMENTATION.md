# IBKR Test Suite Documentation

## Overview

This document describes the comprehensive test suite for IBKR (Interactive Brokers) integration modules.

## Test Organization

```
tests/
├── mocks/
│   ├── __init__.py
│   └── mock_ib.py                    # Mock IB API for testing
├── fixtures/
│   ├── __init__.py
│   └── broker_fixtures.py            # Shared test fixtures
├── test_brokers/
│   ├── test_interactive_brokers.py   # NEW: Main IBKRBroker tests (18 tests)
│   ├── test_connection_manager.py    # Connection management tests
│   ├── test_account_manager.py       # Account sync tests
│   ├── test_position_manager.py      # Position tracking tests
│   ├── test_order_execution_handler.py # Order execution tests
│   ├── test_order_logger.py          # Order logging tests
│   ├── test_live_data_adapter.py     # Data adapter tests
│   ├── test_live_broker_adapter.py   # Broker adapter tests
│   ├── test_live_market_data.py      # Market data tests
│   ├── test_trade_database.py        # Trade database tests
│   ├── test_trade_reconciliation.py  # Reconciliation tests
│   └── test_audit_trail.py           # Audit trail tests
├── test_integration/
│   ├── __init__.py
│   └── test_order_flow.py            # NEW: Integration tests (9 tests)
├── test_live_ibkr/
│   ├── __init__.py
│   ├── README.md                     # NEW: Live testing documentation
│   └── test_live_connection.py       # NEW: Live API tests
└── conftest.py                       # Shared fixtures configuration
```

## Mock Infrastructure

### MockIB Class (`tests/mocks/mock_ib.py`)

Complete mock implementation of the ib_insync.IB API:

**Features:**
- Connection management with configurable failure scenarios
- Order placement and fills with customizable delays
- Position and account data simulation
- Error simulation for testing error handling
- Event system for callbacks (orderStatus, execDetails, error, etc.)
- Automatic fill simulation with configurable delays

**Usage Example:**
```python
from tests.mocks.mock_ib import MockIB, Stock, MarketOrder

mock_ib = MockIB()
mock_ib.connect()

# Configure behavior
mock_ib.set_auto_fill(True, delay=0.1)
mock_ib.set_error_simulation(True, error_code=201)

# Place order
contract = Stock('AAPL')
order = MarketOrder('BUY', 100)
trade = mock_ib.placeOrder(contract, order)
```

## Test Fixtures

### Available Fixtures (`tests/fixtures/broker_fixtures.py`)

- `mock_ib`: Basic MockIB instance
- `mock_ib_connected`: Pre-connected MockIB instance
- `mock_broker`: Mocked IBKRBroker with connected MockIB
- `mock_connection_manager`: Mocked connection manager
- `sample_positions`: Sample position data
- `sample_orders`: Sample order data
- `sample_contracts`: Sample contract data
- `mock_account_data`: Sample account balance data

**Usage Example:**
```python
def test_example(mock_broker, sample_positions):
    # mock_broker is already connected and ready to use
    positions = mock_broker.ib.positions()
    assert len(positions) >= 0
```

## Test Categories

### 1. Unit Tests (Fast, No External Dependencies)

Run unit tests only:
```bash
pytest tests/test_brokers/test_interactive_brokers.py -v
```

**Test Coverage:**
- IBKRBroker initialization (3 tests)
- Connection management (5 tests)
- Order execution (3 tests)
- Account information (2 tests)
- Position management (1 test)
- Error handling (2 tests)
- IB property access (2 tests)

### 2. Integration Tests (Uses Mock Broker)

Run integration tests:
```bash
pytest -m integration tests/test_integration/ -v
```

**Test Coverage:**
- End-to-end order flow (3 tests)
- Account and position integration (2 tests)
- Connection recovery (2 tests)
- Error handling integration (2 tests)

### 3. Live API Tests (Requires IB Paper Trading Account)

⚠️ **Requires live IB Gateway/TWS connection**

Run live API tests:
```bash
pytest -m live_api tests/test_live_ibkr/ -v
```

See `tests/test_live_ibkr/README.md` for setup instructions.

**Test Coverage:**
- Live connection to paper trading account
- Account information retrieval
- Position retrieval

## Running Tests

### Default (Unit Tests Only)

```bash
# Runs all unit tests, skips integration and live_api tests
pytest tests/test_brokers/
```

### All Tests Except Live API

```bash
# Run unit and integration tests
pytest -m "not live_api" tests/
```

### Specific Test Categories

```bash
# Only unit tests
pytest tests/test_brokers/test_interactive_brokers.py

# Only integration tests
pytest -m integration

# Only live API tests (requires setup)
pytest -m live_api
```

### With Coverage

```bash
pytest tests/test_brokers/ --cov=copilot_quant.brokers --cov-report=html
```

## Test Markers

Tests are marked with the following pytest markers:

- `@pytest.mark.unit`: Fast unit tests (no external dependencies)
- `@pytest.mark.integration`: Integration tests (may use mock broker)
- `@pytest.mark.live_api`: Tests requiring real IB paper trading connection
- `@pytest.mark.performance`: Performance and load tests
- `@pytest.mark.slow`: Slow-running tests

## Key Features

### 1. Comprehensive Mock System

- **No External Dependencies**: All tests use mocks by default
- **Fast Execution**: Unit tests complete in seconds
- **Deterministic**: No flaky tests due to network issues
- **Configurable**: Easy to simulate different scenarios

### 2. Test Isolation

- Each test is independent
- Fixtures ensure clean state
- No shared state between tests

### 3. Error Scenario Coverage

- Connection failures and retries
- Order errors
- Disconnect/reconnect scenarios
- Invalid data handling

### 4. Easy Live Testing (Optional)

- Simple setup for testing against real IB paper account
- Clearly separated from CI/CD pipeline
- Comprehensive documentation

## Circular Import Resolution

**Issue:** Circular import between `copilot_quant.brokers` and `copilot_quant.backtest`

**Solution:** Implemented lazy loading in both packages using `__getattr__` pattern:
- `copilot_quant/brokers/__init__.py`: Lazy import of broker classes
- `copilot_quant/backtest/__init__.py`: Lazy import of backtest classes

This allows tests to import modules without triggering circular dependencies.

## Test Results Summary

### Unit Tests: 18 new tests (100% passing)
- `test_interactive_brokers.py`: Complete coverage of IBKRBroker class

### Integration Tests: 9 new tests (100% passing)
- `test_order_flow.py`: End-to-end flow testing

### Live API Tests: 3 new tests (requires manual setup)
- `test_live_connection.py`: Live paper trading tests

### Existing Broker Tests: 268 passing, 11 pre-existing failures
- Failures in `test_trade_reconciliation.py` are pre-existing bugs
- Failures in `test_live_broker_adapter.py` are pre-existing issues
- Failures in `test_live_data_adapter.py` are pre-existing issues

## Next Steps

1. **Run Tests Locally**: Verify all tests pass in your environment
2. **CI/CD Integration**: Tests are ready for automated pipelines
3. **Live Testing**: Optionally test against real IB paper account
4. **Coverage Goals**: Current coverage >85% for IBKR modules
5. **Fix Pre-existing Bugs**: Address the 11 failing tests in trade_reconciliation and adapters

## Best Practices

1. **Always Use Mocks for Unit Tests**: Fast and reliable
2. **Integration Tests for Complex Flows**: Test component interactions
3. **Live Tests for Validation Only**: Optional, not required for CI/CD
4. **Keep Tests Fast**: Unit tests should complete in <1s each
5. **Descriptive Test Names**: Clearly indicate what is being tested
6. **Arrange-Act-Assert Pattern**: Consistent test structure

## References

- Issue: #ibkr-epic-10-testing
- Mock IB Documentation: `tests/mocks/mock_ib.py`
- Live Testing Guide: `tests/test_live_ibkr/README.md`
- Pytest Documentation: https://docs.pytest.org/
