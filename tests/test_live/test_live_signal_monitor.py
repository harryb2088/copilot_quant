"""
Tests for Live Signal Monitor

These tests verify signal monitoring and execution functionality.
"""

import unittest
from datetime import datetime
from unittest.mock import Mock, MagicMock, patch
import pandas as pd

from copilot_quant.live.live_signal_monitor import LiveSignalMonitor
from copilot_quant.backtest.signals import TradingSignal, SignalBasedStrategy


class MockSignalStrategy(SignalBasedStrategy):
    """Mock signal-based strategy for testing"""
    
    def __init__(self, name="MockStrategy"):
        super().__init__()
        self.name = name
        self.signals_to_return = []
        self.initialize_called = False
        self.finalize_called = False
    
    def generate_signals(self, timestamp, data):
        return self.signals_to_return
    
    def initialize(self):
        self.initialize_called = True
    
    def finalize(self):
        self.finalize_called = True


class MockDataFeedAdapter:
    """Mock data feed adapter for testing"""
    
    def __init__(self):
        self.connected = True
        self.subscribed_symbols = set()
        self.historical_data = {}
    
    def connect(self, timeout=30, retry_count=3):
        return self.connected
    
    def disconnect(self):
        self.connected = False
    
    def is_connected(self):
        return self.connected
    
    def subscribe(self, symbols):
        self.subscribed_symbols.update(symbols)
        return {s: True for s in symbols}
    
    def unsubscribe(self, symbols):
        for symbol in symbols:
            self.subscribed_symbols.discard(symbol)
    
    def get_historical_data(self, symbol, start_date, end_date, interval):
        if symbol in self.historical_data:
            return self.historical_data[symbol]
        # Return empty DataFrame
        return pd.DataFrame()
    
    def get_latest_price(self, symbol):
        return 150.0  # Fixed price for testing


class MockBrokerAdapter:
    """Mock broker adapter for testing"""
    
    def __init__(self):
        self.connected = True
        self.account_value = 100000.0
        self.cash_balance = 50000.0
        self.positions = {}
        self.executed_orders = []
    
    def connect(self, timeout=30, retry_count=3):
        return self.connected
    
    def disconnect(self):
        self.connected = False
    
    def is_connected(self):
        return self.connected
    
    def get_account_value(self):
        return self.account_value
    
    def get_cash_balance(self):
        return self.cash_balance
    
    def get_positions(self):
        return self.positions
    
    def execute_order(self, order, price, timestamp):
        from copilot_quant.backtest.orders import Fill
        self.executed_orders.append(order)
        # Return a mock fill
        return Fill(
            fill_id=f"fill_{len(self.executed_orders)}",
            symbol=order.symbol,
            quantity=order.quantity,
            price=price,
            commission=0.0,
            timestamp=timestamp
        )


class TestLiveSignalMonitor(unittest.TestCase):
    """Test LiveSignalMonitor class"""
    
    def setUp(self):
        """Set up test fixtures"""
        with patch('copilot_quant.live.live_signal_monitor.TradeDatabase'):
            with patch('copilot_quant.live.live_signal_monitor.LiveDataFeedAdapter', return_value=MockDataFeedAdapter()):
                with patch('copilot_quant.live.live_signal_monitor.LiveBrokerAdapter', return_value=MockBrokerAdapter()):
                    self.monitor = LiveSignalMonitor(
                        database_url="sqlite:///:memory:",
                        paper_trading=True,
                        update_interval=1.0
                    )
                    
                    # Replace adapters with mocks
                    self.monitor.data_feed = MockDataFeedAdapter()
                    self.monitor.broker = MockBrokerAdapter()
    
    def test_initialization(self):
        """Test monitor initialization"""
        self.assertIsNotNone(self.monitor)
        self.assertEqual(self.monitor.update_interval, 1.0)
        self.assertFalse(self.monitor._running)
        self.assertEqual(len(self.monitor.strategies), 0)
    
    def test_add_strategy_success(self):
        """Test adding a valid signal-based strategy"""
        strategy = MockSignalStrategy()
        self.monitor.add_strategy(strategy)
        
        self.assertEqual(len(self.monitor.strategies), 1)
        self.assertEqual(self.monitor.strategies[0], strategy)
    
    def test_add_strategy_invalid(self):
        """Test adding an invalid strategy"""
        from copilot_quant.backtest.strategy import Strategy
        
        class InvalidStrategy(Strategy):
            def on_data(self, timestamp, data):
                return []
        
        with self.assertRaises(ValueError):
            self.monitor.add_strategy(InvalidStrategy())
    
    def test_connect_success(self):
        """Test successful connection"""
        result = self.monitor.connect()
        
        self.assertTrue(result)
        self.assertTrue(self.monitor.is_connected())
    
    def test_connect_failure(self):
        """Test connection failure"""
        self.monitor.data_feed.connected = False
        result = self.monitor.connect()
        
        self.assertFalse(result)
    
    def test_is_connected(self):
        """Test connection status check"""
        self.assertTrue(self.monitor.is_connected())
        
        self.monitor.broker.connected = False
        self.assertFalse(self.monitor.is_connected())
    
    def test_generate_all_signals(self):
        """Test signal generation from multiple strategies"""
        strategy1 = MockSignalStrategy("Strategy1")
        strategy2 = MockSignalStrategy("Strategy2")
        
        signal1 = TradingSignal(
            symbol='AAPL',
            side='buy',
            confidence=0.8,
            sharpe_estimate=1.5,
            entry_price=150.0,
            strategy_name='Strategy1'
        )
        
        signal2 = TradingSignal(
            symbol='MSFT',
            side='buy',
            confidence=0.7,
            sharpe_estimate=1.2,
            entry_price=250.0,
            strategy_name='Strategy2'
        )
        
        strategy1.signals_to_return = [signal1]
        strategy2.signals_to_return = [signal2]
        
        self.monitor.add_strategy(strategy1)
        self.monitor.add_strategy(strategy2)
        
        timestamp = datetime.now()
        data = pd.DataFrame()
        
        signals = self.monitor._generate_all_signals(timestamp, data)
        
        self.assertEqual(len(signals), 2)
        self.assertIn(signal1, signals)
        self.assertIn(signal2, signals)
    
    def test_risk_check_pass(self):
        """Test risk check passing"""
        signal = TradingSignal(
            symbol='AAPL',
            side='buy',
            confidence=0.8,
            sharpe_estimate=1.5,
            entry_price=150.0
        )
        
        result = self.monitor._risk_check(signal)
        
        self.assertTrue(result)
    
    def test_risk_check_low_quality(self):
        """Test risk check failing due to low quality"""
        signal = TradingSignal(
            symbol='AAPL',
            side='buy',
            confidence=0.2,  # Low confidence
            sharpe_estimate=0.5,  # Low Sharpe
            entry_price=150.0
        )
        
        result = self.monitor._risk_check(signal)
        
        self.assertFalse(result)
    
    def test_calculate_position_size(self):
        """Test position size calculation"""
        signal = TradingSignal(
            symbol='AAPL',
            side='buy',
            confidence=0.8,
            sharpe_estimate=1.5,
            entry_price=150.0
        )
        
        quantity = self.monitor._calculate_position_size(signal)
        
        self.assertGreater(quantity, 0)
        self.assertIsInstance(quantity, int)
    
    def test_get_dashboard_summary(self):
        """Test getting dashboard summary"""
        summary = self.monitor.get_dashboard_summary()
        
        self.assertIsInstance(summary, dict)
        self.assertIn('is_running', summary)
        self.assertIn('is_connected', summary)
        self.assertIn('num_strategies', summary)
        self.assertIn('stats', summary)
        self.assertIn('account_value', summary)
    
    def test_disconnect(self):
        """Test disconnection"""
        self.monitor.disconnect()
        
        self.assertFalse(self.monitor.data_feed.is_connected())
        self.assertFalse(self.monitor.broker.is_connected())


class TestTradingSignalProcessing(unittest.TestCase):
    """Test signal processing logic"""
    
    def setUp(self):
        """Set up test fixtures"""
        with patch('copilot_quant.live.live_signal_monitor.TradeDatabase'):
            with patch('copilot_quant.live.live_signal_monitor.LiveDataFeedAdapter', return_value=MockDataFeedAdapter()):
                with patch('copilot_quant.live.live_signal_monitor.LiveBrokerAdapter', return_value=MockBrokerAdapter()):
                    self.monitor = LiveSignalMonitor(
                        database_url="sqlite:///:memory:",
                        paper_trading=True
                    )
                    self.monitor.data_feed = MockDataFeedAdapter()
                    self.monitor.broker = MockBrokerAdapter()
    
    def test_process_signal_execution(self):
        """Test signal processing and execution"""
        signal = TradingSignal(
            symbol='AAPL',
            side='buy',
            confidence=0.8,
            sharpe_estimate=1.5,
            entry_price=150.0,
            strategy_name='TestStrategy'
        )
        
        self.monitor._process_signal(signal, datetime.now())
        
        # Verify signal was added to history
        self.assertEqual(len(self.monitor.signal_history), 1)
        self.assertEqual(self.monitor.signal_history[0]['symbol'], 'AAPL')
    
    def test_process_signal_rejection(self):
        """Test signal rejection"""
        signal = TradingSignal(
            symbol='AAPL',
            side='buy',
            confidence=0.1,  # Too low
            sharpe_estimate=0.5,
            entry_price=150.0
        )
        
        self.monitor._process_signal(signal, datetime.now())
        
        # Should be rejected
        self.assertEqual(self.monitor.stats['signals_rejected'], 1)
        self.assertEqual(self.monitor.stats['signals_executed'], 0)


if __name__ == '__main__':
    unittest.main()
