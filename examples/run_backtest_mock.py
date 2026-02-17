#!/usr/bin/env python
"""
Example: Running a backtest with mock data (no network required).

This example demonstrates the backtesting engine using mock data,
so it can run without network access.

Run with: python examples/run_backtest_mock.py
"""

import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from datetime import datetime

import numpy as np
import pandas as pd

from copilot_quant.backtest import BacktestEngine, Order, Strategy
from copilot_quant.data.providers import DataProvider


class MockDataProvider(DataProvider):
    """Mock data provider with simulated SPY-like data."""
    
    def get_historical_data(self, symbol, start_date=None, end_date=None, interval='1d'):
        """Generate realistic mock data."""
        np.random.seed(42)
        
        # Generate ~4 years of daily data
        dates = pd.date_range('2020-01-01', '2023-12-31', freq='D')
        
        # Simulate price with upward trend and volatility
        base_price = 300.0
        drift = 0.0003  # ~11% annual drift
        volatility = 0.01  # ~16% annual volatility
        
        returns = np.random.normal(drift, volatility, len(dates))
        prices = base_price * (1 + returns).cumprod()
        
        return pd.DataFrame({
            'Open': prices * 0.999,
            'High': prices * 1.01,
            'Low': prices * 0.99,
            'Close': prices,
            'Volume': np.random.randint(50000000, 150000000, len(dates)),
        }, index=dates)
    
    def get_multiple_symbols(self, symbols, start_date=None, end_date=None, interval='1d'):
        """Get data for multiple symbols."""
        return self.get_historical_data(symbols[0], start_date, end_date, interval)
    
    def get_ticker_info(self, symbol):
        """Return mock ticker info."""
        return {'longName': 'SPDR S&P 500 ETF Trust'}


class BuyAndHold(Strategy):
    """Simple buy-and-hold strategy."""
    
    def __init__(self, symbol='SPY', quantity=100):
        super().__init__()
        self.symbol = symbol
        self.quantity = quantity
        self.invested = False
    
    def initialize(self):
        """Called before backtest starts."""
        print(f"\nInitializing {self.name} strategy")
        print(f"  Symbol: {self.symbol}")
        print(f"  Quantity: {self.quantity}")
    
    def on_data(self, timestamp, data):
        """Buy once on the first data point."""
        if not self.invested:
            self.invested = True
            current_price = data['Close'].iloc[-1]
            print(f"\n[{timestamp.date()}] Placing buy order for {self.quantity} shares")
            print(f"  Current price: ${current_price:.2f}")
            return [Order(
                symbol=self.symbol,
                quantity=self.quantity,
                order_type='market',
                side='buy'
            )]
        return []
    
    def on_fill(self, fill):
        """Called when an order is filled."""
        print(f"\n[{fill.timestamp.date()}] ✓ Order filled:")
        print(f"  {fill.order.side.upper()} {fill.fill_quantity} {fill.order.symbol} @ ${fill.fill_price:.2f}")
        print(f"  Commission: ${fill.commission:.2f}")
        print(f"  Total cost: ${fill.total_cost:.2f}")
    
    def finalize(self):
        """Called after backtest ends."""
        print(f"\nFinalizing {self.name} strategy")


def main():
    """Run the backtest example."""
    print("=" * 80)
    print("Backtesting Example: Buy-and-Hold Strategy (Mock Data)")
    print("=" * 80)
    
    # Configuration
    INITIAL_CAPITAL = 100000
    START_DATE = datetime(2020, 1, 1)
    END_DATE = datetime(2023, 12, 31)
    SYMBOLS = ['SPY']
    COMMISSION = 0.001  # 0.1%
    SLIPPAGE = 0.0005   # 0.05%
    
    print(f"\n📊 Backtest Configuration:")
    print(f"  Initial Capital: ${INITIAL_CAPITAL:,.2f}")
    print(f"  Period: {START_DATE.date()} to {END_DATE.date()}")
    print(f"  Symbols: {', '.join(SYMBOLS)}")
    print(f"  Commission: {COMMISSION:.3%}")
    print(f"  Slippage: {SLIPPAGE:.3%}")
    
    # Create data provider
    print("\n📈 Initializing mock data provider...")
    data_provider = MockDataProvider()
    
    # Create backtesting engine
    print("🔧 Initializing backtesting engine...")
    engine = BacktestEngine(
        initial_capital=INITIAL_CAPITAL,
        data_provider=data_provider,
        commission=COMMISSION,
        slippage=SLIPPAGE
    )
    
    # Create and add strategy
    strategy = BuyAndHold(symbol='SPY', quantity=250)
    engine.add_strategy(strategy)
    
    # Run backtest
    print("\n" + "=" * 80)
    print("🚀 Running backtest...")
    print("=" * 80)
    
    result = engine.run(
        start_date=START_DATE,
        end_date=END_DATE,
        symbols=SYMBOLS
    )
    
    # Display results
    print("\n" + "=" * 80)
    print("📊 Backtest Results")
    print("=" * 80)
    
    profit_loss = result.final_capital - result.initial_capital
    print(f"\n💰 Performance Summary:")
    print(f"  Strategy: {result.strategy_name}")
    print(f"  Initial Capital: ${result.initial_capital:,.2f}")
    print(f"  Final Capital: ${result.final_capital:,.2f}")
    print(f"  Total Return: {result.total_return:.2%}")
    print(f"  Profit/Loss: ${profit_loss:,.2f}")
    
    # Get summary stats
    stats = result.get_summary_stats()
    print(f"\n📈 Trading Statistics:")
    print(f"  Total Trades: {stats['total_trades']}")
    print(f"  Duration: {stats['duration_days']} days ({stats['duration_days']/365:.1f} years)")
    
    if stats['total_trades'] > 0:
        print(f"  Buy Trades: {stats.get('buy_trades', 0)}")
        print(f"  Sell Trades: {stats.get('sell_trades', 0)}")
        print(f"  Total Commission: ${stats.get('total_commission', 0):.2f}")
    
    # Display trade log
    if len(result.trades) > 0:
        print("\n📋 Trade Log:")
        trade_log = result.get_trade_log()
        for idx, row in trade_log.iterrows():
            print(f"  {idx.date()}: {row['side'].upper()} {row['quantity']} @ ${row['price']:.2f} "
                  f"(commission: ${row['commission']:.2f})")
    
    # Display equity curve summary
    print("\n📈 Portfolio Value Over Time:")
    equity = result.get_equity_curve()
    if len(equity) > 0:
        print(f"  Starting Value: ${equity.iloc[0]:,.2f}")
        print(f"  Peak Value: ${equity.max():,.2f}")
        print(f"  Final Value: ${equity.iloc[-1]:,.2f}")
        print(f"  Max Drawdown: {((equity - equity.cummax()) / equity.cummax()).min():.2%}")
    
    print("\n" + "=" * 80)
    print("✅ Backtest Complete!")
    print("=" * 80)
    
    # Display portfolio history sample
    if not result.portfolio_history.empty:
        print("\n📊 Portfolio History Sample (first 5 days):")
        print(result.portfolio_history.head().to_string())


if __name__ == "__main__":
    main()
