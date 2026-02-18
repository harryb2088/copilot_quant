# Pairs Trading Strategy Documentation

## Overview

The Pairs Trading Strategy is a market-neutral statistical arbitrage strategy that identifies pairs of assets with stable historical relationships and trades on temporary deviations from their equilibrium. This implementation supports:

- **Automatic pair identification** using cointegration tests
- **Hedge ratio calculation** via regression analysis
- **Mean-reversion signals** based on Z-scores
- **Multi-pair trading** with configurable limits
- **Comprehensive performance tracking** (PnL, Sharpe ratio, drawdown)

## Strategy Concept

### What is Pairs Trading?

Pairs trading exploits the statistical relationship between two correlated assets. When the relationship temporarily breaks down (the "spread" deviates from its mean), the strategy:

1. **Goes long** the underperforming asset
2. **Goes short** the outperforming asset
3. **Profits** when the spread reverts to its mean

### Key Components

1. **Pair Selection**: Identifies cointegrated pairs using Engle-Granger test
2. **Hedge Ratio**: Determines optimal position sizes via linear regression
3. **Spread Calculation**: Computes the difference between paired assets
4. **Z-Score Signal**: Measures standard deviations from mean for entry/exit
5. **Mean Reversion**: Assumes spread will revert to historical average

## Installation

The pairs trading strategy requires additional statistical libraries:

```bash
pip install scipy statsmodels
```

These are used for:
- `scipy`: Statistical tests and regression analysis
- `statsmodels`: Engle-Granger cointegration test

## Quick Start

### Basic Example

```python
from datetime import datetime
from copilot_quant.backtest import BacktestEngine
from copilot_quant.data.providers import YFinanceProvider
from copilot_quant.strategies import PairsTradingStrategy

# Define asset universe (related assets work best)
asset_universe = ['SPY', 'QQQ', 'IWM', 'DIA']

# Create strategy
strategy = PairsTradingStrategy(
    lookback=60,          # 60-day window for statistics
    entry_zscore=2.0,     # Enter at 2 standard deviations
    exit_zscore=0.5,      # Exit at 0.5 standard deviations
    quantity=100,         # Trade 100 shares per position
    max_pairs=3           # Trade up to 3 pairs
)

# Set up and run backtest
engine = BacktestEngine(
    initial_capital=100000,
    data_provider=YFinanceProvider(),
    commission=0.001,
    slippage=0.0005
)

engine.add_strategy(strategy)

result = engine.run(
    start_date=datetime(2020, 1, 1),
    end_date=datetime(2023, 12, 31),
    symbols=asset_universe
)

# View results
print(f"Total Return: {result.metrics['total_return_pct']:.2f}%")
print(f"Sharpe Ratio: {result.metrics['sharpe_ratio']:.2f}")
print(f"Max Drawdown: {result.metrics['max_drawdown_pct']:.2f}%")
```

### Run the Example Script

```bash
python examples/pairs_trading_example.py
```

## Strategy Parameters

### `PairsTradingStrategy` Configuration

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `lookback` | int | 60 | Historical window for calculating statistics (days) |
| `entry_zscore` | float | 2.0 | Z-score threshold to enter trades (e.g., 2.0 = 2 std devs) |
| `exit_zscore` | float | 0.5 | Z-score threshold to exit trades |
| `quantity` | int | 100 | Number of shares to trade per asset |
| `max_pairs` | int | 5 | Maximum number of pairs to trade simultaneously |
| `min_correlation` | float | 0.6 | Minimum correlation for pair consideration |
| `cointegration_pvalue` | float | 0.05 | P-value threshold for cointegration test (5% significance) |
| `rebalance_frequency` | int | 20 | Days between pair re-evaluation |

### Parameter Guidelines

**Lookback Period (`lookback`)**:
- **Shorter (20-40 days)**: More responsive, higher turnover
- **Medium (60-90 days)**: Balanced approach
- **Longer (120+ days)**: More stable, lower turnover
- Recommended: 60 days for most markets

**Entry Z-Score (`entry_zscore`)**:
- **Conservative (2.5-3.0)**: Fewer trades, higher confidence
- **Moderate (1.5-2.0)**: Balanced trade frequency
- **Aggressive (1.0-1.5)**: More trades, lower confidence
- Recommended: 2.0 for beginners

**Exit Z-Score (`exit_zscore`)**:
- Should be less than entry Z-score
- **Tight (0.2-0.5)**: Quick exits, less profit capture
- **Loose (0.5-1.0)**: Wait for stronger reversion
- Recommended: 0.5 (captures most mean reversion)

**Max Pairs (`max_pairs`)**:
- Limits diversification and risk exposure
- **1-2 pairs**: Concentrated, higher risk
- **3-5 pairs**: Moderate diversification
- **6+ pairs**: High diversification, more capital needed
- Recommended: 3-5 pairs

## Statistical Utilities

The strategy includes comprehensive statistical utilities:

### Cointegration Testing

```python
from copilot_quant.strategies import check_cointegration

# Test if two series are cointegrated
is_coint, p_value, test_stat = check_cointegration(prices1, prices2)

if is_coint:
    print(f"Series are cointegrated (p-value: {p_value:.4f})")
```

### Correlation Analysis

```python
from copilot_quant.strategies import calculate_correlation

# Calculate Pearson correlation
corr = calculate_correlation(prices1, prices2, method='pearson')
print(f"Correlation: {corr:.3f}")
```

### Hedge Ratio Calculation

```python
from copilot_quant.strategies import calculate_hedge_ratio

# Calculate optimal hedge ratio via regression
ratio = calculate_hedge_ratio(prices1, prices2)
print(f"Hedge Ratio: {ratio:.2f}")
```

### Spread Calculation

```python
from copilot_quant.strategies import calculate_spread

# Calculate spread with automatic or manual hedge ratio
spread = calculate_spread(prices1, prices2)  # Auto hedge ratio
spread = calculate_spread(prices1, prices2, hedge_ratio=2.0)  # Manual
```

### Z-Score Calculation

```python
from copilot_quant.strategies import calculate_zscore

# Calculate rolling Z-score
zscore = calculate_zscore(spread, window=60)

# Current Z-score
current_z = zscore.iloc[-1]
if current_z > 2.0:
    print("Spread is 2 std devs above mean - potential short opportunity")
```

### Finding Cointegrated Pairs

```python
from copilot_quant.strategies import find_cointegrated_pairs
import pandas as pd

# DataFrame with price series for multiple assets
prices_df = pd.DataFrame({
    'AAPL': aapl_prices,
    'MSFT': msft_prices,
    'GOOGL': googl_prices
})

# Find all cointegrated pairs
pairs = find_cointegrated_pairs(
    prices_df,
    significance_level=0.05,
    min_correlation=0.7
)

for sym1, sym2, pval, corr in pairs:
    print(f"{sym1}-{sym2}: p={pval:.4f}, corr={corr:.3f}")
```

### Half-Life Calculation

```python
from copilot_quant.strategies import calculate_half_life

# Calculate mean-reversion speed
half_life = calculate_half_life(spread)
print(f"Expected mean-reversion time: {half_life:.1f} days")
```

## Asset Selection Guidelines

### Ideal Asset Pairs

1. **Same Sector**: Companies in the same industry
   - Example: JPM-BAC (banks), XOM-CVX (energy)

2. **Related ETFs**: Tracking similar indices
   - Example: SPY-IWM, QQQ-XLK

3. **Commodity Spreads**: Related commodities
   - Example: Gold-Silver, Crude-Brent

4. **International Pairs**: Same company, different exchanges
   - Example: BABA-9988.HK

### Asset Universe Examples

**Tech Sector ETFs**:
```python
tech_universe = ['QQQ', 'XLK', 'VGT', 'SOXX', 'SMH']
```

**Financial Stocks**:
```python
financial_universe = ['JPM', 'BAC', 'WFC', 'C', 'GS', 'MS']
```

**Market Indices**:
```python
index_universe = ['SPY', 'QQQ', 'IWM', 'DIA', 'MDY']
```

**Energy Sector**:
```python
energy_universe = ['XLE', 'XOP', 'OIH', 'XES', 'VDE']
```

## Strategy Workflow

### 1. Pair Identification Phase

On initialization and every `rebalance_frequency` days:

1. Collect historical prices for all symbols
2. Test all possible pairs for cointegration
3. Filter pairs by minimum correlation
4. Select top `max_pairs` by cointegration strength (lowest p-value)

### 2. Trading Phase

For each identified pair, on every bar:

1. Calculate hedge ratio using `lookback` period
2. Compute spread: `spread = price1 - hedge_ratio * price2`
3. Calculate Z-score of spread
4. Generate signals:
   - **Long spread** when Z-score < -`entry_zscore`
   - **Short spread** when Z-score > `entry_zscore`
   - **Close position** when abs(Z-score) < `exit_zscore`

### 3. Position Management

When entering a spread position:

**Long Spread** (Z-score very negative):
- Buy `quantity` shares of Asset 1
- Sell `quantity * hedge_ratio` shares of Asset 2

**Short Spread** (Z-score very positive):
- Sell `quantity` shares of Asset 1
- Buy `quantity * hedge_ratio` shares of Asset 2

## Performance Metrics

The strategy tracks all standard metrics:

### Return Metrics
- **Total Return**: Overall profit/loss percentage
- **Annualized Return**: Return adjusted for time period
- **CAGR**: Compound annual growth rate

### Risk Metrics
- **Sharpe Ratio**: Risk-adjusted return (higher is better)
- **Sortino Ratio**: Downside risk-adjusted return
- **Max Drawdown**: Largest peak-to-trough decline
- **Volatility**: Standard deviation of returns

### Trade Statistics
- **Total Trades**: Number of completed trades
- **Win Rate**: Percentage of profitable trades
- **Profit Factor**: Gross profit / Gross loss
- **Avg Win/Loss**: Average profit per winning/losing trade

## Advanced Usage

### Custom Pair Selection

```python
from copilot_quant.strategies.pairs_utils import check_cointegration

# Manually test specific pairs
prices_aapl = data[data['Symbol'] == 'AAPL']['Close']
prices_msft = data[data['Symbol'] == 'MSFT']['Close']

is_coint, pval, stat = check_cointegration(prices_aapl, prices_msft)

if is_coint:
    # Use these assets in the strategy
    asset_universe = ['AAPL', 'MSFT']
```

### Dynamic Hedge Ratios

The strategy recalculates hedge ratios on each trade using the most recent `lookback` period. This allows the strategy to adapt to changing market conditions.

### Risk Management

```python
# Conservative approach
strategy = PairsTradingStrategy(
    lookback=90,          # Longer lookback for stability
    entry_zscore=2.5,     # Higher threshold for quality
    exit_zscore=0.5,
    quantity=50,          # Smaller position size
    max_pairs=2           # Fewer concurrent positions
)

# Aggressive approach
strategy = PairsTradingStrategy(
    lookback=30,          # Shorter, more responsive
    entry_zscore=1.5,     # Lower threshold, more trades
    exit_zscore=0.3,
    quantity=200,         # Larger positions
    max_pairs=5           # More diversification
)
```

## Best Practices

### 1. Asset Selection
- Use assets from the same sector or market
- Ensure sufficient trading volume (liquidity)
- Verify historical correlation > 0.6
- Check for cointegration before deployment

### 2. Parameter Tuning
- Start with default parameters
- Backtest over multiple time periods
- Validate out-of-sample performance
- Adjust based on market regime

### 3. Risk Management
- Don't over-leverage positions
- Use stop-losses for risk control
- Monitor pair correlation regularly
- Be aware of structural breaks

### 4. Backtesting
- Use sufficient historical data (2+ years)
- Include transaction costs
- Test across different market conditions
- Avoid overfitting parameters

### 5. Monitoring
- Track pair correlation changes
- Monitor spread Z-scores
- Watch for changing market dynamics
- Re-evaluate pairs periodically

## Common Issues and Solutions

### Issue: No Pairs Identified

**Causes**:
- Correlation too low between assets
- Cointegration test fails
- Insufficient historical data

**Solutions**:
- Lower `min_correlation` parameter
- Increase `cointegration_pvalue` threshold
- Use related assets (same sector)
- Increase data history period

### Issue: Too Many Trades

**Causes**:
- `entry_zscore` too low
- `lookback` period too short

**Solutions**:
- Increase `entry_zscore` to 2.5 or 3.0
- Increase `lookback` to 90 or 120 days
- Tighten `min_correlation` requirement

### Issue: Low Win Rate

**Causes**:
- Pairs not truly cointegrated
- Market regime change
- Transaction costs too high

**Solutions**:
- Verify cointegration significance
- Re-evaluate pairs more frequently
- Reduce trading frequency
- Check spread half-life

## Examples

### Example 1: Sector ETF Pairs

```python
from copilot_quant.strategies import PairsTradingStrategy

# Trade sector ETF pairs
sector_etfs = ['XLF', 'XLK', 'XLE', 'XLV', 'XLI', 'XLU']

strategy = PairsTradingStrategy(
    lookback=60,
    entry_zscore=2.0,
    exit_zscore=0.5,
    quantity=100,
    max_pairs=3,
    min_correlation=0.7
)

# Run backtest...
```

### Example 2: Large Cap Tech Stocks

```python
# Trade pairs within FAANG stocks
tech_stocks = ['AAPL', 'MSFT', 'GOOGL', 'META', 'AMZN']

strategy = PairsTradingStrategy(
    lookback=90,          # Longer for stability
    entry_zscore=2.5,     # Higher quality trades
    exit_zscore=0.5,
    quantity=50,          # Smaller size for high-price stocks
    max_pairs=2,
    min_correlation=0.75  # Stricter correlation
)
```

### Example 3: International Index Pairs

```python
# Trade related international indices
indices = ['SPY', 'EWG', 'EWJ', 'EWU', 'FXI']

strategy = PairsTradingStrategy(
    lookback=120,         # Longer for macro trends
    entry_zscore=2.0,
    exit_zscore=0.5,
    quantity=100,
    max_pairs=3,
    rebalance_frequency=30  # Monthly rebalance
)
```

## References

### Academic Papers
- Gatev, E., Goetzmann, W. N., & Rouwenhorst, K. G. (2006). "Pairs trading: Performance of a relative-value arbitrage rule"

### Further Reading
- Engle-Granger cointegration test
- Ornstein-Uhlenbeck process for mean reversion
- Kalman filter for dynamic hedge ratios

## See Also

- [Backtesting Documentation](backtesting.md)
- [Strategy Development Guide](usage_guide.md)
- [Performance Metrics](architecture.md)
