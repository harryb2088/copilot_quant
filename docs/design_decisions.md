# Backtesting Engine Design Decisions

## Overview

This document captures key design decisions made during the development of the Copilot Quant backtesting engine, including the rationale behind architectural choices and trade-offs considered.

## 1. Event-Driven Architecture

### Decision
Use an event-driven architecture that processes market data chronologically rather than vectorized backtesting.

### Rationale
- **Realistic Simulation**: Events occur in chronological order, matching how real trading works
- **Avoids Look-Ahead Bias**: Strategy can only access past data, preventing unrealistic perfect foresight
- **Flexibility**: Easy to add event handlers (on_data, on_fill) without changing core engine
- **Testability**: Each event can be tested independently

### Trade-offs
- **Performance**: Slower than vectorized approaches for simple strategies
- **Memory**: Must maintain state at each time step
- **Complexity**: More complex implementation than batch processing

### Alternatives Considered
1. **Vectorized Backtesting**: Fast but harder to avoid look-ahead bias
2. **Tick-by-Tick**: Most realistic but unnecessarily slow for daily data
3. **Batch Processing**: Simple but doesn't model temporal dependencies

### Conclusion
Event-driven provides the best balance of realism and performance for daily/intraday strategies.

---

## 2. Abstract Strategy Interface

### Decision
Use abstract base class (ABC) with lifecycle hooks (initialize, on_data, on_fill, finalize).

### Rationale
- **Separation of Concerns**: Strategy logic separate from execution
- **Template Method Pattern**: Consistent lifecycle across all strategies
- **Extensibility**: Easy to add new strategies without modifying engine
- **Type Safety**: Static type checking catches interface violations

### Trade-offs
- **Learning Curve**: Users must understand the lifecycle
- **Boilerplate**: Need to implement abstract methods even if empty
- **Rigidity**: Less flexible than pure duck typing

### Alternatives Considered
1. **Protocol/Duck Typing**: More flexible but less type-safe
2. **Callbacks Only**: Simpler but less structured
3. **Configuration-Based**: Limited to predefined strategies

### Implementation Details
```python
class Strategy(ABC):
    @abstractmethod
    def on_data(self, timestamp, data) -> List[Order]:
        """Required: Generate trading signals."""
        pass
    
    def on_fill(self, fill) -> None:
        """Optional: Handle order fills."""
        pass
```

The `on_data` method is required (abstract) because every strategy needs to generate signals. The `on_fill` method is optional because not all strategies need to track fills.

---

## 3. Transaction Cost Model

### Decision
Use percentage-based commission and slippage applied to all trades.

### Rationale
- **Simplicity**: Easy to understand and configure
- **Conservative**: Encourages realistic strategy development
- **Consistency**: Same model applies to all symbols
- **Industry Standard**: Matches typical retail trading costs

### Trade-offs
- **Accuracy**: Real costs vary by broker, symbol, order size
- **Sophistication**: Doesn't model market impact or bid-ask spread
- **Flexibility**: Fixed model may not suit all use cases

### Alternatives Considered
1. **Fixed Per-Share Commission**: Common for US stocks
2. **Volume-Based Slippage**: More realistic for large orders
3. **Bid-Ask Spread Model**: More accurate but requires tick data
4. **No Costs**: Unrealistic but useful for development

### Configuration
```python
BacktestEngine(
    commission=0.001,  # 0.1% of trade value
    slippage=0.0005    # 0.05% worse than mid-price
)
```

### Future Enhancements
- Tiered commission based on trade size
- Volume-weighted slippage
- Symbol-specific cost models

---

## 4. Position Tracking

### Decision
Track positions with average entry price and separate realized/unrealized P&L.

### Rationale
- **Accounting Accuracy**: Matches standard accounting practices
- **P&L Attribution**: Clear separation of closed vs. open positions
- **Tax Implications**: Realized P&L matters for taxes
- **Performance Analysis**: Helps identify profitable entry prices

### Trade-offs
- **Complexity**: More complex than simple quantity tracking
- **Memory**: Stores additional metadata per position
- **Calculation**: Requires updating on each fill

### Alternatives Considered
1. **Quantity-Only Tracking**: Simpler but less informative
2. **FIFO Cost Basis**: More accurate but complex
3. **Separate Long/Short Positions**: Clearer but harder to manage

### Implementation
```python
@dataclass
class Position:
    symbol: str
    quantity: float          # Positive = long, negative = short
    avg_entry_price: float   # Average cost basis
    unrealized_pnl: float    # Mark-to-market P&L
    realized_pnl: float      # Closed position P&L
```

When positions are increased, the average entry price is updated. When positions are closed, P&L is realized and moved from unrealized to realized.

---

## 5. Order Types

### Decision
Start with market and limit orders only; defer advanced order types.

### Rationale
- **MVP Approach**: Cover 80% of use cases with 20% of complexity
- **Simplicity**: Easier to implement and test
- **Extensibility**: Can add more types later without breaking changes

### Trade-offs
- **Limited Functionality**: Can't model stop-loss strategies directly
- **Workarounds**: Users must implement stops in strategy logic
- **Realism**: Missing common order types used in production

### Current Support
- **Market Orders**: Execute immediately at next price + slippage
- **Limit Orders**: Execute only if price reaches limit

### Future Order Types
1. **Stop Orders**: Trigger at stop price, execute as market
2. **Stop-Limit Orders**: Trigger at stop, execute as limit
3. **Trailing Stops**: Dynamic stop based on price movement
4. **OCO (One-Cancels-Other)**: Paired orders for brackets
5. **Bracket Orders**: Entry + stop-loss + take-profit

---

## 6. Data Provider Abstraction

### Decision
Use abstract DataProvider interface with concrete implementations.

### Rationale
- **Flexibility**: Easy to switch data sources without changing strategies
- **Testability**: Mock providers for unit testing
- **Extensibility**: Add new providers without modifying engine
- **Consistency**: Standardized data format across sources

### Trade-offs
- **Abstraction Overhead**: Extra layer of indirection
- **Format Conversion**: Must normalize different data formats
- **Feature Parity**: Some sources have unique capabilities

### Supported Providers
1. **YFinanceProvider**: Yahoo Finance (primary)
2. **CSVProvider**: Local CSV files
3. **MockProvider**: Synthetic data for testing
4. **DatabaseProvider**: SQL databases (future)

### Standard Data Format
```python
DataFrame with DatetimeIndex:
    - Open: float
    - High: float
    - Low: float
    - Close: float
    - Volume: int
```

All providers must return data in this format, regardless of source.

---

## 7. Portfolio vs. Broker Separation

### Decision
Combine portfolio tracking and broker execution in the BacktestEngine for now.

### Rationale
- **Simplicity**: Single place for state management
- **Performance**: No extra message passing
- **Cohesion**: Portfolio and execution are tightly coupled in backtesting

### Trade-offs
- **Coupling**: Less modular than separate components
- **Reusability**: Harder to use portfolio tracking independently
- **Testing**: Can't test portfolio logic without full engine

### Future Refactoring
For production systems, consider separating:
```python
class Portfolio:
    """Tracks positions and P&L."""
    positions: Dict[str, Position]
    cash: float
    
class Broker:
    """Executes orders and applies costs."""
    def execute_order(order, price) -> Fill:
        ...

class BacktestEngine:
    """Orchestrates backtest using Portfolio and Broker."""
    portfolio: Portfolio
    broker: Broker
```

This separation would enable:
- Independent testing of portfolio logic
- Different broker implementations (paper trading, live)
- Portfolio analytics without full backtest

---

## 8. Results Storage

### Decision
Store complete results in memory as BacktestResult dataclass.

### Rationale
- **Simplicity**: Easy to access and analyze
- **Performance**: Fast access to all metrics
- **Convenience**: Single object contains everything

### Trade-offs
- **Memory**: Large backtests consume significant memory
- **Persistence**: Results lost if not saved manually
- **Scalability**: Not suitable for very long backtests

### Alternatives Considered
1. **Database Storage**: Persistent but slower
2. **Streaming Results**: Low memory but can't re-analyze
3. **File-Based**: Simple but requires I/O

### Implementation
```python
@dataclass
class BacktestResult:
    strategy_name: str
    start_date: datetime
    end_date: datetime
    initial_capital: float
    final_capital: float
    total_return: float
    trades: List[Fill]
    portfolio_history: pd.DataFrame
```

### Future Enhancements
- Option to save to database
- Streaming mode for long backtests
- Compressed storage for large results

---

## 9. Error Handling Strategy

### Decision
Log errors and continue execution rather than failing fast.

### Rationale
- **Robustness**: Single bad data point doesn't kill backtest
- **Partial Results**: Get results even with some issues
- **Debugging**: Logs show where problems occurred

### Trade-offs
- **Silent Failures**: Errors might go unnoticed
- **Corrupted Results**: Bad data could skew results
- **Debugging**: Harder to find root cause

### Error Categories
1. **Data Errors**: Missing prices, invalid symbols
   - Action: Log warning, skip timestamp, continue
   
2. **Strategy Errors**: Exception in on_data()
   - Action: Log error, skip orders, continue
   
3. **Execution Errors**: Insufficient capital
   - Action: Reject order, log warning, continue
   
4. **System Errors**: Critical failures
   - Action: Save partial results, raise exception

### Configuration Option (Future)
```python
BacktestEngine(
    error_mode='continue'  # or 'strict' to fail fast
)
```

---

## 10. Performance Metrics

### Decision
Calculate basic metrics (return, trades) by default; defer advanced analytics.

### Rationale
- **MVP Approach**: Core metrics sufficient for most users
- **Performance**: Complex calculations can be slow
- **Extensibility**: Users can add custom metrics

### Included Metrics
- Total Return (%)
- Final Capital
- Number of Trades
- Trade Log
- Equity Curve

### Future Metrics (via separate analyzer)
- Sharpe Ratio
- Sortino Ratio
- Maximum Drawdown
- Calmar Ratio
- Win Rate
- Profit Factor
- Average Win/Loss
- Rolling Metrics

### Usage Pattern
```python
result = engine.run(...)

# Basic metrics (included)
print(result.total_return)
print(result.final_capital)

# Advanced metrics (future)
analyzer = PerformanceAnalyzer()
metrics = analyzer.analyze(result)
print(metrics['sharpe_ratio'])
print(metrics['max_drawdown'])
```

---

## 11. Multi-Strategy Support

### Decision
Support single strategy per backtest for now.

### Rationale
- **Simplicity**: One strategy = one set of orders
- **Clarity**: Clear attribution of performance
- **Common Case**: Most backtests test one strategy

### Trade-offs
- **Flexibility**: Can't test portfolio of strategies
- **Comparison**: Must run multiple backtests separately
- **Allocation**: Can't model dynamic allocation

### Current Pattern
```python
engine = BacktestEngine(...)
engine.add_strategy(MyStrategy())
result = engine.run(...)
```

### Future Multi-Strategy Support
```python
engine = BacktestEngine(...)
engine.add_strategy(Strategy1(), allocation=0.5)
engine.add_strategy(Strategy2(), allocation=0.5)
result = engine.run(...)
```

Challenges:
- Capital allocation between strategies
- Order prioritization
- Performance attribution
- Strategy correlation

---

## 12. Data Caching

### Decision
No automatic caching; rely on data provider caching.

### Rationale
- **Simplicity**: Caching adds complexity
- **Provider Responsibility**: Data providers can cache if needed
- **Memory**: Avoid duplicating large datasets

### Trade-offs
- **Performance**: Repeated runs may re-fetch data
- **Network**: More API calls without caching
- **Consistency**: Different runs might get different data

### Recommended Pattern
```python
# Provider-level caching
class YFinanceProvider:
    def __init__(self):
        self.cache = {}
    
    def get_historical_data(self, symbol, start, end):
        cache_key = (symbol, start, end)
        if cache_key in self.cache:
            return self.cache[cache_key]
        
        data = self._fetch_data(symbol, start, end)
        self.cache[cache_key] = data
        return data
```

---

## 13. Testing Strategy

### Decision
Comprehensive unit tests + integration tests with mock data.

### Rationale
- **Reliability**: Tests catch regressions
- **Documentation**: Tests show usage patterns
- **Confidence**: Refactoring is safer
- **Speed**: Mock data = fast tests

### Test Structure
```
tests/test_backtest/
    test_strategy.py      # Strategy interface tests
    test_orders.py        # Order/Fill/Position tests
    test_engine.py        # Engine unit tests
    test_integration.py   # End-to-end tests
```

### Testing Approach
1. **Unit Tests**: Test each class independently with mocks
2. **Integration Tests**: Test full backtest with MockDataProvider
3. **Smoke Tests**: Run simple strategy with real data (slow)

### Mock Data Provider
```python
class MockDataProvider:
    def get_historical_data(self, symbol, start, end):
        # Return predictable test data
        dates = pd.date_range(start, end)
        return pd.DataFrame({
            'Close': range(100, 100 + len(dates)),
            'Open': range(100, 100 + len(dates)),
            'High': range(101, 101 + len(dates)),
            'Low': range(99, 99 + len(dates)),
            'Volume': [1000000] * len(dates)
        }, index=dates)
```

---

## 14. Configuration Management

### Decision
Pass configuration parameters directly to engine constructor.

### Rationale
- **Explicit**: Clear what's being configured
- **Type Safety**: IDE autocomplete works
- **Simplicity**: No config file parsing

### Trade-offs
- **Verbosity**: More code to create engine
- **Persistence**: Can't save/load configurations
- **Sharing**: Harder to share configurations

### Current Pattern
```python
engine = BacktestEngine(
    initial_capital=100000,
    data_provider=YFinanceProvider(),
    commission=0.001,
    slippage=0.0005
)
```

### Future Enhancement
```python
# Load from config file
config = BacktestConfig.from_yaml('config.yaml')
engine = BacktestEngine.from_config(config)

# Or use dataclass
config = BacktestConfig(
    initial_capital=100000,
    commission=0.001,
    slippage=0.0005
)
engine = BacktestEngine(config=config)
```

---

## 15. Logging Strategy

### Decision
Use Python logging module with configurable levels.

### Rationale
- **Standard**: Python standard library
- **Flexible**: Configure verbosity per module
- **Integration**: Works with other logging systems

### Logging Levels
- **DEBUG**: Detailed execution flow, individual orders
- **INFO**: High-level events (start backtest, add strategy)
- **WARNING**: Recoverable issues (insufficient capital)
- **ERROR**: Unrecoverable errors in strategy code

### Usage
```python
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)

# Run backtest
engine = BacktestEngine(...)
result = engine.run(...)  # Logs: "Starting backtest..."
```

---

## Conclusion

These design decisions prioritize:
1. **Simplicity**: Start simple, add complexity when needed
2. **Realism**: Simulate real trading conditions
3. **Extensibility**: Easy to customize and extend
4. **Testability**: Comprehensive testing support
5. **Type Safety**: Leverage Python's type system

The architecture supports the 80/20 rule: cover 80% of use cases with 20% of the complexity, while remaining extensible for advanced needs.

---

## Review and Updates

This document should be updated when:
- Major architectural changes are made
- New features significantly impact design
- Alternative approaches are implemented
- Performance characteristics change

**Last Updated**: 2026-02-17
**Next Review**: When adding advanced features (risk management, advanced orders, etc.)
