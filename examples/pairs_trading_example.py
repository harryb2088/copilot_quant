#!/usr/bin/env python
"""
Example: Pairs Trading Strategy Backtest

This example demonstrates how to:
1. Use the PairsTradingStrategy to identify cointegrated pairs
2. Execute mean-reversion trades based on spread Z-scores
3. Backtest across multiple assets
4. Analyze performance metrics

The strategy automatically:
- Identifies cointegrated pairs from the asset universe
- Calculates hedge ratios using regression
- Computes spread Z-scores for entry/exit signals
- Tracks performance metrics (PnL, Sharpe ratio, max drawdown)

Run with: python examples/pairs_trading_example.py
"""

from datetime import datetime

from copilot_quant.backtest import BacktestEngine
from copilot_quant.data.providers import YFinanceProvider
from copilot_quant.strategies import PairsTradingStrategy


def main():
    """Run pairs trading strategy backtest."""
    print("=" * 80)
    print("Pairs Trading Strategy Backtest")
    print("=" * 80)
    
    # Define asset universe for pairs trading
    # These should be related assets (e.g., same sector, correlated markets)
    asset_universe = [
        'SPY',   # S&P 500 ETF
        'QQQ',   # Nasdaq 100 ETF
        'IWM',   # Russell 2000 ETF
        'DIA',   # Dow Jones ETF
        'XLF',   # Financial sector ETF
        'XLK',   # Technology sector ETF
        'XLE',   # Energy sector ETF
        'XLV',   # Healthcare sector ETF
    ]
    
    print(f"\nAsset Universe ({len(asset_universe)} symbols):")
    for symbol in asset_universe:
        print(f"  - {symbol}")
    
    # Configure the pairs trading strategy
    strategy = PairsTradingStrategy(
        lookback=60,              # 60-day window for statistics
        entry_zscore=2.0,         # Enter when spread is 2 std devs from mean
        exit_zscore=0.5,          # Exit when spread reverts to 0.5 std devs
        quantity=100,             # Trade 100 shares per position
        max_pairs=3,              # Trade up to 3 pairs simultaneously
        min_correlation=0.7,      # Require 0.7 correlation minimum
        cointegration_pvalue=0.05,  # 5% significance for cointegration
        rebalance_frequency=20    # Re-evaluate pairs every 20 days
    )
    
    # Set up backtesting engine
    engine = BacktestEngine(
        initial_capital=100000,
        data_provider=YFinanceProvider(),
        commission=0.001,  # 0.1% commission
        slippage=0.0005    # 0.05% slippage
    )
    
    engine.add_strategy(strategy)
    
    # Run backtest
    print("\n" + "=" * 80)
    print("Running Backtest...")
    print("=" * 80)
    
    start_date = datetime(2020, 1, 1)
    end_date = datetime(2023, 12, 31)
    
    result = engine.run(
        start_date=start_date,
        end_date=end_date,
        symbols=asset_universe
    )
    
    # Display results
    print("\n" + "=" * 80)
    print("Backtest Results")
    print("=" * 80)
    
    metrics = result.metrics
    
    print("\n📊 Performance Metrics:")
    print(f"  Initial Capital:    ${metrics['initial_capital']:,.2f}")
    print(f"  Final Capital:      ${metrics['final_capital']:,.2f}")
    print(f"  Total Return:       {metrics['total_return_pct']:.2f}%")
    print(f"  Annualized Return:  {metrics['annualized_return_pct']:.2f}%")
    
    print("\n📈 Risk Metrics:")
    print(f"  Sharpe Ratio:       {metrics['sharpe_ratio']:.3f}")
    print(f"  Sortino Ratio:      {metrics['sortino_ratio']:.3f}")
    print(f"  Max Drawdown:       {metrics['max_drawdown_pct']:.2f}%")
    print(f"  Volatility:         {metrics['volatility_pct']:.2f}%")
    
    print("\n💰 Trade Statistics:")
    print(f"  Total Trades:       {metrics['total_trades']}")
    print(f"  Win Rate:           {metrics['win_rate_pct']:.2f}%")
    print(f"  Profit Factor:      {metrics['profit_factor']:.2f}")
    print(f"  Avg Win:            ${metrics['avg_win']:.2f}")
    print(f"  Avg Loss:           ${metrics['avg_loss']:.2f}")
    
    print("\n⏱️  Time Metrics:")
    print(f"  Trading Days:       {metrics['trading_days']}")
    print(f"  Start Date:         {start_date.date()}")
    print(f"  End Date:           {end_date.date()}")
    
    # Display equity curve information
    print("\n📉 Equity Curve:")
    equity = result.equity_curve
    print(f"  Data Points:        {len(equity)}")
    print(f"  Peak Value:         ${equity.max():,.2f}")
    print(f"  Lowest Value:       ${equity.min():,.2f}")
    
    # Display trade history sample
    if result.trades:
        print("\n📝 Recent Trades (last 10):")
        for fill in result.trades[-10:]:
            print(f"  [{fill.timestamp.date()}] {fill.order.side.upper():5} "
                  f"{fill.fill_quantity:3} {fill.order.symbol:6} @ ${fill.fill_price:7.2f} "
                  f"(commission: ${fill.commission:.2f})")
    
    # Visualization (optional - requires matplotlib)
    try:
        import matplotlib.pyplot as plt
        
        print("\n📊 Generating charts...")
        
        fig, axes = plt.subplots(2, 1, figsize=(12, 8))
        
        # Equity curve
        axes[0].plot(equity.index, equity.values, linewidth=2)
        axes[0].set_title('Equity Curve', fontsize=14, fontweight='bold')
        axes[0].set_xlabel('Date')
        axes[0].set_ylabel('Portfolio Value ($)')
        axes[0].grid(True, alpha=0.3)
        axes[0].axhline(y=metrics['initial_capital'], color='r', 
                       linestyle='--', label='Initial Capital', alpha=0.5)
        axes[0].legend()
        
        # Drawdown
        cummax = equity.expanding().max()
        drawdown = (equity - cummax) / cummax * 100
        axes[1].fill_between(drawdown.index, drawdown.values, 0, 
                            alpha=0.3, color='red')
        axes[1].set_title('Drawdown', fontsize=14, fontweight='bold')
        axes[1].set_xlabel('Date')
        axes[1].set_ylabel('Drawdown (%)')
        axes[1].grid(True, alpha=0.3)
        
        plt.tight_layout()
        plt.savefig('/tmp/pairs_trading_backtest.png', dpi=150, bbox_inches='tight')
        print("  Chart saved to: /tmp/pairs_trading_backtest.png")
        
    except ImportError:
        print("\n(Install matplotlib for visualization: pip install matplotlib)")
    
    print("\n" + "=" * 80)
    print("Backtest Complete!")
    print("=" * 80)
    
    return result


if __name__ == "__main__":
    result = main()
