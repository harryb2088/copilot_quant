# Issue: Unit & Integration Tests (Mock and Real IB API)

**Epic**: Live Trading & Interactive Brokers (IBKR) Integration  
**Priority**: Critical  
**Status**: Not Started  
**Created**: 2026-02-18

## Overview
Create comprehensive test suite for all IBKR integration components, including unit tests, integration tests with mock IB API, and optional tests with real IB paper trading account.

## Requirements

### 1. Unit Tests
- [ ] Connection management tests
- [ ] Order execution tests
- [ ] Account sync tests
- [ ] Position tracking tests
- [ ] Data adapter tests
- [ ] Configuration tests
- [ ] Signal routing tests
- [ ] Reconciliation tests

### 2. Mock IB API
- [ ] Create mock IB connection
- [ ] Mock order placement and fills
- [ ] Mock market data streaming
- [ ] Mock account data
- [ ] Mock position updates
- [ ] Configurable mock responses
- [ ] Simulate IB errors

### 3. Integration Tests
- [ ] End-to-end order flow (signal → execution → fill)
- [ ] Strategy execution tests
- [ ] Data pipeline integration
- [ ] UI integration tests
- [ ] Multi-component interaction tests
- [ ] Error recovery tests
- [ ] Reconnection tests

### 4. Paper Trading Tests (Optional)
- [ ] Real IB paper trading connection tests
- [ ] Real order placement tests
- [ ] Real market data tests
- [ ] Performance tests with real API
- [ ] Rate limit tests
- [ ] Long-running stability tests

### 5. Performance Tests
- [ ] High-frequency order tests
- [ ] Large position portfolio tests
- [ ] Concurrent strategy tests
- [ ] Memory leak detection
- [ ] Latency measurements
- [ ] Throughput tests

## Implementation Tasks

### Mock IB API
```python
# tests/mocks/mock_ib.py
class MockIB:
    """
    Mock Interactive Brokers API for testing
    """
    def __init__(self):
        self._connected = False
        self._orders = {}
        self._positions = {}
        self._account_values = {}
        
    def connect(self, host: str, port: int, clientId: int) -> None:
        """Mock connection"""
        self._connected = True
        
    def placeOrder(self, contract, order):
        """Mock order placement"""
        trade = MockTrade(contract, order)
        self._orders[order.orderId] = trade
        # Simulate fill after delay
        self._simulate_fill(trade)
        return trade
        
    def positions(self):
        """Mock positions"""
        return list(self._positions.values())
        
    def accountSummary(self):
        """Mock account summary"""
        return list(self._account_values.values())
```

### Test Fixtures
```python
# tests/fixtures/broker_fixtures.py
import pytest

@pytest.fixture
def mock_broker():
    """Provide mock IBKR broker"""
    broker = IBKRBroker(paper_trading=True)
    broker.ib = MockIB()
    return broker

@pytest.fixture
def mock_account_manager(mock_broker):
    """Provide mock account manager"""
    return IBKRAccountManager(mock_broker)

@pytest.fixture
def sample_positions():
    """Provide sample position data"""
    return [
        Position(symbol='AAPL', quantity=100, avg_cost=150.0, ...),
        Position(symbol='TSLA', quantity=50, avg_cost=200.0, ...),
    ]
```

### Unit Test Examples
```python
# tests/test_brokers/test_connection.py
def test_connection_establishment(mock_broker):
    """Test successful connection"""
    assert mock_broker.connect()
    assert mock_broker.is_connected()

def test_connection_retry(mock_broker):
    """Test connection retry logic"""
    mock_broker.ib.fail_first_connection = True
    assert mock_broker.connect(retry_count=3)

# tests/test_brokers/test_order_execution.py
def test_market_order_placement(mock_broker):
    """Test market order placement"""
    trade = mock_broker.execute_market_order('AAPL', 100, 'buy')
    assert trade is not None
    assert trade.order.totalQuantity == 100

def test_order_validation(mock_broker):
    """Test order validation"""
    validator = OrderValidator(mock_broker)
    order = Order(symbol='AAPL', quantity=1000000, ...)
    result = validator.validate_order(order)
    assert not result.valid
    assert 'position limit' in result.errors

# tests/test_brokers/test_position_sync.py
def test_position_retrieval(mock_broker, sample_positions):
    """Test position retrieval"""
    mock_broker.ib._positions = sample_positions
    positions = mock_broker.get_positions()
    assert len(positions) == 2
    assert positions[0]['symbol'] == 'AAPL'
```

### Integration Test Examples
```python
# tests/test_integration/test_strategy_execution.py
def test_end_to_end_strategy_execution():
    """Test complete strategy execution flow"""
    # Setup
    broker = IBKRBroker(paper_trading=True)
    broker.ib = MockIB()
    strategy_adapter = LiveStrategyAdapter(broker)
    
    # Create simple strategy
    strategy = MockStrategy()
    strategy_adapter.register_strategy(strategy)
    
    # Generate signal
    signal = Signal(
        strategy_id='test',
        symbol='AAPL',
        action=SignalAction.BUY,
        quantity=100
    )
    
    # Process signal → order → fill
    order = strategy_adapter.process_signal(signal)
    assert order is not None
    
    # Wait for fill
    time.sleep(0.1)
    
    # Verify position
    positions = broker.get_positions()
    assert len(positions) == 1
    assert positions[0]['symbol'] == 'AAPL'
    assert positions[0]['position'] == 100

# tests/test_integration/test_reconnection.py
def test_automatic_reconnection():
    """Test automatic reconnection on disconnect"""
    broker = IBKRBroker(paper_trading=True)
    broker.ib = MockIB()
    
    # Connect
    assert broker.connect()
    
    # Simulate disconnect
    broker.ib.disconnect()
    assert not broker.is_connected()
    
    # Should auto-reconnect
    time.sleep(6)  # Wait for reconnection attempt
    assert broker.is_connected()
```

### Performance Test Examples
```python
# tests/test_performance/test_order_throughput.py
def test_order_throughput():
    """Test order placement throughput"""
    broker = IBKRBroker(paper_trading=True)
    broker.ib = MockIB()
    broker.connect()
    
    start_time = time.time()
    num_orders = 100
    
    for i in range(num_orders):
        broker.execute_market_order('SPY', 1, 'buy')
    
    duration = time.time() - start_time
    throughput = num_orders / duration
    
    assert throughput > 10  # At least 10 orders/second
    print(f"Throughput: {throughput:.2f} orders/second")

# tests/test_performance/test_latency.py
def test_order_latency():
    """Test order placement latency"""
    broker = IBKRBroker(paper_trading=True)
    broker.ib = MockIB()
    broker.connect()
    
    latencies = []
    
    for _ in range(100):
        start = time.time()
        broker.execute_market_order('SPY', 1, 'buy')
        latency = time.time() - start
        latencies.append(latency)
    
    avg_latency = sum(latencies) / len(latencies)
    p95_latency = sorted(latencies)[94]
    
    assert avg_latency < 0.1  # < 100ms average
    assert p95_latency < 0.2  # < 200ms p95
```

## Test Organization
```
tests/
├── __init__.py
├── conftest.py                    # Shared fixtures
├── mocks/
│   ├── __init__.py
│   ├── mock_ib.py                # Mock IB API
│   └── mock_data.py              # Mock market data
├── fixtures/
│   ├── __init__.py
│   ├── broker_fixtures.py        # Broker fixtures
│   └── data_fixtures.py          # Data fixtures
├── test_brokers/
│   ├── __init__.py
│   ├── test_connection.py
│   ├── test_order_execution.py
│   ├── test_account_sync.py
│   ├── test_position_manager.py
│   └── test_data_adapter.py
├── test_integration/
│   ├── __init__.py
│   ├── test_strategy_execution.py
│   ├── test_reconnection.py
│   ├── test_data_pipeline.py
│   └── test_ui_integration.py
├── test_performance/
│   ├── __init__.py
│   ├── test_order_throughput.py
│   ├── test_latency.py
│   └── test_concurrent_strategies.py
└── test_live/  # Optional, requires IB paper account
    ├── __init__.py
    ├── test_live_connection.py
    ├── test_live_orders.py
    └── README.md
```

## Pytest Configuration
```ini
# pytest.ini
[pytest]
markers =
    unit: Unit tests (fast, no external dependencies)
    integration: Integration tests (may use mock broker)
    live_api: Tests requiring real IB paper trading connection
    performance: Performance and load tests
    slow: Slow-running tests

# Default: run only unit and integration tests
addopts = 
    --verbose
    --strict-markers
    -m "not live_api and not performance"
    --cov=copilot_quant.brokers
    --cov-report=html
    --cov-report=term

testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
```

## Test Coverage Requirements
- [ ] Overall coverage > 80%
- [ ] Critical paths (orders, positions) > 95%
- [ ] Connection management > 90%
- [ ] Error handling paths covered
- [ ] Edge cases tested

## Acceptance Criteria
- [ ] All unit tests passing
- [ ] All integration tests passing
- [ ] Code coverage > 80%
- [ ] No memory leaks in long-running tests
- [ ] Performance benchmarks met
- [ ] CI/CD pipeline integration
- [ ] Tests documented
- [ ] Mock IB API feature-complete

## CI/CD Integration
```yaml
# .github/workflows/test.yml
name: Test IBKR Integration

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v2
    
    - name: Set up Python
      uses: actions/setup-python@v2
      with:
        python-version: '3.9'
    
    - name: Install dependencies
      run: |
        pip install -r requirements.txt
        pip install pytest pytest-cov pytest-mock
    
    - name: Run unit tests
      run: pytest -m unit
    
    - name: Run integration tests
      run: pytest -m integration
    
    - name: Upload coverage
      uses: codecov/codecov-action@v2
```

## Related Files
- `tests/mocks/mock_ib.py` - Mock IB API (to create)
- `tests/fixtures/` - Test fixtures (to create)
- `tests/test_brokers/` - Unit tests (to create)
- `tests/test_integration/` - Integration tests (to create)
- `tests/test_performance/` - Performance tests (to create)
- `pytest.ini` - Pytest configuration (update)
- `.github/workflows/test.yml` - CI config (to create)

## Dependencies
- pytest>=7.0.0
- pytest-cov
- pytest-mock
- pytest-asyncio
- All IBKR integration modules

## Testing Best Practices
- [ ] Test one thing per test
- [ ] Use descriptive test names
- [ ] Arrange-Act-Assert pattern
- [ ] Clean up resources after tests
- [ ] Use fixtures for common setup
- [ ] Mock external dependencies
- [ ] Test edge cases and errors
- [ ] Keep tests fast (unit tests < 1s)

## References
- pytest documentation: https://docs.pytest.org/
- pytest-cov: https://pytest-cov.readthedocs.io/
- Testing best practices
