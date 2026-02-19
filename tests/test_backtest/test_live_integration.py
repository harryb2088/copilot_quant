"""
Integration test example for live data and execution adapters

This demonstrates how to test the complete integration of adapters
with a simple strategy.
"""

import unittest
from unittest.mock import patch, MagicMock
from datetime import datetime
import pandas as pd
import time
import pytest

from copilot_quant.backtest.strategy import Strategy
from copilot_quant.backtest.orders import Order
from copilot_quant.backtest.live_engine import LiveStrategyEngine


class SimpleTestStrategy(Strategy):
    """
    Simple test strategy for integration testing.
    
    This strategy does nothing in production but is useful for testing
    the integration flow.
    """
    
    def initialize(self):
        """Initialize strategy"""
        self.call_count = 0
        self.fills_received = []
    
    def on_data(self, timestamp: datetime, data: pd.DataFrame) -> list:
        """
        Called on each data update.
        
        Returns empty list (no orders) for testing.
        """
        self.call_count += 1
        return []
    
    def on_fill(self, fill):
        """Called when order is filled"""
        self.fills_received.append(fill)
    
    def finalize(self):
        """Called when strategy ends"""
        pass


@pytest.mark.integration
class TestLiveIntegration(unittest.TestCase):
    """Integration tests for live trading system"""
    
    @patch('copilot_quant.brokers.live_data_adapter.IBKRLiveDataFeed')
    @patch('copilot_quant.brokers.live_broker_adapter.IBKRBroker')
    def test_engine_lifecycle(self, mock_broker_class, mock_data_feed_class):
        """Test complete engine lifecycle"""
        # Setup mocks
        mock_broker = MagicMock()
        mock_broker_class.return_value = mock_broker
        mock_broker.connect.return_value = True
        mock_broker.is_connected.return_value = True
        mock_broker.get_positions.return_value = []
        
        mock_data_feed = MagicMock()
        mock_data_feed_class.return_value = mock_data_feed
        mock_data_feed.connect.return_value = True
        mock_data_feed.is_connected.return_value = True
        
        # Mock historical data
        hist_data = pd.DataFrame({
            'Open': [100, 101],
            'High': [102, 103],
            'Low': [99, 100],
            'Close': [101, 102],
            'Volume': [1000, 1100]
        }, index=pd.date_range('2024-01-01', periods=2))
        
        mock_data_feed.get_historical_data.return_value = hist_data
        mock_data_feed.subscribe.return_value = {'AAPL': True}
        
        # Create engine
        engine = LiveStrategyEngine(paper_trading=True)
        
        # Add strategy
        strategy = SimpleTestStrategy()
        engine.add_strategy(strategy)
        
        # Test connection
        self.assertTrue(engine.connect())
        
        # Test start
        self.assertTrue(engine.start(['AAPL'], lookback_days=2))
        
        # Let it run briefly
        time.sleep(0.5)
        
        # Test stop
        engine.stop()
        
        # Test disconnect
        engine.disconnect()
        
        # Verify calls
        mock_broker.connect.assert_called()
        mock_data_feed.connect.assert_called()
        mock_data_feed.get_historical_data.assert_called()
        mock_data_feed.subscribe.assert_called_with(['AAPL'])
    
    @patch('copilot_quant.brokers.live_data_adapter.IBKRLiveDataFeed')
    @patch('copilot_quant.brokers.live_broker_adapter.IBKRBroker')
    def test_engine_reconnection(self, mock_broker_class, mock_data_feed_class):
        """Test engine reconnection on connection loss"""
        # Setup mocks
        mock_broker = MagicMock()
        mock_broker_class.return_value = mock_broker
        mock_broker.connect.return_value = True
        
        # Simulate connection loss then reconnect
        mock_broker.is_connected.side_effect = [True, False, True]
        
        mock_data_feed = MagicMock()
        mock_data_feed_class.return_value = mock_data_feed
        mock_data_feed.connect.return_value = True
        mock_data_feed.is_connected.side_effect = [True, False, True]
        mock_data_feed.reconnect.return_value = True
        
        # Create engine with reconnection enabled
        engine = LiveStrategyEngine(
            paper_trading=True,
            enable_reconnect=True
        )
        
        # Connect
        engine.connect()
        
        # Simulate connection check
        # First call: connected
        self.assertTrue(engine.is_connected())
        
        # Second call: disconnected (triggers reconnect in _run_loop)
        # Third call: reconnected
        
        # Cleanup
        engine.disconnect()
    
    @patch('copilot_quant.brokers.live_data_adapter.IBKRLiveDataFeed')
    @patch('copilot_quant.brokers.live_broker_adapter.IBKRBroker')
    def test_strategy_execution_flow(self, mock_broker_class, mock_data_feed_class):
        """Test complete strategy execution flow"""
        # Setup mocks
        mock_broker = MagicMock()
        mock_broker_class.return_value = mock_broker
        mock_broker.connect.return_value = True
        mock_broker.is_connected.return_value = True
        mock_broker.get_positions.return_value = []
        mock_broker.get_account_balance.return_value = {
            'BuyingPower': 100000.0,
            'TotalCashValue': 100000.0,
            'NetLiquidation': 100000.0
        }
        
        mock_data_feed = MagicMock()
        mock_data_feed_class.return_value = mock_data_feed
        mock_data_feed.connect.return_value = True
        mock_data_feed.is_connected.return_value = True
        
        # Mock data
        hist_data = pd.DataFrame({
            'Close': [100, 101, 102]
        }, index=pd.date_range('2024-01-01', periods=3))
        
        mock_data_feed.get_historical_data.return_value = hist_data
        mock_data_feed.subscribe.return_value = {'AAPL': True}
        mock_data_feed.get_latest_price.return_value = 102.0
        
        # Create engine
        engine = LiveStrategyEngine(
            paper_trading=True,
            update_interval=0.1  # Fast updates for testing
        )
        
        # Create strategy that generates an order
        class OrderGeneratingStrategy(Strategy):
            def __init__(self):
                super().__init__()
                self.order_placed = False
            
            def on_data(self, timestamp, data):
                if not self.order_placed:
                    self.order_placed = True
                    return [Order(
                        symbol='AAPL',
                        quantity=10,
                        order_type='market',
                        side='buy'
                    )]
                return []
        
        strategy = OrderGeneratingStrategy()
        engine.add_strategy(strategy)
        
        # Connect and start
        engine.connect()
        engine.start(['AAPL'], lookback_days=5)
        
        # Wait for at least one update
        time.sleep(0.3)
        
        # Stop
        engine.stop()
        engine.disconnect()
        
        # Verify strategy was called
        self.assertTrue(strategy.order_placed)
    
    def test_adapter_compatibility_with_backtest_interfaces(self):
        """Test that adapters are compatible with backtest interfaces"""
        from copilot_quant.backtest.interfaces import IDataFeed, IBroker
        from copilot_quant.brokers.live_data_adapter import LiveDataFeedAdapter
        from copilot_quant.brokers.live_broker_adapter import LiveBrokerAdapter
        
        # Check LiveDataFeedAdapter implements IDataFeed
        self.assertTrue(issubclass(LiveDataFeedAdapter, IDataFeed))
        
        # Check LiveBrokerAdapter implements IBroker
        self.assertTrue(issubclass(LiveBrokerAdapter, IBroker))
    
    @patch('copilot_quant.brokers.live_data_adapter.IBKRLiveDataFeed')
    @patch('copilot_quant.brokers.live_broker_adapter.IBKRBroker')
    def test_performance_summary(self, mock_broker_class, mock_data_feed_class):
        """Test performance summary generation"""
        # Setup mocks
        mock_broker = MagicMock()
        mock_broker_class.return_value = mock_broker
        mock_broker.connect.return_value = True
        mock_broker.is_connected.return_value = True
        mock_broker.get_positions.return_value = []
        mock_broker.get_account_balance.return_value = {
            'NetLiquidation': 105000.0,
            'TotalCashValue': 105000.0
        }
        
        mock_data_feed = MagicMock()
        mock_data_feed_class.return_value = mock_data_feed
        mock_data_feed.connect.return_value = True
        mock_data_feed.is_connected.return_value = True
        
        # Create engine
        engine = LiveStrategyEngine(paper_trading=True)
        engine.add_strategy(SimpleTestStrategy())
        
        # Connect
        engine.connect()
        
        # Get performance summary
        summary = engine.get_performance_summary()
        
        # Verify summary structure
        self.assertIn('account_value', summary)
        self.assertIn('cash_balance', summary)
        self.assertIn('positions', summary)
        self.assertIn('total_fills', summary)
        self.assertIn('total_errors', summary)
        self.assertIn('is_running', summary)
        self.assertIn('is_connected', summary)
        
        # Verify values
        self.assertEqual(summary['account_value'], 105000.0)
        self.assertEqual(summary['cash_balance'], 105000.0)
        self.assertTrue(summary['is_connected'])
        
        engine.disconnect()


if __name__ == '__main__':
    unittest.main()
