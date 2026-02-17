# Backtesting Engine Architecture

## Overview

The Copilot Quant backtesting engine is designed with a modular, event-driven architecture that simulates realistic trading conditions. This document describes the core abstractions, their interactions, and the design principles that guide the implementation.

## Design Principles

1. **Event-Driven**: Processes market data chronologically to avoid look-ahead bias
2. **Realistic Simulation**: Includes transaction costs, slippage, and position tracking
3. **Extensibility**: Abstract interfaces allow custom strategies, data sources, and brokers
4. **Simplicity**: Clear separation of concerns with minimal coupling
5. **Testability**: Each component can be tested in isolation

## System Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                       Backtesting Engine                            │
│                                                                     │
│  ┌──────────────┐      ┌──────────────┐      ┌──────────────┐    │
│  │   Strategy   │      │   DataFeed   │      │    Broker    │    │
│  │  Interface   │      │  Connector   │      │  Execution   │    │
│  └──────┬───────┘      └──────┬───────┘      └──────┬───────┘    │
│         │                     │                     │             │
│         │                     │                     │             │
│         └──────────┬──────────┴──────────┬──────────┘             │
│                    │                     │                        │
│              ┌─────▼─────────────────────▼─────┐                  │
│              │     Backtest Engine Core        │                  │
│              │  (Event Loop & Orchestration)   │                  │
│              └─────┬─────────────────────┬─────┘                  │
│                    │                     │                        │
│         ┌──────────▼──────────┐   ┌──────▼──────────┐            │
│         │    Portfolio         │   │     Results     │            │
│         │    Manager           │   │   Tracker       │            │
│         └──────────────────────┘   └─────────────────┘            │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

## Core Components

### 1. Strategy Interface

The Strategy interface defines how trading logic plugs into the backtesting engine.

**Purpose**: Encapsulate trading logic and signal generation

**Key Methods**:
- `initialize()`: Setup indicators and state
- `on_data(timestamp, data)`: Process new market data and generate orders
- `on_fill(fill)`: Handle order execution notifications
- `finalize()`: Cleanup and final calculations

**Design Pattern**: Template Method Pattern

```python
class Strategy(ABC):
    """
    Abstract base class for all trading strategies.
    
    The engine calls lifecycle methods in this order:
    1. initialize() - once at start
    2. on_data() - for each market data point
    3. on_fill() - when orders execute
    4. finalize() - once at end
    """
    
    @abstractmethod
    def on_data(self, timestamp: datetime, data: pd.DataFrame) -> List[Order]:
        """Generate trading signals based on market data."""
        pass
```

**Implementation Notes**:
- Strategies are stateful and maintain their own indicators/variables
- Must avoid look-ahead bias by only using historical data
- Return orders to execute, not direct portfolio modifications
- Can track their own performance metrics via on_fill()

### 2. DataFeed Connector

The DataFeed abstraction provides market data to the backtesting engine.

**Purpose**: Standardize access to historical and real-time market data

**Key Methods**:
- `get_historical_data(symbol, start, end)`: Fetch historical OHLCV data
- `get_multiple_symbols(symbols, start, end)`: Batch fetch for efficiency
- `get_ticker_info(symbol)`: Metadata about securities

**Design Pattern**: Strategy Pattern (for different data sources)

```python
class DataProvider(ABC):
    """
    Abstract interface for market data sources.
    
    Implementations can connect to:
    - Yahoo Finance (YFinanceProvider)
    - Alpha Vantage
    - Polygon.io
    - CSV files
    - Databases
    """
    
    @abstractmethod
    def get_historical_data(
        self, 
        symbol: str,
        start_date: Optional[datetime],
        end_date: Optional[datetime],
        interval: str = '1d'
    ) -> pd.DataFrame:
        """Return OHLCV data in standardized format."""
        pass
```

**Data Format**:
```
DataFrame with DatetimeIndex:
- Open: float
- High: float
- Low: float
- Close: float
- Volume: int
- (Optional) Dividends, Stock Splits
```

**Implementation Notes**:
- Data is always sorted chronologically
- Missing data should be handled gracefully
- Supports multiple timeframes (daily, hourly, etc.)
- Can be mocked for testing

### 3. Broker/Execution Engine

The Broker handles order execution, position tracking, and portfolio accounting.

**Purpose**: Simulate realistic order execution with costs and slippage

**Key Responsibilities**:
1. **Order Execution**: Convert orders to fills with realistic pricing
2. **Position Tracking**: Maintain current holdings and P&L
3. **Cash Management**: Track available capital and margin
4. **Transaction Costs**: Apply commissions and slippage

**Design Pattern**: Facade Pattern (simplifies complex execution logic)

```python
class Broker:
    """
    Simulates a brokerage for order execution and position management.
    
    Handles:
    - Market and limit order execution
    - Position tracking (long/short)
    - Cash management
    - Commission and slippage
    - Buying power checks
    """
    
    def execute_order(
        self, 
        order: Order, 
        current_price: float,
        timestamp: datetime
    ) -> Optional[Fill]:
        """
        Execute order if conditions are met.
        
        Returns Fill if executed, None if rejected/unfilled.
        """
        pass
```

**Order Types Supported**:
- **Market Orders**: Execute immediately at next available price + slippage
- **Limit Orders**: Execute only if price reaches limit price
- (Future) Stop orders, trailing stops, etc.

**Transaction Costs**:
```python
# Commission (percentage of trade value)
commission = fill_price * quantity * commission_rate

# Slippage (simulates market impact)
if order.side == 'buy':
    fill_price = market_price * (1 + slippage_rate)
else:  # sell
    fill_price = market_price * (1 - slippage_rate)
```

### 4. Portfolio Manager

The Portfolio tracks positions, calculates P&L, and maintains portfolio history.

**Purpose**: Centralized portfolio state management

**Key Responsibilities**:
1. Track positions across all symbols
2. Calculate unrealized and realized P&L
3. Maintain portfolio value history
4. Compute performance metrics

**Design Pattern**: Repository Pattern

```python
class Portfolio:
    """
    Manages all positions and portfolio-level accounting.
    
    Tracks:
    - Cash balance
    - Positions (symbol -> Position object)
    - Portfolio value over time
    - Performance metrics
    """
    
    positions: Dict[str, Position]
    cash: float
    portfolio_history: List[PortfolioSnapshot]
    
    def get_position(self, symbol: str) -> Optional[Position]:
        """Get current position for a symbol."""
        pass
    
    def get_portfolio_value(self, current_prices: Dict[str, float]) -> float:
        """Calculate total portfolio value."""
        pass
    
    def update_from_fill(self, fill: Fill, current_price: float) -> None:
        """Update positions and cash from order fill."""
        pass
```

**Position Tracking**:
```python
@dataclass
class Position:
    symbol: str
    quantity: float  # positive = long, negative = short
    avg_entry_price: float
    unrealized_pnl: float
    realized_pnl: float
    
    def update_from_fill(self, fill: Fill) -> None:
        """Update position based on fill."""
        # Handle increasing/decreasing positions
        # Calculate realized P&L on closes
        # Update average entry price
        pass
```

### 5. Results Tracking & Reporting

Results tracking captures backtest outcomes for analysis and visualization.

**Purpose**: Store and analyze backtest results

**Key Components**:

```python
@dataclass
class BacktestResult:
    """
    Complete record of a backtest run.
    
    Contains:
    - Configuration (strategy, dates, capital)
    - Performance metrics (return, Sharpe, drawdown)
    - Trade log (all fills)
    - Portfolio history (equity curve)
    """
    
    strategy_name: str
    start_date: datetime
    end_date: datetime
    initial_capital: float
    final_capital: float
    total_return: float
    trades: List[Fill]
    portfolio_history: pd.DataFrame
    
    def get_trade_log(self) -> pd.DataFrame:
        """Return formatted trade history."""
        pass
    
    def get_equity_curve(self) -> pd.Series:
        """Return portfolio value over time."""
        pass
    
    def get_summary_stats(self) -> dict:
        """Calculate performance metrics."""
        pass
```

**Performance Metrics**:
- Total Return (%)
- Sharpe Ratio
- Maximum Drawdown
- Win Rate
- Average Win/Loss
- Profit Factor
- Number of Trades

## Event Flow Diagram

```
┌──────────────────────────────────────────────────────────────────┐
│                    Backtest Event Loop                           │
└──────────────────────────────────────────────────────────────────┘

1. Initialize
   ├─→ Strategy.initialize()
   ├─→ Load historical data from DataFeed
   └─→ Setup Portfolio (cash, positions)

2. For each timestamp in data:
   │
   ├─→ Get current market data
   │   └─→ DataFeed provides data up to timestamp
   │
   ├─→ Update portfolio with current prices
   │   ├─→ Mark-to-market all positions
   │   └─→ Calculate unrealized P&L
   │
   ├─→ Record portfolio state
   │   └─→ Save snapshot to history
   │
   ├─→ Generate trading signals
   │   └─→ Strategy.on_data(timestamp, data) → [Order, ...]
   │
   ├─→ Execute orders
   │   ├─→ For each order:
   │   │   ├─→ Broker.execute_order() → Fill
   │   │   ├─→ Check buying power
   │   │   ├─→ Apply slippage and commission
   │   │   ├─→ Update Portfolio
   │   │   └─→ Strategy.on_fill(fill)
   │   └─→ Continue
   │
   └─→ Next timestamp

3. Finalize
   ├─→ Strategy.finalize()
   ├─→ Calculate final metrics
   └─→ Return BacktestResult
```

## Component Interactions

### Order Placement Flow

```
Strategy                 Engine                  Broker                Portfolio
   |                       |                       |                       |
   |  on_data()            |                       |                       |
   |──────────────────────>|                       |                       |
   |  returns [Order]      |                       |                       |
   |<──────────────────────|                       |                       |
   |                       |  execute_order()      |                       |
   |                       |──────────────────────>|                       |
   |                       |                       |  check_buying_power() |
   |                       |                       |──────────────────────>|
   |                       |                       |  OK                   |
   |                       |                       |<──────────────────────|
   |                       |  Fill                 |                       |
   |                       |<──────────────────────|                       |
   |                       |                       |  update_position()    |
   |                       |                       |──────────────────────>|
   |                       |                       |                       |
   |  on_fill(fill)        |                       |                       |
   |<──────────────────────|                       |                       |
   |                       |                       |                       |
```

### Data Flow

```
DataFeed → Backtest Engine → Strategy
                ↓
            Portfolio ← Broker
                ↓
           Results Tracker
```

## Design Patterns Used

1. **Strategy Pattern**: Different trading strategies, data providers
2. **Template Method**: Strategy lifecycle hooks
3. **Observer Pattern**: Strategy callbacks (on_fill)
4. **Facade Pattern**: Broker simplifies execution complexity
5. **Repository Pattern**: Portfolio manages position state
6. **Factory Pattern**: Creating strategies, data providers

## Extension Points

### Adding a New Strategy

```python
class MyStrategy(Strategy):
    def __init__(self, param1, param2):
        super().__init__()
        self.param1 = param1
        self.param2 = param2
    
    def initialize(self):
        # Setup indicators, load config
        self.sma_short = None
        self.sma_long = None
    
    def on_data(self, timestamp, data):
        # Your trading logic here
        orders = []
        # ... generate signals ...
        return orders
```

### Adding a New Data Provider

```python
class CustomDataProvider(DataProvider):
    def get_historical_data(self, symbol, start_date, end_date, interval='1d'):
        # Connect to your data source
        # Return standardized DataFrame
        return pd.DataFrame(...)
```

### Adding a New Order Type

```python
@dataclass
class StopOrder(Order):
    stop_price: float
    
    def should_trigger(self, current_price: float) -> bool:
        # Custom trigger logic
        pass
```

## Configuration

Backtest configuration is centralized in engine initialization:

```python
engine = BacktestEngine(
    initial_capital=100000,      # Starting cash
    data_provider=provider,      # Data source
    commission=0.001,            # 0.1% commission
    slippage=0.0005,            # 0.05% slippage
    # Future extensions:
    # margin_rate=0.5,
    # short_cost=0.001,
    # max_leverage=2.0,
)
```

## Error Handling

The engine handles errors at multiple levels:

1. **Data Errors**: Missing data, invalid symbols
   - Log warning and skip timestamp
   - Continue backtest with available data

2. **Strategy Errors**: Exceptions in on_data()
   - Catch exception, log error
   - Continue to next timestamp
   - Don't crash entire backtest

3. **Execution Errors**: Insufficient capital, invalid orders
   - Reject order, log warning
   - Notify strategy via logging
   - Continue execution

4. **System Errors**: Critical failures
   - Gracefully terminate
   - Save partial results
   - Provide diagnostic information

## Performance Considerations

### Optimization Strategies

1. **Vectorization**: Use pandas operations for indicator calculations
2. **Data Caching**: Cache repeated data lookups
3. **Selective Updates**: Only update changed positions
4. **Efficient Indexing**: Use datetime indexes for fast lookups
5. **Memory Management**: Clear unnecessary history data

### Scalability Limits

Current design supports:
- ✅ Thousands of data points (years of daily data)
- ✅ Dozens of symbols simultaneously
- ✅ Hundreds of trades per backtest
- ⚠️ Not optimized for tick-level data
- ⚠️ Not optimized for thousands of symbols

## Testing Strategy

### Unit Tests

Each component is tested in isolation:

- **Strategy Tests**: Mock engine, verify order generation
- **Broker Tests**: Mock prices, verify execution logic
- **Portfolio Tests**: Verify P&L calculations
- **DataFeed Tests**: Verify data format standardization

### Integration Tests

Test components working together:

- Simple buy-and-hold strategy
- Moving average crossover
- Multiple symbols
- Edge cases (gaps, splits, etc.)

### Mock Objects

```python
class MockDataProvider(DataProvider):
    """Provides deterministic test data."""
    
    def get_historical_data(self, symbol, start_date, end_date, interval='1d'):
        # Return controlled, predictable data
        return create_test_data(trend='up', volatility=0.01)
```

## Future Enhancements

### Planned Features

1. **Advanced Order Types**
   - Stop-loss orders
   - Trailing stops
   - OCO (One-Cancels-Other)
   - Bracket orders

2. **Risk Management**
   - Position size limits
   - Portfolio heat maps
   - Risk-adjusted metrics
   - VaR calculations

3. **Performance Analytics**
   - Sharpe ratio
   - Sortino ratio
   - Maximum drawdown
   - Rolling metrics

4. **Portfolio Optimization**
   - Multi-strategy allocation
   - Kelly criterion
   - Mean-variance optimization

5. **Advanced Simulation**
   - Partial fills
   - Market impact modeling
   - More realistic slippage
   - Borrowing costs for shorts

### Not Planned (Out of Scope)

- Real-time trading execution
- Complex derivatives pricing
- High-frequency tick data
- Machine learning integration

## Conclusion

The backtesting engine architecture is designed to be:

- **Simple**: Easy to understand and use
- **Flexible**: Extensible through abstract interfaces
- **Realistic**: Accurate simulation of trading costs
- **Testable**: Each component can be tested independently
- **Maintainable**: Clear separation of concerns

The modular design allows each component to evolve independently while maintaining backward compatibility.
