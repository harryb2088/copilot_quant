"""
Unit tests for LiveBrokerAdapter

Tests the adapter implementation that bridges IBroker interface
with IBKR live broker.
"""

import unittest
from unittest.mock import Mock, MagicMock, patch
from datetime import datetime
import uuid

from copilot_quant.brokers.live_broker_adapter import LiveBrokerAdapter
from copilot_quant.backtest.orders import Order, Fill, Position


class TestLiveBrokerAdapter(unittest.TestCase):
    """Test suite for LiveBrokerAdapter"""
    
    def setUp(self):
        """Set up test fixtures"""
        # Mock the underlying IBKRBroker
        self.mock_broker_patcher = patch('copilot_quant.brokers.live_broker_adapter.IBKRBroker')
        self.mock_broker_class = self.mock_broker_patcher.start()
        self.mock_broker = MagicMock()
        self.mock_broker_class.return_value = self.mock_broker
        
        # Create adapter instance
        self.adapter = LiveBrokerAdapter(
            paper_trading=True,
            commission_rate=0.001,
            slippage_rate=0.0005
        )
    
    def tearDown(self):
        """Clean up test fixtures"""
        self.mock_broker_patcher.stop()
    
    def test_initialization(self):
        """Test adapter initialization"""
        self.assertIsNotNone(self.adapter)
        self.assertEqual(self.adapter.commission_rate, 0.001)
        self.assertEqual(self.adapter.slippage_rate, 0.0005)
        self.assertTrue(self.adapter.enable_position_tracking)
    
    def test_connect_success(self):
        """Test successful connection"""
        self.mock_broker.connect.return_value = True
        self.mock_broker.get_positions.return_value = []
        
        result = self.adapter.connect(timeout=30, retry_count=3)
        
        self.assertTrue(result)
        self.mock_broker.connect.assert_called_once_with(timeout=30, retry_count=3)
    
    def test_connect_syncs_positions(self):
        """Test that connect syncs positions from IBKR"""
        self.mock_broker.connect.return_value = True
        self.mock_broker.get_positions.return_value = [
            {
                'symbol': 'AAPL',
                'position': 100,
                'avg_cost': 150.0
            }
        ]
        
        self.adapter.connect()
        
        # Check position was synced
        position = self.adapter.get_position('AAPL')
        self.assertIsNotNone(position)
        self.assertEqual(position.quantity, 100)
        self.assertEqual(position.avg_entry_price, 150.0)
    
    def test_is_connected(self):
        """Test connection status check"""
        self.mock_broker.is_connected.return_value = True
        
        result = self.adapter.is_connected()
        
        self.assertTrue(result)
    
    def test_execute_market_order_buy(self):
        """Test executing market buy order"""
        # Setup
        order = Order(
            symbol='AAPL',
            quantity=10,
            order_type='market',
            side='buy'
        )
        
        mock_order_record = MagicMock()
        mock_order_record.order_id = 123
        
        self.mock_broker.is_connected.return_value = True
        self.mock_broker.get_account_balance.return_value = {
            'BuyingPower': 100000.0
        }
        self.mock_broker.execute_market_order.return_value = mock_order_record
        
        # Execute
        fill = self.adapter.execute_order(order, 150.0, datetime.now())
        
        # Verify
        self.assertIsNotNone(fill)
        self.assertEqual(fill.order.symbol, 'AAPL')
        self.assertEqual(fill.fill_quantity, 10)
        self.assertGreater(fill.fill_price, 150.0)  # Should include slippage
        self.assertGreater(fill.commission, 0)
    
    def test_execute_market_order_sell(self):
        """Test executing market sell order"""
        # Setup position first
        self.adapter._positions['AAPL'] = Position(symbol='AAPL')
        self.adapter._positions['AAPL'].quantity = 20
        
        order = Order(
            symbol='AAPL',
            quantity=10,
            order_type='market',
            side='sell'
        )
        
        mock_order_record = MagicMock()
        self.mock_broker.is_connected.return_value = True
        self.mock_broker.execute_market_order.return_value = mock_order_record
        
        # Execute
        fill = self.adapter.execute_order(order, 150.0, datetime.now())
        
        # Verify
        self.assertIsNotNone(fill)
        self.assertLess(fill.fill_price, 150.0)  # Should include negative slippage
    
    def test_execute_limit_order(self):
        """Test executing limit order"""
        order = Order(
            symbol='AAPL',
            quantity=10,
            order_type='limit',
            side='buy',
            limit_price=149.0
        )
        
        mock_order_record = MagicMock()
        mock_order_record.order_id = 124
        
        self.mock_broker.is_connected.return_value = True
        self.mock_broker.get_account_balance.return_value = {
            'BuyingPower': 100000.0
        }
        self.mock_broker.execute_limit_order.return_value = mock_order_record
        
        # Execute (limit orders return None until filled)
        fill = self.adapter.execute_order(order, 150.0, datetime.now())
        
        # Limit order submitted but not immediately filled
        self.assertIsNone(fill)
        self.mock_broker.execute_limit_order.assert_called_once()
    
    def test_execute_order_not_connected(self):
        """Test executing order when not connected"""
        self.mock_broker.is_connected.return_value = False
        
        order = Order(symbol='AAPL', quantity=10, order_type='market', side='buy')
        fill = self.adapter.execute_order(order, 150.0, datetime.now())
        
        self.assertIsNone(fill)
    
    def test_execute_order_insufficient_buying_power(self):
        """Test order rejected due to insufficient buying power"""
        order = Order(symbol='AAPL', quantity=1000, order_type='market', side='buy')
        
        self.mock_broker.is_connected.return_value = True
        self.mock_broker.get_account_balance.return_value = {
            'BuyingPower': 1000.0  # Not enough for 1000 shares @ 150
        }
        
        fill = self.adapter.execute_order(order, 150.0, datetime.now())
        
        self.assertIsNone(fill)
    
    def test_execute_order_insufficient_position_for_sell(self):
        """Test sell order rejected due to insufficient position"""
        order = Order(symbol='AAPL', quantity=100, order_type='market', side='sell')
        
        self.mock_broker.is_connected.return_value = True
        # No position exists
        
        fill = self.adapter.execute_order(order, 150.0, datetime.now())
        
        self.assertIsNone(fill)
    
    def test_check_buying_power_buy_sufficient(self):
        """Test buying power check for buy order with sufficient funds"""
        order = Order(symbol='AAPL', quantity=10, order_type='market', side='buy')
        
        self.mock_broker.is_connected.return_value = True
        self.mock_broker.get_account_balance.return_value = {
            'BuyingPower': 10000.0
        }
        
        result = self.adapter.check_buying_power(order, 150.0)
        
        self.assertTrue(result)
    
    def test_check_buying_power_buy_insufficient(self):
        """Test buying power check for buy order with insufficient funds"""
        order = Order(symbol='AAPL', quantity=100, order_type='market', side='buy')
        
        self.mock_broker.is_connected.return_value = True
        self.mock_broker.get_account_balance.return_value = {
            'BuyingPower': 1000.0
        }
        
        result = self.adapter.check_buying_power(order, 150.0)
        
        self.assertFalse(result)
    
    def test_check_buying_power_sell_sufficient_position(self):
        """Test buying power check for sell with sufficient position"""
        # Setup position
        self.adapter._positions['AAPL'] = Position(symbol='AAPL')
        self.adapter._positions['AAPL'].quantity = 20
        
        order = Order(symbol='AAPL', quantity=10, order_type='market', side='sell')
        
        self.mock_broker.is_connected.return_value = True
        
        result = self.adapter.check_buying_power(order, 150.0)
        
        self.assertTrue(result)
    
    def test_check_buying_power_sell_insufficient_position(self):
        """Test buying power check for sell with insufficient position"""
        # Setup position
        self.adapter._positions['AAPL'] = Position(symbol='AAPL')
        self.adapter._positions['AAPL'].quantity = 5
        
        order = Order(symbol='AAPL', quantity=10, order_type='market', side='sell')
        
        self.mock_broker.is_connected.return_value = True
        
        result = self.adapter.check_buying_power(order, 150.0)
        
        self.assertFalse(result)
    
    def test_calculate_commission(self):
        """Test commission calculation"""
        commission = self.adapter.calculate_commission(150.0, 10)
        
        # 150 * 10 * 0.001 = 1.50
        self.assertGreaterEqual(commission, 1.0)  # At least minimum
        self.assertAlmostEqual(commission, 1.50, places=2)
    
    def test_calculate_commission_minimum(self):
        """Test minimum commission is applied"""
        commission = self.adapter.calculate_commission(1.0, 1)
        
        # Commission would be 0.001, but minimum is 1.0
        self.assertEqual(commission, 1.0)
    
    def test_calculate_slippage_buy(self):
        """Test slippage calculation for buy order"""
        order = Order(symbol='AAPL', quantity=10, order_type='market', side='buy')
        
        fill_price = self.adapter.calculate_slippage(order, 150.0)
        
        # Buy orders pay slippage (higher price)
        expected = 150.0 * (1 + 0.0005)
        self.assertAlmostEqual(fill_price, expected, places=2)
    
    def test_calculate_slippage_sell(self):
        """Test slippage calculation for sell order"""
        order = Order(symbol='AAPL', quantity=10, order_type='market', side='sell')
        
        fill_price = self.adapter.calculate_slippage(order, 150.0)
        
        # Sell orders receive less (lower price)
        expected = 150.0 * (1 - 0.0005)
        self.assertAlmostEqual(fill_price, expected, places=2)
    
    def test_get_positions(self):
        """Test getting all positions"""
        # Setup positions
        self.adapter._positions['AAPL'] = Position(symbol='AAPL')
        self.adapter._positions['MSFT'] = Position(symbol='MSFT')
        
        positions = self.adapter.get_positions()
        
        self.assertEqual(len(positions), 2)
        self.assertIn('AAPL', positions)
        self.assertIn('MSFT', positions)
    
    def test_get_position(self):
        """Test getting specific position"""
        # Setup position
        self.adapter._positions['AAPL'] = Position(symbol='AAPL')
        self.adapter._positions['AAPL'].quantity = 100
        
        position = self.adapter.get_position('AAPL')
        
        self.assertIsNotNone(position)
        self.assertEqual(position.quantity, 100)
    
    def test_get_position_not_exists(self):
        """Test getting position that doesn't exist"""
        position = self.adapter.get_position('AAPL')
        
        self.assertIsNone(position)
    
    def test_get_cash_balance(self):
        """Test getting cash balance"""
        self.mock_broker.is_connected.return_value = True
        self.mock_broker.get_account_balance.return_value = {
            'TotalCashValue': 50000.0
        }
        
        cash = self.adapter.get_cash_balance()
        
        self.assertEqual(cash, 50000.0)
    
    def test_get_cash_balance_not_connected(self):
        """Test getting cash balance when not connected"""
        self.mock_broker.is_connected.return_value = False
        
        cash = self.adapter.get_cash_balance()
        
        self.assertEqual(cash, 0.0)
    
    def test_get_account_value(self):
        """Test getting total account value"""
        self.mock_broker.is_connected.return_value = True
        self.mock_broker.get_account_balance.return_value = {
            'NetLiquidation': 100000.0
        }
        
        value = self.adapter.get_account_value()
        
        self.assertEqual(value, 100000.0)
    
    def test_sync_positions(self):
        """Test syncing positions from IBKR"""
        self.mock_broker.is_connected.return_value = True
        self.mock_broker.get_positions.return_value = [
            {
                'symbol': 'AAPL',
                'position': 100,
                'avg_cost': 150.0
            },
            {
                'symbol': 'MSFT',
                'position': 50,
                'avg_cost': 300.0
            }
        ]
        
        self.adapter._sync_positions()
        
        # Check positions were synced
        self.assertEqual(len(self.adapter._positions), 2)
        self.assertIn('AAPL', self.adapter._positions)
        self.assertIn('MSFT', self.adapter._positions)
        
        aapl_pos = self.adapter._positions['AAPL']
        self.assertEqual(aapl_pos.quantity, 100)
        self.assertEqual(aapl_pos.avg_entry_price, 150.0)
    
    def test_update_position_from_fill(self):
        """Test updating position from fill"""
        order = Order(symbol='AAPL', quantity=10, order_type='market', side='buy')
        fill = Fill(
            order=order,
            fill_price=150.0,
            fill_quantity=10,
            commission=1.5,
            timestamp=datetime.now(),
            fill_id=str(uuid.uuid4())
        )
        
        self.adapter._update_position_from_fill(fill, 150.0)
        
        # Check position was created/updated
        position = self.adapter._positions.get('AAPL')
        self.assertIsNotNone(position)
    
    def test_register_fill_callback(self):
        """Test registering fill callback"""
        callback = Mock()
        
        self.adapter.register_fill_callback(callback)
        
        # Verify it was registered with underlying broker
        self.mock_broker.register_order_fill_callback.assert_called_once_with(callback)
    
    def test_register_error_callback(self):
        """Test registering error callback"""
        callback = Mock()
        
        self.adapter.register_error_callback(callback)
        
        # Verify it was registered with underlying broker
        self.mock_broker.register_order_error_callback.assert_called_once_with(callback)
    
    def test_disconnect(self):
        """Test disconnection"""
        self.adapter.disconnect()
        
        self.mock_broker.disconnect.assert_called_once()
    
    def test_context_manager(self):
        """Test using adapter as context manager"""
        self.mock_broker.connect.return_value = True
        self.mock_broker.get_positions.return_value = []
        
        with self.adapter as adapter:
            self.assertIsNotNone(adapter)
        
        self.mock_broker.connect.assert_called()
        self.mock_broker.disconnect.assert_called()


if __name__ == '__main__':
    unittest.main()
