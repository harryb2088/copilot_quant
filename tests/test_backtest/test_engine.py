"""Tests for backtesting engine."""

from datetime import datetime
from unittest.mock import Mock, patch

import pandas as pd
import pytest

from copilot_quant.backtest.engine import BacktestEngine
from copilot_quant.backtest.orders import Order
from copilot_quant.backtest.strategy import Strategy
from copilot_quant.data.providers import DataProvider


class MockDataProvider(DataProvider):
    """Mock data provider for testing."""
    
    def __init__(self, data=None):
        self.data = data
    
    def get_historical_data(self, symbol, start_date=None, end_date=None, interval='1d'):
        """Return mock data."""
        if self.data is not None:
            return self.data
        
        # Default test data
        dates = pd.date_range('2024-01-01', periods=10, freq='D')
        return pd.DataFrame({
            'Open': [100.0] * 10,
            'High': [105.0] * 10,
            'Low': [95.0] * 10,
            'Close': [100.0 + i for i in range(10)],
            'Volume': [1000000] * 10,
        }, index=dates)
    
    def get_multiple_symbols(self, symbols, start_date=None, end_date=None, interval='1d'):
        """Return mock data for multiple symbols."""
        if self.data is not None:
            return self.data
        
        dates = pd.date_range('2024-01-01', periods=10, freq='D')
        data = {}
        
        for symbol in symbols:
            data[('Close', symbol)] = [100.0 + i for i in range(10)]
        
        return pd.DataFrame(data, index=dates)
    
    def get_ticker_info(self, symbol):
        """Return mock ticker info."""
        return {'longName': 'Test Company'}


class BuyOnceStrategy(Strategy):
    """Simple strategy that buys once for testing."""
    
    def __init__(self):
        super().__init__()
        self.bought = False
    
    def on_data(self, timestamp, data):
        """Buy once on first data point."""
        if not self.bought:
            self.bought = True
            return [Order(symbol='AAPL', quantity=10, order_type='market', side='buy')]
        return []


class TestBacktestEngine:
    """Tests for BacktestEngine class."""
    
    def test_engine_initialization(self):
        """Test engine initializes correctly."""
        provider = MockDataProvider()
        engine = BacktestEngine(
            initial_capital=100000,
            data_provider=provider,
            commission=0.001,
            slippage=0.0005
        )
        
        assert engine.initial_capital == 100000
        assert engine.commission_rate == 0.001
        assert engine.slippage_rate == 0.0005
        assert engine.cash == 100000
        assert engine.strategy is None
    
    def test_add_strategy(self):
        """Test adding a strategy to the engine."""
        provider = MockDataProvider()
        engine = BacktestEngine(initial_capital=100000, data_provider=provider)
        
        strategy = BuyOnceStrategy()
        engine.add_strategy(strategy)
        
        assert engine.strategy == strategy
    
    def test_run_without_strategy_raises_error(self):
        """Test that running without strategy raises error."""
        provider = MockDataProvider()
        engine = BacktestEngine(initial_capital=100000, data_provider=provider)
        
        with pytest.raises(ValueError, match="No strategy registered"):
            engine.run(
                start_date=datetime(2024, 1, 1),
                end_date=datetime(2024, 1, 10),
                symbols=['AAPL']
            )
    
    def test_get_portfolio_value_initial(self):
        """Test initial portfolio value equals cash."""
        provider = MockDataProvider()
        engine = BacktestEngine(initial_capital=100000, data_provider=provider)
        
        assert engine.get_portfolio_value() == 100000
    
    def test_get_positions_empty(self):
        """Test getting positions when none exist."""
        provider = MockDataProvider()
        engine = BacktestEngine(initial_capital=100000, data_provider=provider)
        
        positions = engine.get_positions()
        assert positions == {}
    
    def test_simple_backtest_runs(self):
        """Test that a simple backtest runs successfully."""
        # Create mock data
        dates = pd.date_range('2024-01-01', periods=5, freq='D')
        data = pd.DataFrame({
            'Open': [100.0, 101.0, 102.0, 103.0, 104.0],
            'High': [105.0, 106.0, 107.0, 108.0, 109.0],
            'Low': [95.0, 96.0, 97.0, 98.0, 99.0],
            'Close': [100.0, 101.0, 102.0, 103.0, 104.0],
            'Volume': [1000000] * 5,
        }, index=dates)
        
        provider = MockDataProvider(data=data)
        engine = BacktestEngine(
            initial_capital=10000,
            data_provider=provider,
            commission=0.001,
            slippage=0.0005
        )
        
        strategy = BuyOnceStrategy()
        engine.add_strategy(strategy)
        
        result = engine.run(
            start_date=datetime(2024, 1, 1),
            end_date=datetime(2024, 1, 5),
            symbols=['AAPL']
        )
        
        assert result is not None
        assert result.strategy_name == 'BuyOnceStrategy'
        assert result.initial_capital == 10000
        assert len(result.trades) > 0
    
    def test_backtest_executes_buy_order(self):
        """Test that buy orders are executed correctly."""
        dates = pd.date_range('2024-01-01', periods=5, freq='D')
        data = pd.DataFrame({
            'Close': [100.0, 101.0, 102.0, 103.0, 104.0],
            'Open': [100.0, 101.0, 102.0, 103.0, 104.0],
            'High': [105.0, 106.0, 107.0, 108.0, 109.0],
            'Low': [95.0, 96.0, 97.0, 98.0, 99.0],
            'Volume': [1000000] * 5,
        }, index=dates)
        
        provider = MockDataProvider(data=data)
        engine = BacktestEngine(
            initial_capital=10000,
            data_provider=provider,
            commission=0.001,
            slippage=0.0005
        )
        
        strategy = BuyOnceStrategy()
        engine.add_strategy(strategy)
        
        result = engine.run(
            start_date=datetime(2024, 1, 1),
            end_date=datetime(2024, 1, 5),
            symbols=['AAPL']
        )
        
        # Should have one buy trade
        assert len(result.trades) == 1
        assert result.trades[0].order.side == 'buy'
        assert result.trades[0].order.symbol == 'AAPL'
        assert result.trades[0].fill_quantity == 10
    
    def test_backtest_applies_commission(self):
        """Test that commission is applied to trades."""
        dates = pd.date_range('2024-01-01', periods=5, freq='D')
        data = pd.DataFrame({
            'Close': [100.0, 101.0, 102.0, 103.0, 104.0],
            'Open': [100.0, 101.0, 102.0, 103.0, 104.0],
            'High': [105.0, 106.0, 107.0, 108.0, 109.0],
            'Low': [95.0, 96.0, 97.0, 98.0, 99.0],
            'Volume': [1000000] * 5,
        }, index=dates)
        
        provider = MockDataProvider(data=data)
        engine = BacktestEngine(
            initial_capital=10000,
            data_provider=provider,
            commission=0.001,  # 0.1% commission
            slippage=0.0
        )
        
        strategy = BuyOnceStrategy()
        engine.add_strategy(strategy)
        
        result = engine.run(
            start_date=datetime(2024, 1, 1),
            end_date=datetime(2024, 1, 5),
            symbols=['AAPL']
        )
        
        # Commission should be > 0
        fill = result.trades[0]
        assert fill.commission > 0
        # Commission should be approximately 0.1% of trade value
        expected_commission = fill.fill_price * fill.fill_quantity * 0.001
        assert abs(fill.commission - expected_commission) < 0.01
    
    def test_backtest_applies_slippage(self):
        """Test that slippage is applied to market orders."""
        dates = pd.date_range('2024-01-01', periods=5, freq='D')
        data = pd.DataFrame({
            'Close': [100.0, 101.0, 102.0, 103.0, 104.0],
            'Open': [100.0, 101.0, 102.0, 103.0, 104.0],
            'High': [105.0, 106.0, 107.0, 108.0, 109.0],
            'Low': [95.0, 96.0, 97.0, 98.0, 99.0],
            'Volume': [1000000] * 5,
        }, index=dates)
        
        provider = MockDataProvider(data=data)
        engine = BacktestEngine(
            initial_capital=10000,
            data_provider=provider,
            commission=0.0,
            slippage=0.001  # 0.1% slippage
        )
        
        strategy = BuyOnceStrategy()
        engine.add_strategy(strategy)
        
        result = engine.run(
            start_date=datetime(2024, 1, 1),
            end_date=datetime(2024, 1, 5),
            symbols=['AAPL']
        )
        
        # Fill price should be higher than market price due to slippage on buy
        fill = result.trades[0]
        # First close price is 100.0, fill should be ~100.1 (100 * 1.001)
        assert fill.fill_price > 100.0
    
    def test_backtest_insufficient_capital(self):
        """Test that orders are rejected with insufficient capital."""
        dates = pd.date_range('2024-01-01', periods=5, freq='D')
        data = pd.DataFrame({
            'Close': [100.0, 101.0, 102.0, 103.0, 104.0],
            'Open': [100.0, 101.0, 102.0, 103.0, 104.0],
            'High': [105.0, 106.0, 107.0, 108.0, 109.0],
            'Low': [95.0, 96.0, 97.0, 98.0, 99.0],
            'Volume': [1000000] * 5,
        }, index=dates)
        
        provider = MockDataProvider(data=data)
        
        # Very low capital
        engine = BacktestEngine(
            initial_capital=10,  # Only $10
            data_provider=provider,
            commission=0.001,
            slippage=0.0005
        )
        
        strategy = BuyOnceStrategy()  # Tries to buy 10 shares at ~$100
        engine.add_strategy(strategy)
        
        result = engine.run(
            start_date=datetime(2024, 1, 1),
            end_date=datetime(2024, 1, 5),
            symbols=['AAPL']
        )
        
        # Order should be rejected, no trades
        assert len(result.trades) == 0
    
    def test_backtest_portfolio_history_recorded(self):
        """Test that portfolio history is recorded."""
        dates = pd.date_range('2024-01-01', periods=5, freq='D')
        data = pd.DataFrame({
            'Close': [100.0, 101.0, 102.0, 103.0, 104.0],
            'Open': [100.0, 101.0, 102.0, 103.0, 104.0],
            'High': [105.0, 106.0, 107.0, 108.0, 109.0],
            'Low': [95.0, 96.0, 97.0, 98.0, 99.0],
            'Volume': [1000000] * 5,
        }, index=dates)
        
        provider = MockDataProvider(data=data)
        engine = BacktestEngine(
            initial_capital=10000,
            data_provider=provider,
            commission=0.001,
            slippage=0.0005
        )
        
        strategy = BuyOnceStrategy()
        engine.add_strategy(strategy)
        
        result = engine.run(
            start_date=datetime(2024, 1, 1),
            end_date=datetime(2024, 1, 5),
            symbols=['AAPL']
        )
        
        # Should have portfolio history
        assert not result.portfolio_history.empty
        assert 'portfolio_value' in result.portfolio_history.columns
        assert len(result.portfolio_history) == 5  # One for each day
    
    def test_backtest_calculates_return(self):
        """Test that total return is calculated correctly."""
        dates = pd.date_range('2024-01-01', periods=5, freq='D')
        data = pd.DataFrame({
            'Close': [100.0, 101.0, 102.0, 103.0, 104.0],
            'Open': [100.0, 101.0, 102.0, 103.0, 104.0],
            'High': [105.0, 106.0, 107.0, 108.0, 109.0],
            'Low': [95.0, 96.0, 97.0, 98.0, 99.0],
            'Volume': [1000000] * 5,
        }, index=dates)
        
        provider = MockDataProvider(data=data)
        engine = BacktestEngine(
            initial_capital=10000,
            data_provider=provider,
            commission=0.001,
            slippage=0.0005
        )
        
        strategy = BuyOnceStrategy()
        engine.add_strategy(strategy)
        
        result = engine.run(
            start_date=datetime(2024, 1, 1),
            end_date=datetime(2024, 1, 5),
            symbols=['AAPL']
        )
        
        # Check return calculation
        expected_return = (result.final_capital - result.initial_capital) / result.initial_capital
        assert abs(result.total_return - expected_return) < 0.0001
    
    def test_backtest_with_empty_data(self):
        """Test backtest handles empty data gracefully."""
        provider = MockDataProvider(data=pd.DataFrame())
        engine = BacktestEngine(initial_capital=10000, data_provider=provider)
        
        strategy = BuyOnceStrategy()
        engine.add_strategy(strategy)
        
        result = engine.run(
            start_date=datetime(2024, 1, 1),
            end_date=datetime(2024, 1, 5),
            symbols=['AAPL']
        )
        
        assert result.total_return == 0.0
        assert len(result.trades) == 0
        assert result.final_capital == result.initial_capital
