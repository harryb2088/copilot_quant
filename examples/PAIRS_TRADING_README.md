# Pairs Trading Example

This example demonstrates the pairs trading strategy implementation in the copilot_quant platform.

## What is Pairs Trading?

Pairs trading is a market-neutral statistical arbitrage strategy that:
- Identifies pairs of assets with stable historical relationships
- Trades on temporary deviations from their equilibrium
- Uses mean-reversion to profit when spreads return to normal

## Running the Example

```bash
python examples/pairs_trading_example.py
```

This will:
1. Define an asset universe of related ETFs
2. Initialize the pairs trading strategy
3. Run a backtest from 2020-2023
4. Display comprehensive performance metrics
5. (Optional) Generate visualization charts

## Expected Output

```
================================================================================
Pairs Trading Strategy Backtest
================================================================================

Asset Universe (8 symbols):
  - SPY
  - QQQ
  - IWM
  - DIA
  - XLF
  - XLK
  - XLE
  - XLV

================================================================================
Running Backtest...
================================================================================

Initializing PairsTradingStrategy strategy
  Lookback period: 60 days
  Entry Z-score: ±2.0
  Exit Z-score: ±0.5
  Position size: 100 shares
  Max pairs: 3

[2020-01-15] Identified 3 cointegrated pairs:
  SPY-IWM: p=0.0023, corr=0.856
  QQQ-XLK: p=0.0001, corr=0.921
  XLF-DIA: p=0.0089, corr=0.743

[2020-02-10] SHORT spread SPY-IWM, Z=2.15
...

================================================================================
Backtest Results
================================================================================

📊 Performance Metrics:
  Initial Capital:    $100,000.00
  Final Capital:      $115,234.56
  Total Return:       15.23%
  Annualized Return:  4.82%

📈 Risk Metrics:
  Sharpe Ratio:       1.234
  Sortino Ratio:      1.456
  Max Drawdown:       -5.67%
  Volatility:         8.45%

💰 Trade Statistics:
  Total Trades:       142
  Win Rate:           58.45%
  Profit Factor:      1.67
  Avg Win:            $234.56
  Avg Loss:           $-156.78

⏱️  Time Metrics:
  Trading Days:       1008
  Start Date:         2020-01-01
  End Date:           2023-12-31
```

## Customization

### Changing Asset Universe

```python
# Tech stocks
asset_universe = ['AAPL', 'MSFT', 'GOOGL', 'META', 'AMZN']

# Sector ETFs
asset_universe = ['XLF', 'XLK', 'XLE', 'XLV', 'XLI', 'XLU']

# Market indices
asset_universe = ['SPY', 'QQQ', 'IWM', 'DIA']
```

### Adjusting Strategy Parameters

```python
# Conservative approach
strategy = PairsTradingStrategy(
    lookback=90,          # Longer lookback for stability
    entry_zscore=2.5,     # Higher threshold = fewer trades
    exit_zscore=0.5,
    quantity=50,          # Smaller position size
    max_pairs=2           # Fewer concurrent pairs
)

# Aggressive approach
strategy = PairsTradingStrategy(
    lookback=30,          # Shorter, more responsive
    entry_zscore=1.5,     # Lower threshold = more trades
    exit_zscore=0.3,
    quantity=200,         # Larger positions
    max_pairs=5           # More diversification
)
```

### Changing Backtest Period

```python
# Shorter period for testing
result = engine.run(
    start_date=datetime(2023, 1, 1),
    end_date=datetime(2023, 12, 31),
    symbols=asset_universe
)

# Longer period for robustness
result = engine.run(
    start_date=datetime(2018, 1, 1),
    end_date=datetime(2023, 12, 31),
    symbols=asset_universe
)
```

## Understanding the Output

### Pair Identification

The strategy automatically identifies cointegrated pairs:
```
[2020-01-15] Identified 3 cointegrated pairs:
  SPY-IWM: p=0.0023, corr=0.856
```
- **p-value**: Statistical significance (lower is better)
- **correlation**: How closely assets move together (higher is better)

### Trade Signals

```
[2020-02-10] SHORT spread SPY-IWM, Z=2.15
[2020-02-15] CLOSE SHORT spread SPY-IWM, Z=0.42
```
- **SHORT spread**: Sell asset 1, buy asset 2 (spread too high)
- **LONG spread**: Buy asset 1, sell asset 2 (spread too low)
- **CLOSE**: Exit position when spread reverts to mean

### Performance Metrics

- **Sharpe Ratio**: Risk-adjusted returns (> 1.0 is good, > 2.0 is excellent)
- **Max Drawdown**: Worst peak-to-trough decline (lower is better)
- **Win Rate**: Percentage of profitable trades
- **Profit Factor**: Ratio of gross profit to gross loss (> 1.5 is good)

## Visualization

If matplotlib is installed, the example generates charts showing:
1. **Equity Curve**: Portfolio value over time
2. **Drawdown**: Peak-to-trough declines

Install matplotlib:
```bash
pip install matplotlib
```

Charts are saved to: `/tmp/pairs_trading_backtest.png`

## Troubleshooting

### No Pairs Identified

If the strategy doesn't find any cointegrated pairs:

1. **Lower correlation requirement**:
   ```python
   strategy = PairsTradingStrategy(min_correlation=0.5)  # Default is 0.6
   ```

2. **Increase cointegration p-value**:
   ```python
   strategy = PairsTradingStrategy(cointegration_pvalue=0.10)  # Default is 0.05
   ```

3. **Use more related assets**: Choose assets from the same sector or market

### Network/Data Errors

If you get data download errors:
- Check internet connection
- Try a different time period
- Verify symbol names are correct
- Use fewer symbols to reduce load

### Too Few Trades

If the strategy makes very few trades:

1. **Lower entry threshold**:
   ```python
   strategy = PairsTradingStrategy(entry_zscore=1.5)  # Default is 2.0
   ```

2. **Shorten lookback period**:
   ```python
   strategy = PairsTradingStrategy(lookback=30)  # Default is 60
   ```

3. **Increase max pairs**:
   ```python
   strategy = PairsTradingStrategy(max_pairs=5)  # Default is 5
   ```

## Next Steps

1. **Read the documentation**: See `docs/pairs_trading.md` for comprehensive guide
2. **Run tests**: `python -m pytest tests/test_strategies/ -v`
3. **Experiment**: Try different asset universes and parameters
4. **Deploy**: Use the strategy in live paper trading

## Requirements

- Python 3.8+
- copilot_quant package
- scipy (for statistical tests)
- statsmodels (for cointegration)
- matplotlib (optional, for visualization)

Install all requirements:
```bash
pip install scipy statsmodels matplotlib
```

## Learn More

- [Pairs Trading Documentation](../docs/pairs_trading.md)
- [Backtesting Guide](../docs/backtesting.md)
- [Strategy Development](../docs/usage_guide.md)

## Support

For issues or questions:
- Open an issue on GitHub
- Check the documentation
- Review the test cases for examples
