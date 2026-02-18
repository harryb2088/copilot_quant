# Issue: Real-time and Historical Market Data Ingestion

**Epic**: Live Trading & Interactive Brokers (IBKR) Integration  
**Priority**: High  
**Status**: Not Started  
**Created**: 2026-02-18

## Overview
Implement comprehensive market data ingestion from Interactive Brokers, including real-time streaming data, historical data retrieval, and market data subscription management.

## Requirements

### 1. Real-time Market Data
- [ ] Live price streaming (bid, ask, last)
- [ ] Real-time order book (Level II data)
- [ ] Live volume and trade data
- [ ] Market depth information
- [ ] Ticker plant for multiple symbols
- [ ] Data feed subscription management

### 2. Historical Data Retrieval
- [ ] Historical bars (1min, 5min, 15min, 1hour, 1day)
- [ ] Historical tick data
- [ ] Fundamental data retrieval
- [ ] Contract details and specifications
- [ ] Rate limit handling for historical requests
- [ ] Data caching and storage

### 3. Market Data Subscriptions
- [ ] Subscribe/unsubscribe to real-time data
- [ ] Market data snapshot requests
- [ ] Subscription limit management
- [ ] Cost tracking for market data
- [ ] Delayed vs real-time data handling
- [ ] Subscription persistence across reconnects

### 4. Data Normalization
- [ ] Convert IB data format to platform standard
- [ ] Handle timezone conversions
- [ ] Normalize contract specifications
- [ ] Handle corporate actions (splits, dividends)
- [ ] Data quality validation
- [ ] Missing data interpolation

### 5. Integration with Existing Data Pipeline
- [ ] Integrate with existing data loader
- [ ] Merge with EOD data pipeline
- [ ] Database storage integration
- [ ] Data backup and recovery
- [ ] Historical backfill coordination

## Implementation Tasks

### Real-time Data Manager
```python
class IBKRRealTimeDataManager:
    """
    Manages real-time market data subscriptions and streaming
    """
    - subscribe(symbols: List[str]) -> None
    - unsubscribe(symbols: List[str]) -> None
    - get_quote(symbol: str) -> Quote
    - register_callback(symbol: str, callback: Callable)
    - start_streaming()
    - stop_streaming()
```

### Historical Data Manager
```python
class IBKRHistoricalDataManager:
    """
    Retrieves and manages historical market data
    """
    - get_historical_bars(symbol: str, duration: str, bar_size: str) -> pd.DataFrame
    - get_tick_data(symbol: str, start: datetime, end: datetime) -> pd.DataFrame
    - get_fundamental_data(symbol: str) -> Dict
    - request_with_rate_limit(request: DataRequest) -> Any
```

### Data Models
```python
@dataclass
class Quote:
    symbol: str
    timestamp: datetime
    bid: float
    ask: float
    last: float
    bid_size: int
    ask_size: int
    volume: int
    
@dataclass
class HistoricalBar:
    symbol: str
    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    volume: int
```

### Market Data Adapter
```python
class IBKRDataAdapter:
    """
    Adapts IB data format to Copilot Quant platform format
    """
    - normalize_quote(ib_quote) -> Quote
    - normalize_bars(ib_bars) -> pd.DataFrame
    - normalize_contract(ib_contract) -> Contract
```

## Acceptance Criteria
- [ ] Can subscribe to real-time data for multiple symbols
- [ ] Real-time data updates delivered with < 1 second latency
- [ ] Historical data retrieval respects rate limits
- [ ] Data normalized to platform standard format
- [ ] Subscription state persists across reconnections
- [ ] All data operations are logged
- [ ] Integration with existing data pipeline working
- [ ] Unit tests for all data operations
- [ ] Integration tests with mock IB API

## Testing Requirements
- [ ] Unit tests for data managers
- [ ] Unit tests for data normalization
- [ ] Integration tests with mock market data
- [ ] Performance tests for high-frequency data
- [ ] Tests for rate limit handling
- [ ] Tests for subscription management

## Market Data Subscription Considerations
- **Free Account**: 15-minute delayed data for US stocks
- **Paid Subscriptions**: Real-time data requires monthly fees
- **Rate Limits**: 
  - 100 market data requests per 10 seconds
  - 60 historical data requests per 10 minutes
- **Concurrent Subscriptions**: Limited by account type

## Related Files
- `copilot_quant/brokers/data_manager.py` - New module (to create)
- `copilot_quant/brokers/data_adapter.py` - New module (to create)
- `copilot_quant/data/` - Existing data modules
- `tests/test_brokers/test_data_manager.py` - Tests (to create)

## Dependencies
- ib_insync>=0.9.86
- pandas
- Issue #02 (Connection Management) - Required

## Notes
- Need to handle delayed vs real-time data based on subscription
- Implement rate limiting to avoid API bans
- Consider caching frequently requested data
- Need strategy for handling reconnections (re-subscribe to data feeds)
- Market data costs should be tracked and logged

## References
- [IB Market Data Documentation](https://interactivebrokers.github.io/tws-api/market_data.html)
- [ib_insync market data examples](https://ib-insync.readthedocs.io/recipes.html#market-data)
