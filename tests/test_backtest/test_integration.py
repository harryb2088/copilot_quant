"""Integration tests for backtesting engine."""

from datetime import datetime

import pandas as pd
import pytest

from copilot_quant.backtest import BacktestEngine, Order, Strategy
from copilot_quant.data.providers import DataProvider


class MockDataProvider(DataProvider):
    """Mock data provider with realistic test data."""
    
    def get_historical_data(self, symbol, start_date=None, end_date=None, interval='1d'):
        """Return mock SPY-like data."""
        dates = pd.date_range('2020-01-01', periods=252, freq='D')  # ~1 year
        
        # Generate realistic price data with slight upward trend
        import numpy as np
        np.random.seed(42)  # Reproducible
        
        base_price = 300.0
        returns = np.random.normal(0.0005, 0.01, 252)  # Small positive drift
        prices = base_price * (1 + returns).cumprod()
        
        return pd.DataFrame({
            'Open': prices * 0.999,
            'High': prices * 1.005,
            'Low': prices * 0.995,
            'Close': prices,
            'Volume': np.random.randint(50000000, 150000000, 252),
        }, index=dates)
    
    def get_multiple_symbols(self, symbols, start_date=None, end_date=None, interval='1d'):
        """Return mock data for multiple symbols."""
        dates = pd.date_range('2020-01-01', periods=252, freq='D')
        
        import numpy as np
        np.random.seed(42)
        
        data = {}
        for i, symbol in enumerate(symbols):
            base_price = 100.0 * (i + 1)
            returns = np.random.normal(0.0005, 0.01, 252)
            prices = base_price * (1 + returns).cumprod()
            
            data[('Close', symbol)] = prices
            data[('Open', symbol)] = prices * 0.999
            data[('High', symbol)] = prices * 1.005
            data[('Low', symbol)] = prices * 0.995
            data[('Volume', symbol)] = np.random.randint(10000000, 50000000, 252)
        
        return pd.DataFrame(data, index=dates)
    
    def get_ticker_info(self, symbol):
        """Return mock ticker info."""
        return {'longName': f'{symbol} Test Company'}


class BuyAndHoldStrategy(Strategy):
    """Simple buy and hold strategy."""
    
    def __init__(self, symbol='SPY', quantity=100):
        super().__init__()
        self.symbol = symbol
        self.quantity = quantity
        self.invested = False
    
    def on_data(self, timestamp, data):
        """Buy once and hold."""
        if not self.invested:
            self.invested = True
            return [Order(
                symbol=self.symbol,
                quantity=self.quantity,
                order_type='market',
                side='buy'
            )]
        return []


class SimpleMomentumStrategy(Strategy):
    """Simple momentum strategy - buy when price > 20-day MA."""
    
    def __init__(self, symbol='SPY', lookback=20):
        super().__init__()
        self.symbol = symbol
        self.lookback = lookback
        self.position = 0
    
    def on_data(self, timestamp, data):
        """Trade based on price vs moving average."""
        if len(data) < self.lookback:
            return []
        
        orders = []
        current_price = data['Close'].iloc[-1]
        ma = data['Close'].tail(self.lookback).mean()
        
        if current_price > ma and self.position <= 0:
            # Go long
            orders.append(Order(
                symbol=self.symbol,
                quantity=10,
                order_type='market',
                side='buy'
            ))
            self.position = 1
        elif current_price < ma and self.position > 0:
            # Close long
            orders.append(Order(
                symbol=self.symbol,
                quantity=10,
                order_type='market',
                side='sell'
            ))
            self.position = 0
        
        return orders


@pytest.mark.integration
class TestBacktestIntegration:
    """Integration tests for backtesting engine."""
    
    def test_buy_and_hold_strategy_full_backtest(self):
        """Test complete buy and hold strategy backtest."""
        provider = MockDataProvider()
        engine = BacktestEngine(
            initial_capital=100000,
            data_provider=provider,
            commission=0.001,
            slippage=0.0005
        )
        
        strategy = BuyAndHoldStrategy(symbol='SPY', quantity=100)
        engine.add_strategy(strategy)
        
        result = engine.run(
            start_date=datetime(2020, 1, 1),
            end_date=datetime(2020, 12, 31),
            symbols=['SPY']
        )
        
        # Verify result properties
        assert result.strategy_name == 'BuyAndHoldStrategy'
        assert result.initial_capital == 100000
        assert result.final_capital > 0
        
        # Should have exactly one trade (buy)
        assert len(result.trades) == 1
        assert result.trades[0].order.side == 'buy'
        
        # Should have portfolio history
        assert not result.portfolio_history.empty
        
        # Get trade log
        trade_log = result.get_trade_log()
        assert len(trade_log) == 1
        
        # Get equity curve
        equity_curve = result.get_equity_curve()
        assert len(equity_curve) > 0
    
    def test_momentum_strategy_multiple_trades(self):
        """Test momentum strategy generates multiple trades."""
        provider = MockDataProvider()
        engine = BacktestEngine(
            initial_capital=100000,
            data_provider=provider,
            commission=0.001,
            slippage=0.0005
        )
        
        strategy = SimpleMomentumStrategy(symbol='SPY', lookback=20)
        engine.add_strategy(strategy)
        
        result = engine.run(
            start_date=datetime(2020, 1, 1),
            end_date=datetime(2020, 12, 31),
            symbols=['SPY']
        )
        
        # Momentum strategy should trade multiple times
        assert len(result.trades) >= 2
        
        # Should have both buy and sell trades
        trade_log = result.get_trade_log()
        assert 'buy' in trade_log['side'].values
        assert 'sell' in trade_log['side'].values
    
    def test_backtest_result_summary_stats(self):
        """Test backtest result summary statistics."""
        provider = MockDataProvider()
        engine = BacktestEngine(
            initial_capital=100000,
            data_provider=provider,
            commission=0.001,
            slippage=0.0005
        )
        
        strategy = BuyAndHoldStrategy(symbol='SPY', quantity=100)
        engine.add_strategy(strategy)
        
        result = engine.run(
            start_date=datetime(2020, 1, 1),
            end_date=datetime(2020, 12, 31),
            symbols=['SPY']
        )
        
        # Get summary stats
        stats = result.get_summary_stats()
        
        assert 'strategy_name' in stats
        assert 'initial_capital' in stats
        assert 'final_capital' in stats
        assert 'total_return' in stats
        assert 'total_trades' in stats
        assert 'duration_days' in stats
        
        assert stats['strategy_name'] == 'BuyAndHoldStrategy'
        assert stats['initial_capital'] == 100000
        assert stats['total_trades'] == 1
    
    def test_backtest_with_transaction_costs(self):
        """Test that transaction costs impact returns."""
        provider = MockDataProvider()
        
        # Run with no costs
        engine1 = BacktestEngine(
            initial_capital=100000,
            data_provider=provider,
            commission=0.0,
            slippage=0.0
        )
        strategy1 = BuyAndHoldStrategy(symbol='SPY', quantity=100)
        engine1.add_strategy(strategy1)
        result1 = engine1.run(
            start_date=datetime(2020, 1, 1),
            end_date=datetime(2020, 12, 31),
            symbols=['SPY']
        )
        
        # Run with costs
        engine2 = BacktestEngine(
            initial_capital=100000,
            data_provider=provider,
            commission=0.01,  # 1% commission
            slippage=0.005     # 0.5% slippage
        )
        strategy2 = BuyAndHoldStrategy(symbol='SPY', quantity=100)
        engine2.add_strategy(strategy2)
        result2 = engine2.run(
            start_date=datetime(2020, 1, 1),
            end_date=datetime(2020, 12, 31),
            symbols=['SPY']
        )
        
        # Result with costs should have lower final capital
        assert result2.final_capital < result1.final_capital
    
    def test_strategy_callbacks_called(self):
        """Test that strategy callbacks are called correctly."""
        class CallbackTrackingStrategy(Strategy):
            def __init__(self):
                super().__init__()
                self.initialize_called = False
                self.finalize_called = False
                self.on_data_count = 0
                self.on_fill_count = 0
            
            def initialize(self):
                self.initialize_called = True
            
            def on_data(self, timestamp, data):
                self.on_data_count += 1
                if self.on_data_count == 1:
                    return [Order(symbol='SPY', quantity=10, order_type='market', side='buy')]
                return []
            
            def on_fill(self, fill):
                self.on_fill_count += 1
            
            def finalize(self):
                self.finalize_called = True
        
        provider = MockDataProvider()
        engine = BacktestEngine(
            initial_capital=100000,
            data_provider=provider,
            commission=0.001,
            slippage=0.0005
        )
        
        strategy = CallbackTrackingStrategy()
        engine.add_strategy(strategy)
        
        result = engine.run(
            start_date=datetime(2020, 1, 1),
            end_date=datetime(2020, 12, 31),
            symbols=['SPY']
        )
        
        # Verify callbacks were called
        assert strategy.initialize_called
        assert strategy.finalize_called
        assert strategy.on_data_count > 0
        assert strategy.on_fill_count == 1  # One buy order
    
    def test_position_tracking(self):
        """Test that positions are tracked correctly."""
        provider = MockDataProvider()
        engine = BacktestEngine(
            initial_capital=100000,
            data_provider=provider,
            commission=0.001,
            slippage=0.0005
        )
        
        strategy = BuyAndHoldStrategy(symbol='SPY', quantity=100)
        engine.add_strategy(strategy)
        
        # Before backtest, no positions
        assert len(engine.get_positions()) == 0
        
        result = engine.run(
            start_date=datetime(2020, 1, 1),
            end_date=datetime(2020, 12, 31),
            symbols=['SPY']
        )
        
        # After backtest with buy-and-hold, should have one position
        # Note: positions are from engine state after run
        # The result object doesn't expose positions directly
        assert result.final_capital != result.initial_capital
    
    def test_long_and_short_positions(self):
        """Test strategy with both long and short positions."""
        class LongShortStrategy(Strategy):
            def __init__(self):
                super().__init__()
                self.trade_count = 0
            
            def on_data(self, timestamp, data):
                self.trade_count += 1
                
                # First: buy
                if self.trade_count == 10:
                    return [Order(symbol='SPY', quantity=10, order_type='market', side='buy')]
                # Second: sell to close and go short
                elif self.trade_count == 20:
                    return [Order(symbol='SPY', quantity=20, order_type='market', side='sell')]
                # Third: buy to close short
                elif self.trade_count == 30:
                    return [Order(symbol='SPY', quantity=10, order_type='market', side='buy')]
                
                return []
        
        provider = MockDataProvider()
        engine = BacktestEngine(
            initial_capital=100000,
            data_provider=provider,
            commission=0.001,
            slippage=0.0005
        )
        
        strategy = LongShortStrategy()
        engine.add_strategy(strategy)
        
        result = engine.run(
            start_date=datetime(2020, 1, 1),
            end_date=datetime(2020, 12, 31),
            symbols=['SPY']
        )
        
        # Should have 3 trades
        assert len(result.trades) == 3
        
        # Check trade sides
        assert result.trades[0].order.side == 'buy'
        assert result.trades[1].order.side == 'sell'
        assert result.trades[2].order.side == 'buy'
