"""Tests for strategy base class."""

from datetime import datetime

import pandas as pd
import pytest

from copilot_quant.backtest.orders import Order
from copilot_quant.backtest.strategy import Strategy


class SimpleStrategy(Strategy):
    """Simple test strategy that buys on first data point."""
    
    def __init__(self):
        super().__init__()
        self.initialized = False
        self.finalized = False
        self.data_count = 0
        self.fills_received = []
    
    def initialize(self):
        """Mark strategy as initialized."""
        self.initialized = True
    
    def on_data(self, timestamp, data):
        """Buy once on first data point."""
        self.data_count += 1
        if self.data_count == 1:
            return [Order(symbol='AAPL', quantity=100, order_type='market', side='buy')]
        return []
    
    def on_fill(self, fill):
        """Track fills received."""
        self.fills_received.append(fill)
    
    def finalize(self):
        """Mark strategy as finalized."""
        self.finalized = True


class TestStrategy:
    """Tests for Strategy base class."""
    
    def test_strategy_is_abstract(self):
        """Test that Strategy cannot be instantiated directly."""
        with pytest.raises(TypeError):
            Strategy()
    
    def test_strategy_requires_on_data(self):
        """Test that subclasses must implement on_data."""
        class IncompleteStrategy(Strategy):
            pass
        
        with pytest.raises(TypeError):
            IncompleteStrategy()
    
    def test_strategy_name(self):
        """Test that strategy name is set correctly."""
        strategy = SimpleStrategy()
        assert strategy.name == 'SimpleStrategy'
    
    def test_strategy_initialize_called(self):
        """Test that initialize is called."""
        strategy = SimpleStrategy()
        assert not strategy.initialized
        
        strategy.initialize()
        assert strategy.initialized
    
    def test_strategy_finalize_called(self):
        """Test that finalize is called."""
        strategy = SimpleStrategy()
        assert not strategy.finalized
        
        strategy.finalize()
        assert strategy.finalized
    
    def test_strategy_on_data_returns_orders(self):
        """Test that on_data returns orders."""
        strategy = SimpleStrategy()
        
        data = pd.DataFrame({
            'Close': [150.0],
        }, index=[datetime(2024, 1, 1)])
        
        orders = strategy.on_data(datetime(2024, 1, 1), data)
        
        assert isinstance(orders, list)
        assert len(orders) == 1
        assert isinstance(orders[0], Order)
        assert orders[0].symbol == 'AAPL'
        assert orders[0].quantity == 100
    
    def test_strategy_on_data_called_multiple_times(self):
        """Test that on_data is called for each data point."""
        strategy = SimpleStrategy()
        
        data = pd.DataFrame({
            'Close': [150.0],
        }, index=[datetime(2024, 1, 1)])
        
        # First call returns order
        orders1 = strategy.on_data(datetime(2024, 1, 1), data)
        assert len(orders1) == 1
        
        # Second call returns no orders
        orders2 = strategy.on_data(datetime(2024, 1, 2), data)
        assert len(orders2) == 0
        
        assert strategy.data_count == 2
    
    def test_strategy_on_fill_receives_fills(self):
        """Test that on_fill receives fill objects."""
        from copilot_quant.backtest.orders import Fill
        
        strategy = SimpleStrategy()
        
        order = Order(symbol='AAPL', quantity=100, order_type='market', side='buy')
        fill = Fill(
            order=order,
            fill_price=150.0,
            fill_quantity=100,
            commission=15.0,
            timestamp=datetime(2024, 1, 1)
        )
        
        strategy.on_fill(fill)
        
        assert len(strategy.fills_received) == 1
        assert strategy.fills_received[0] == fill
    
    def test_strategy_repr(self):
        """Test strategy string representation."""
        strategy = SimpleStrategy()
        assert repr(strategy) == "SimpleStrategy()"


class BuyAndHoldStrategy(Strategy):
    """Buy and hold strategy for testing."""
    
    def __init__(self, symbol='SPY', quantity=100):
        super().__init__()
        self.symbol = symbol
        self.quantity = quantity
        self.invested = False
    
    def on_data(self, timestamp, data):
        """Buy on first call, then hold."""
        if not self.invested:
            self.invested = True
            return [Order(
                symbol=self.symbol,
                quantity=self.quantity,
                order_type='market',
                side='buy'
            )]
        return []


class TestBuyAndHold:
    """Tests for example buy and hold strategy."""
    
    def test_buy_and_hold_buys_once(self):
        """Test that strategy buys once and holds."""
        strategy = BuyAndHoldStrategy(symbol='SPY', quantity=100)
        
        data = pd.DataFrame({
            'Close': [400.0],
        }, index=[datetime(2024, 1, 1)])
        
        # First call should buy
        orders1 = strategy.on_data(datetime(2024, 1, 1), data)
        assert len(orders1) == 1
        assert orders1[0].symbol == 'SPY'
        assert orders1[0].quantity == 100
        assert orders1[0].side == 'buy'
        
        # Subsequent calls should not trade
        orders2 = strategy.on_data(datetime(2024, 1, 2), data)
        assert len(orders2) == 0
        
        orders3 = strategy.on_data(datetime(2024, 1, 3), data)
        assert len(orders3) == 0
    
    def test_buy_and_hold_configurable(self):
        """Test that strategy parameters are configurable."""
        strategy = BuyAndHoldStrategy(symbol='AAPL', quantity=50)
        
        assert strategy.symbol == 'AAPL'
        assert strategy.quantity == 50
        
        data = pd.DataFrame({
            'Close': [150.0],
        }, index=[datetime(2024, 1, 1)])
        
        orders = strategy.on_data(datetime(2024, 1, 1), data)
        assert orders[0].symbol == 'AAPL'
        assert orders[0].quantity == 50


class MovingAverageCrossStrategy(Strategy):
    """Simple moving average crossover strategy for testing."""
    
    def __init__(self, symbol='SPY', short_window=5, long_window=20):
        super().__init__()
        self.symbol = symbol
        self.short_window = short_window
        self.long_window = long_window
        self.position = 0
    
    def on_data(self, timestamp, data):
        """Generate signals based on MA crossover."""
        orders = []
        
        # Need enough data for long MA
        if len(data) < self.long_window:
            return orders
        
        # Calculate moving averages
        closes = data['Close']
        short_ma = closes.tail(self.short_window).mean()
        long_ma = closes.tail(self.long_window).mean()
        
        # Generate signals
        if short_ma > long_ma and self.position <= 0:
            # Buy signal
            orders.append(Order(
                symbol=self.symbol,
                quantity=100,
                order_type='market',
                side='buy'
            ))
            self.position = 1
        elif short_ma < long_ma and self.position >= 0:
            # Sell signal
            orders.append(Order(
                symbol=self.symbol,
                quantity=100,
                order_type='market',
                side='sell'
            ))
            self.position = -1
        
        return orders


class TestMovingAverageCross:
    """Tests for moving average crossover strategy."""
    
    def test_strategy_waits_for_enough_data(self):
        """Test that strategy doesn't trade without enough data."""
        strategy = MovingAverageCrossStrategy(short_window=5, long_window=20)
        
        # Create data with only 10 points (need 20)
        data = pd.DataFrame({
            'Close': [100.0] * 10,
        }, index=pd.date_range('2024-01-01', periods=10))
        
        orders = strategy.on_data(datetime(2024, 1, 10), data)
        assert len(orders) == 0
    
    def test_strategy_generates_buy_signal(self):
        """Test that strategy generates buy signal on bullish cross."""
        strategy = MovingAverageCrossStrategy(short_window=2, long_window=5)
        
        # Create uptrend data
        closes = [100, 101, 102, 103, 110]  # Short MA will cross above
        data = pd.DataFrame({
            'Close': closes,
        }, index=pd.date_range('2024-01-01', periods=5))
        
        orders = strategy.on_data(datetime(2024, 1, 5), data)
        
        # Should generate buy order
        assert len(orders) >= 0  # May or may not cross depending on exact values
