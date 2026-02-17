#!/usr/bin/env python
"""
Example: Running a simple backtest with buy-and-hold strategy.

This example demonstrates how to:
1. Create a custom trading strategy
2. Set up the backtesting engine
3. Run a backtest on historical data
4. Analyze the results

Run with: python examples/run_backtest.py
"""

from datetime import datetime

from copilot_quant.backtest import BacktestEngine, Order, Strategy
from copilot_quant.data.providers import YFinanceProvider


class BuyAndHold(Strategy):
    """
    Simple buy-and-hold strategy.
    
    Buys the specified quantity of a symbol on the first day
    and holds until the end of the backtest period.
    """
    
    def __init__(self, symbol='SPY', quantity=100):
        """
        Initialize the strategy.
        
        Args:
            symbol: Symbol to trade (default: SPY)
            quantity: Number of shares to buy (default: 100)
        """
        super().__init__()
        self.symbol = symbol
        self.quantity = quantity
        self.invested = False
    
    def initialize(self):
        """Called before backtest starts."""
        print(f"Initializing {self.name} strategy")
        print(f"  Symbol: {self.symbol}")
        print(f"  Quantity: {self.quantity}")
    
    def on_data(self, timestamp, data):
        """
        Called on each new data point.
        
        Buy once on the first data point, then hold.
        """
        if not self.invested:
            self.invested = True
            print(f"\n[{timestamp.date()}] Placing buy order for {self.quantity} shares of {self.symbol}")
            return [Order(
                symbol=self.symbol,
                quantity=self.quantity,
                order_type='market',
                side='buy'
            )]
        return []
    
    def on_fill(self, fill):
        """Called when an order is filled."""
        print(f"[{fill.timestamp.date()}] Order filled:")
        print(f"  {fill.order.side.upper()} {fill.fill_quantity} {fill.order.symbol} @ ${fill.fill_price:.2f}")
        print(f"  Commission: ${fill.commission:.2f}")
        print(f"  Total cost: ${fill.total_cost:.2f}")
    
    def finalize(self):
        """Called after backtest ends."""
        print(f"\nFinalizing {self.name} strategy")


def main():
    """Run the backtest example."""
    print("=" * 70)
    print("Backtesting Example: Buy-and-Hold Strategy on SPY")
    print("=" * 70)
    
    # Configuration
    INITIAL_CAPITAL = 100000
    START_DATE = datetime(2020, 1, 1)
    END_DATE = datetime(2023, 12, 31)
    SYMBOLS = ['SPY']
    COMMISSION = 0.001  # 0.1%
    SLIPPAGE = 0.0005   # 0.05%
    
    print(f"\nBacktest Configuration:")
    print(f"  Initial Capital: ${INITIAL_CAPITAL:,.2f}")
    print(f"  Period: {START_DATE.date()} to {END_DATE.date()}")
    print(f"  Symbols: {', '.join(SYMBOLS)}")
    print(f"  Commission: {COMMISSION:.3%}")
    print(f"  Slippage: {SLIPPAGE:.3%}")
    
    # Create data provider
    print("\nInitializing data provider...")
    data_provider = YFinanceProvider()
    
    # Create backtesting engine
    print("Initializing backtesting engine...")
    engine = BacktestEngine(
        initial_capital=INITIAL_CAPITAL,
        data_provider=data_provider,
        commission=COMMISSION,
        slippage=SLIPPAGE
    )
    
    # Create and add strategy
    print("\nCreating strategy...")
    strategy = BuyAndHold(symbol='SPY', quantity=100)
    engine.add_strategy(strategy)
    
    # Run backtest
    print("\n" + "=" * 70)
    print("Running backtest...")
    print("=" * 70)
    
    result = engine.run(
        start_date=START_DATE,
        end_date=END_DATE,
        symbols=SYMBOLS
    )
    
    # Display results
    print("\n" + "=" * 70)
    print("Backtest Results")
    print("=" * 70)
    
    print(f"\nPerformance Summary:")
    print(f"  Strategy: {result.strategy_name}")
    print(f"  Initial Capital: ${result.initial_capital:,.2f}")
    print(f"  Final Capital: ${result.final_capital:,.2f}")
    print(f"  Total Return: {result.total_return:.2%}")
    print(f"  Profit/Loss: ${result.final_capital - result.initial_capital:,.2f}")
    
    # Get summary stats
    stats = result.get_summary_stats()
    print(f"\nTrading Statistics:")
    print(f"  Total Trades: {stats['total_trades']}")
    print(f"  Duration: {stats['duration_days']} days")
    
    if stats['total_trades'] > 0:
        print(f"  Buy Trades: {stats.get('buy_trades', 0)}")
        print(f"  Sell Trades: {stats.get('sell_trades', 0)}")
        print(f"  Total Commission: ${stats.get('total_commission', 0):.2f}")
    
    # Display trade log
    if len(result.trades) > 0:
        print("\nTrade Log:")
        trade_log = result.get_trade_log()
        print(trade_log.to_string())
    
    # Display equity curve
    print("\nEquity Curve (first 10 and last 10 days):")
    equity = result.get_equity_curve()
    if len(equity) > 0:
        print("\nFirst 10 days:")
        print(equity.head(10).to_string())
        print("\nLast 10 days:")
        print(equity.tail(10).to_string())
    
    print("\n" + "=" * 70)
    print("Backtest Complete!")
    print("=" * 70)


if __name__ == "__main__":
    main()
