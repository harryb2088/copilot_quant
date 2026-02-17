"""
Signal-Based Multi-Strategy Backtest Example

This example demonstrates the signal-based allocation system where multiple
strategies compete for capital based on signal quality rather than pre-allocated pods.

Key features demonstrated:
- Multiple strategies generating signals simultaneously
- Dynamic position sizing based on signal quality
- Risk limits enforcement (max position, max deployment)
- Strategy attribution tracking
"""

from datetime import datetime

from copilot_quant.backtest import MultiStrategyEngine, SignalBasedStrategy, TradingSignal
from copilot_quant.data.providers import YFinanceProvider


class MeanReversionStrategy(SignalBasedStrategy):
    """
    High-quality, low-frequency strategy.
    
    Generates rare signals when price deviates significantly from moving average.
    """
    
    def __init__(self, window=20, threshold=2.0):
        super().__init__()
        self.window = window
        self.threshold = threshold
    
    def generate_signals(self, timestamp, data):
        """Generate mean reversion signals."""
        signals = []
        
        if len(data) < self.window:
            return signals
        
        # Get recent data
        recent = data.tail(self.window)
        
        # Check each symbol
        symbols = recent['Symbol'].unique() if 'Symbol' in recent.columns else [None]
        
        for symbol in symbols:
            if symbol is None:
                symbol_data = recent
            else:
                symbol_data = recent[recent['Symbol'] == symbol]
            
            if len(symbol_data) < self.window:
                continue
            
            # Calculate indicators
            close_prices = symbol_data['Close'].values
            ma = close_prices.mean()
            std = close_prices.std()
            current_price = close_prices[-1]
            
            # Mean reversion signal when price is 2 std devs from mean
            z_score = (current_price - ma) / std if std > 0 else 0
            
            if abs(z_score) > self.threshold:
                # High confidence for strong deviations
                confidence = min(abs(z_score) / 3.0, 1.0)
                
                signals.append(TradingSignal(
                    symbol=symbol or 'UNKNOWN',
                    side='buy' if z_score < 0 else 'sell',
                    confidence=confidence,
                    sharpe_estimate=2.0,  # High Sharpe expected
                    entry_price=current_price,
                    strategy_name=self.name
                ))
        
        return signals


class MomentumStrategy(SignalBasedStrategy):
    """
    Moderate-quality, high-frequency strategy.
    
    Generates frequent signals based on price momentum.
    """
    
    def __init__(self, short_window=5, long_window=20):
        super().__init__()
        self.short_window = short_window
        self.long_window = long_window
    
    def generate_signals(self, timestamp, data):
        """Generate momentum signals."""
        signals = []
        
        if len(data) < self.long_window:
            return signals
        
        # Get recent data
        recent = data.tail(self.long_window)
        
        # Check each symbol
        symbols = recent['Symbol'].unique() if 'Symbol' in recent.columns else [None]
        
        for symbol in symbols:
            if symbol is None:
                symbol_data = recent
            else:
                symbol_data = recent[recent['Symbol'] == symbol]
            
            if len(symbol_data) < self.long_window:
                continue
            
            # Calculate moving averages
            close_prices = symbol_data['Close'].values
            short_ma = close_prices[-self.short_window:].mean()
            long_ma = close_prices.mean()
            current_price = close_prices[-1]
            
            # Momentum signal when short MA crosses long MA
            if short_ma > long_ma * 1.02:  # 2% above
                # Moderate confidence for momentum
                strength = (short_ma - long_ma) / long_ma
                confidence = min(strength * 10, 0.7)  # Cap at 0.7
                
                signals.append(TradingSignal(
                    symbol=symbol or 'UNKNOWN',
                    side='buy',
                    confidence=confidence,
                    sharpe_estimate=1.2,  # Moderate Sharpe
                    entry_price=current_price,
                    strategy_name=self.name
                ))
        
        return signals


def main():
    """Run multi-strategy backtest example."""
    
    print("=" * 80)
    print("Signal-Based Multi-Strategy Backtest Example")
    print("=" * 80)
    
    # Initialize data provider
    print("\nInitializing data provider...")
    data_provider = YFinanceProvider()
    
    # Create multi-strategy engine
    print("Creating multi-strategy engine...")
    engine = MultiStrategyEngine(
        initial_capital=100000,
        data_provider=data_provider,
        commission=0.001,      # 0.1% commission
        slippage=0.0005,       # 0.05% slippage
        max_position_pct=0.025,  # 2.5% max per position
        max_deployed_pct=0.80    # 80% max deployed
    )
    
    # Add strategies
    print("Adding strategies...")
    mean_reversion = MeanReversionStrategy(window=20, threshold=2.0)
    mean_reversion.name = 'MeanReversion'
    engine.add_strategy(mean_reversion)
    
    momentum = MomentumStrategy(short_window=5, long_window=20)
    momentum.name = 'Momentum'
    engine.add_strategy(momentum)
    
    # Run backtest
    print("\nRunning backtest...")
    print("Date Range: 2023-01-01 to 2023-12-31")
    print("Symbols: SPY, AAPL, MSFT, GOOGL, AMZN")
    print()
    
    result = engine.run(
        start_date=datetime(2023, 1, 1),
        end_date=datetime(2023, 12, 31),
        symbols=['SPY', 'AAPL', 'MSFT', 'GOOGL', 'AMZN']
    )
    
    # Display overall results
    print("\n" + "=" * 80)
    print("OVERALL RESULTS")
    print("=" * 80)
    print(f"Initial Capital:  ${result.initial_capital:,.2f}")
    print(f"Final Capital:    ${result.final_capital:,.2f}")
    print(f"Total Return:     {result.total_return:.2%}")
    print(f"Total Trades:     {len(result.trades)}")
    
    # Display strategy attribution
    print("\n" + "=" * 80)
    print("STRATEGY ATTRIBUTION")
    print("=" * 80)
    
    for strategy_name, attribution in result.strategy_attributions.items():
        print(f"\n{strategy_name}:")
        print(f"  Trades:                  {attribution['num_trades']}")
        print(f"  Total Deployed:          ${attribution['total_deployed']:,.2f}")
        print(f"  Total P&L:               ${attribution['total_pnl']:,.2f}")
        print(f"  Deployed Capital Return: {attribution['deployed_capital_return']:.2%}")
        print(f"  Win Rate:                {attribution['win_rate']:.1%}")
        
        if attribution['num_trades'] > 0:
            print(f"  Wins:                    {attribution['num_wins']}")
            print(f"  Losses:                  {attribution['num_losses']}")
    
    # Key takeaways
    print("\n" + "=" * 80)
    print("KEY TAKEAWAYS")
    print("=" * 80)
    print("""
This example demonstrates signal-based allocation where:

1. Both strategies compete for the same capital pool
2. Position sizes are determined by signal quality (confidence × Sharpe)
3. High-quality signals get larger allocations
4. Capital flows dynamically to the best opportunities
5. Attribution reflects actual deployed capital, not allocated pods

Benefits:
✓ No penalty for infrequent but high-quality strategies
✓ No idle capital sitting in inactive strategies  
✓ Fair performance measurement based on actual signal quality
✓ Global risk limits prevent overexposure
✓ Transparent P&L attribution by strategy type
""")
    
    print("\n" + "=" * 80)


if __name__ == "__main__":
    main()
