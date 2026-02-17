#!/usr/bin/env python
"""
Example: Running a backtest with comprehensive performance metrics.

This example demonstrates how to:
1. Create a custom trading strategy
2. Set up the backtesting engine
3. Run a backtest on historical data
4. Analyze comprehensive performance metrics

Run with: python examples/run_backtest_with_metrics.py
"""

from datetime import datetime

from copilot_quant.backtest import BacktestEngine, Order, Strategy
from copilot_quant.data.providers import YFinanceProvider


class SimpleMomentum(Strategy):
    """
    Simple momentum strategy.
    
    Buys when price is above 50-day MA, sells when below.
    """
    
    def __init__(self, symbol='SPY', quantity=100, lookback=50):
        """
        Initialize the strategy.
        
        Args:
            symbol: Symbol to trade
            quantity: Number of shares to trade
            lookback: Moving average lookback period
        """
        super().__init__()
        self.symbol = symbol
        self.quantity = quantity
        self.lookback = lookback
        self.position = 0
    
    def initialize(self):
        """Called before backtest starts."""
        print(f"\nInitializing {self.name} strategy")
        print(f"  Symbol: {self.symbol}")
        print(f"  Quantity: {self.quantity}")
        print(f"  MA Lookback: {self.lookback}")
    
    def on_data(self, timestamp, data):
        """
        Called on each new data point.
        
        Buy when price crosses above MA, sell when crosses below.
        """
        # Need enough data for MA
        if len(data) < self.lookback:
            return []
        
        # Calculate moving average
        closes = data['Close']
        ma = closes.tail(self.lookback).mean()
        current_price = closes.iloc[-1]
        
        orders = []
        
        # Buy signal: price above MA and not invested
        if current_price > ma and self.position == 0:
            self.position = 1
            orders.append(Order(
                symbol=self.symbol,
                quantity=self.quantity,
                order_type='market',
                side='buy'
            ))
        
        # Sell signal: price below MA and invested
        elif current_price < ma and self.position == 1:
            self.position = 0
            orders.append(Order(
                symbol=self.symbol,
                quantity=self.quantity,
                order_type='market',
                side='sell'
            ))
        
        return orders
    
    def finalize(self):
        """Called after backtest ends."""
        print(f"\nFinalizing {self.name} strategy")


def print_section(title):
    """Print a section header."""
    print("\n" + "=" * 70)
    print(title)
    print("=" * 70)


def main():
    """Run the backtest example with metrics."""
    print_section("Backtesting Example: Momentum Strategy with Performance Metrics")
    
    # Configuration
    INITIAL_CAPITAL = 100000
    START_DATE = datetime(2020, 1, 1)
    END_DATE = datetime(2023, 12, 31)
    SYMBOLS = ['SPY']
    COMMISSION = 0.001  # 0.1%
    SLIPPAGE = 0.0005   # 0.05%
    RISK_FREE_RATE = 0.02  # 2% annual
    
    print("\nBacktest Configuration:")
    print(f"  Initial Capital: ${INITIAL_CAPITAL:,.2f}")
    print(f"  Period: {START_DATE.date()} to {END_DATE.date()}")
    print(f"  Symbols: {', '.join(SYMBOLS)}")
    print(f"  Commission: {COMMISSION:.3%}")
    print(f"  Slippage: {SLIPPAGE:.3%}")
    print(f"  Risk-Free Rate: {RISK_FREE_RATE:.1%}")
    
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
    strategy = SimpleMomentum(symbol='SPY', quantity=100, lookback=50)
    engine.add_strategy(strategy)
    
    # Run backtest
    print_section("Running backtest...")
    
    result = engine.run(
        start_date=START_DATE,
        end_date=END_DATE,
        symbols=SYMBOLS
    )
    
    # Display comprehensive metrics
    print_section("Performance Metrics")
    
    metrics = result.get_performance_metrics(risk_free_rate=RISK_FREE_RATE)
    
    print("\nBasic Information:")
    print(f"  Strategy: {metrics['strategy_name']}")
    print(f"  Period: {metrics['start_date'].date()} to {metrics['end_date'].date()}")
    print(f"  Trading Days: {metrics['trading_days']}")
    print(f"  Trading Years: {metrics['trading_years']:.2f}")
    
    print("\nReturn Metrics:")
    print(f"  Initial Capital: ${metrics['initial_capital']:,.2f}")
    print(f"  Final Capital: ${metrics['final_capital']:,.2f}")
    print(f"  Total Return: {metrics['total_return']:.2%}")
    print(f"  Annualized Return (CAGR): {metrics['annualized_return']:.2%}")
    print(f"  Profit/Loss: ${metrics['final_capital'] - metrics['initial_capital']:,.2f}")
    
    print("\nRisk Metrics:")
    print(f"  Volatility (Annual): {metrics['volatility']:.2%}")
    print(f"  Maximum Drawdown: {metrics['max_drawdown']:.2%}")
    print(f"  Sharpe Ratio: {metrics['sharpe_ratio']:.3f}")
    print(f"  Sortino Ratio: {metrics['sortino_ratio']:.3f}")
    print(f"  Calmar Ratio: {metrics['calmar_ratio']:.3f}")
    
    print("\nTrade Statistics:")
    print(f"  Total Trades: {metrics['total_trades']}")
    print(f"  Win Rate: {metrics['win_rate']:.2%}")
    print(f"  Profit Factor: {metrics['profit_factor']:.2f}")
    print(f"  Average Win: ${metrics['avg_win']:.2f}")
    print(f"  Average Loss: ${metrics['avg_loss']:.2f}")
    print(f"  Average Trade: ${metrics['avg_trade']:.2f}")
    
    if 'total_commission' in metrics:
        print(f"  Total Commission: ${metrics['total_commission']:.2f}")
    
    # Display trade log
    if len(result.trades) > 0:
        print_section("Trade Log")
        trade_log = result.get_trade_log()
        print("\nAll Trades:")
        print(trade_log.to_string())
    
    # Equity curve summary
    print_section("Equity Curve Summary")
    equity = result.get_equity_curve()
    if len(equity) > 0:
        print(f"\nStarting Value: ${equity.iloc[0]:,.2f}")
        print(f"Ending Value: ${equity.iloc[-1]:,.2f}")
        print(f"Minimum Value: ${equity.min():,.2f}")
        print(f"Maximum Value: ${equity.max():,.2f}")
        
        print("\nFirst 5 days:")
        print(equity.head(5).to_frame('Portfolio Value').to_string())
        
        print("\nLast 5 days:")
        print(equity.tail(5).to_frame('Portfolio Value').to_string())
    
    # Performance interpretation
    print_section("Performance Interpretation")
    
    print("\nKey Takeaways:")
    
    if metrics['total_return'] > 0:
        print(f"  ✓ Strategy was profitable with {metrics['total_return']:.2%} total return")
    else:
        print(f"  ✗ Strategy lost {abs(metrics['total_return']):.2%}")
    
    if metrics['sharpe_ratio'] > 1.0:
        print(f"  ✓ Good risk-adjusted returns (Sharpe: {metrics['sharpe_ratio']:.2f})")
    elif metrics['sharpe_ratio'] > 0:
        print(f"  ~ Moderate risk-adjusted returns (Sharpe: {metrics['sharpe_ratio']:.2f})")
    else:
        print(f"  ✗ Poor risk-adjusted returns (Sharpe: {metrics['sharpe_ratio']:.2f})")
    
    if abs(metrics['max_drawdown']) < 0.10:
        print(f"  ✓ Low maximum drawdown ({metrics['max_drawdown']:.2%})")
    elif abs(metrics['max_drawdown']) < 0.20:
        print(f"  ~ Moderate maximum drawdown ({metrics['max_drawdown']:.2%})")
    else:
        print(f"  ✗ High maximum drawdown ({metrics['max_drawdown']:.2%})")
    
    if metrics['win_rate'] > 0.5:
        print(f"  ✓ Above 50% win rate ({metrics['win_rate']:.2%})")
    else:
        print(f"  ~ Below 50% win rate ({metrics['win_rate']:.2%})")
    
    if metrics['profit_factor'] > 1.5:
        print(f"  ✓ Strong profit factor ({metrics['profit_factor']:.2f})")
    elif metrics['profit_factor'] > 1.0:
        print(f"  ~ Positive profit factor ({metrics['profit_factor']:.2f})")
    else:
        print(f"  ✗ Negative profit factor ({metrics['profit_factor']:.2f})")
    
    print_section("Backtest Complete!")


if __name__ == "__main__":
    main()
