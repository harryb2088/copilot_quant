"""
Tests for Order Execution Handler

These tests use mocking to avoid requiring an actual IBKR connection.
"""

import unittest
from datetime import datetime
from unittest.mock import MagicMock, patch

from copilot_quant.brokers.order_execution_handler import Fill, OrderExecutionHandler, OrderRecord, OrderStatus


class TestOrderStatus(unittest.TestCase):
    """Test OrderStatus enum"""

    def test_order_status_values(self):
        """Test that all expected order statuses exist"""
        self.assertEqual(OrderStatus.PENDING.value, "Pending")
        self.assertEqual(OrderStatus.SUBMITTED.value, "Submitted")
        self.assertEqual(OrderStatus.PARTIALLY_FILLED.value, "PartiallyFilled")
        self.assertEqual(OrderStatus.FILLED.value, "Filled")
        self.assertEqual(OrderStatus.CANCELLED.value, "Cancelled")
        self.assertEqual(OrderStatus.ERROR.value, "Error")


class TestFill(unittest.TestCase):
    """Test Fill dataclass"""

    def test_fill_creation(self):
        """Test creating a Fill"""
        fill = Fill(
            fill_id="fill-123",
            order_id=1,
            symbol="AAPL",
            quantity=100,
            price=150.50,
            timestamp=datetime.now(),
            commission=1.0,
        )

        self.assertEqual(fill.fill_id, "fill-123")
        self.assertEqual(fill.order_id, 1)
        self.assertEqual(fill.symbol, "AAPL")
        self.assertEqual(fill.quantity, 100)
        self.assertEqual(fill.price, 150.50)
        self.assertEqual(fill.commission, 1.0)

    def test_fill_auto_id_generation(self):
        """Test that fill_id is auto-generated if not provided"""
        fill = Fill(fill_id=None, order_id=1, symbol="AAPL", quantity=100, price=150.50, timestamp=datetime.now())

        self.assertIsNotNone(fill.fill_id)
        self.assertTrue(len(fill.fill_id) > 0)


class TestOrderRecord(unittest.TestCase):
    """Test OrderRecord dataclass"""

    def test_order_record_creation(self):
        """Test creating an OrderRecord"""
        record = OrderRecord(order_id=1, symbol="AAPL", action="BUY", total_quantity=100, order_type="MARKET")

        self.assertEqual(record.order_id, 1)
        self.assertEqual(record.symbol, "AAPL")
        self.assertEqual(record.action, "BUY")
        self.assertEqual(record.total_quantity, 100)
        self.assertEqual(record.order_type, "MARKET")
        self.assertEqual(record.status, OrderStatus.PENDING)
        self.assertEqual(record.filled_quantity, 0)
        self.assertEqual(record.remaining_quantity, 100)

    def test_add_fill_complete(self):
        """Test adding a complete fill"""
        record = OrderRecord(order_id=1, symbol="AAPL", action="BUY", total_quantity=100, order_type="MARKET")

        fill = Fill(fill_id="fill-1", order_id=1, symbol="AAPL", quantity=100, price=150.50, timestamp=datetime.now())

        record.add_fill(fill)

        self.assertEqual(record.filled_quantity, 100)
        self.assertEqual(record.remaining_quantity, 0)
        self.assertEqual(record.status, OrderStatus.FILLED)
        self.assertEqual(record.avg_fill_price, 150.50)
        self.assertEqual(len(record.fills), 1)

    def test_add_fill_partial(self):
        """Test adding a partial fill"""
        record = OrderRecord(order_id=1, symbol="AAPL", action="BUY", total_quantity=100, order_type="MARKET")

        fill = Fill(fill_id="fill-1", order_id=1, symbol="AAPL", quantity=50, price=150.50, timestamp=datetime.now())

        record.add_fill(fill)

        self.assertEqual(record.filled_quantity, 50)
        self.assertEqual(record.remaining_quantity, 50)
        self.assertEqual(record.status, OrderStatus.PARTIALLY_FILLED)
        self.assertEqual(record.avg_fill_price, 150.50)

    def test_add_multiple_fills(self):
        """Test adding multiple fills with different prices"""
        record = OrderRecord(order_id=1, symbol="AAPL", action="BUY", total_quantity=100, order_type="MARKET")

        # First partial fill
        fill1 = Fill(fill_id="fill-1", order_id=1, symbol="AAPL", quantity=50, price=150.00, timestamp=datetime.now())
        record.add_fill(fill1)

        self.assertEqual(record.filled_quantity, 50)
        self.assertEqual(record.status, OrderStatus.PARTIALLY_FILLED)
        self.assertEqual(record.avg_fill_price, 150.00)

        # Second partial fill at different price
        fill2 = Fill(fill_id="fill-2", order_id=1, symbol="AAPL", quantity=50, price=151.00, timestamp=datetime.now())
        record.add_fill(fill2)

        self.assertEqual(record.filled_quantity, 100)
        self.assertEqual(record.remaining_quantity, 0)
        self.assertEqual(record.status, OrderStatus.FILLED)
        # Average: (50*150 + 50*151) / 100 = 150.50
        self.assertEqual(record.avg_fill_price, 150.50)

    def test_update_status(self):
        """Test updating order status"""
        record = OrderRecord(order_id=1, symbol="AAPL", action="BUY", total_quantity=100, order_type="MARKET")

        record.update_status(OrderStatus.SUBMITTED)
        self.assertEqual(record.status, OrderStatus.SUBMITTED)
        self.assertIsNone(record.error_message)

        record.update_status(OrderStatus.ERROR, "Connection lost")
        self.assertEqual(record.status, OrderStatus.ERROR)
        self.assertEqual(record.error_message, "Connection lost")

    def test_to_dict(self):
        """Test converting OrderRecord to dictionary"""
        record = OrderRecord(
            order_id=1,
            symbol="AAPL",
            action="BUY",
            total_quantity=100,
            order_type="MARKET",
            status=OrderStatus.SUBMITTED,
        )

        data = record.to_dict()

        self.assertEqual(data["order_id"], 1)
        self.assertEqual(data["symbol"], "AAPL")
        self.assertEqual(data["action"], "BUY")
        self.assertEqual(data["total_quantity"], 100)
        self.assertEqual(data["status"], "Submitted")
        self.assertIn("submission_time", data)
        self.assertIn("last_update_time", data)


class TestOrderExecutionHandler(unittest.TestCase):
    """Test cases for OrderExecutionHandler"""

    def setUp(self):
        """Set up test fixtures"""
        self.handler = OrderExecutionHandler(max_retries=3, initial_retry_delay=1.0, retry_backoff_factor=2.0)

        # Create mock IB connection
        self.mock_ib = MagicMock()

    def _create_mock_contract(self, symbol):
        """Helper to create mock contract"""
        contract = MagicMock()
        contract.symbol = symbol
        return contract

    def _create_mock_order(self, order_id, action, quantity):
        """Helper to create mock order"""
        order = MagicMock()
        order.orderId = order_id
        order.action = action
        order.totalQuantity = quantity
        return order

    def _create_mock_trade(self, order_id, symbol, action, quantity):
        """Helper to create mock trade"""
        trade = MagicMock()
        trade.order = self._create_mock_order(order_id, action, quantity)
        trade.contract = self._create_mock_contract(symbol)
        return trade

    @patch("ib_insync.Stock")
    @patch("ib_insync.MarketOrder")
    def test_submit_market_order_success(self, mock_market_order_class, mock_stock_class):
        """Test successful market order submission"""
        # Setup mocks
        mock_contract = self._create_mock_contract("AAPL")
        mock_stock_class.return_value = mock_contract

        mock_order = self._create_mock_order(1, "BUY", 100)
        mock_market_order_class.return_value = mock_order

        mock_trade = self._create_mock_trade(1, "AAPL", "BUY", 100)
        self.mock_ib.placeOrder.return_value = mock_trade

        # Submit order
        order_record = self.handler.submit_order(
            ib_connection=self.mock_ib, symbol="AAPL", action="BUY", quantity=100, order_type="MARKET"
        )

        # Verify
        self.assertIsNotNone(order_record)
        self.assertEqual(order_record.symbol, "AAPL")
        self.assertEqual(order_record.action, "BUY")
        self.assertEqual(order_record.total_quantity, 100)
        self.assertEqual(order_record.order_type, "MARKET")
        self.assertEqual(order_record.status, OrderStatus.SUBMITTED)

        # Verify IB calls
        self.mock_ib.qualifyContracts.assert_called_once()
        self.mock_ib.placeOrder.assert_called_once()

    @patch("ib_insync.Stock")
    @patch("ib_insync.LimitOrder")
    def test_submit_limit_order_success(self, mock_limit_order_class, mock_stock_class):
        """Test successful limit order submission"""
        # Setup mocks
        mock_contract = self._create_mock_contract("AAPL")
        mock_stock_class.return_value = mock_contract

        mock_order = self._create_mock_order(2, "SELL", 50)
        mock_limit_order_class.return_value = mock_order

        mock_trade = self._create_mock_trade(2, "AAPL", "SELL", 50)
        self.mock_ib.placeOrder.return_value = mock_trade

        # Submit order
        order_record = self.handler.submit_order(
            ib_connection=self.mock_ib,
            symbol="AAPL",
            action="SELL",
            quantity=50,
            order_type="LIMIT",
            limit_price=155.00,
        )

        # Verify
        self.assertIsNotNone(order_record)
        self.assertEqual(order_record.symbol, "AAPL")
        self.assertEqual(order_record.action, "SELL")
        self.assertEqual(order_record.total_quantity, 50)
        self.assertEqual(order_record.order_type, "LIMIT")
        self.assertEqual(order_record.limit_price, 155.00)

    def test_submit_order_duplicate_prevention(self):
        """Test that duplicate orders are prevented"""
        # First submission should succeed
        with patch("ib_insync.Stock"), patch("ib_insync.MarketOrder"):
            mock_trade = self._create_mock_trade(1, "AAPL", "BUY", 100)
            self.mock_ib.placeOrder.return_value = mock_trade

            order1 = self.handler.submit_order(
                ib_connection=self.mock_ib, symbol="AAPL", action="BUY", quantity=100, order_type="MARKET"
            )

            self.assertIsNotNone(order1)

            # Immediate duplicate should be rejected
            order2 = self.handler.submit_order(
                ib_connection=self.mock_ib, symbol="AAPL", action="BUY", quantity=100, order_type="MARKET"
            )

            self.assertIsNone(order2)

    def test_handle_fill_complete(self):
        """Test handling a complete fill"""
        # Create an order first
        order_record = OrderRecord(
            order_id=1,
            symbol="AAPL",
            action="BUY",
            total_quantity=100,
            order_type="MARKET",
            status=OrderStatus.SUBMITTED,
        )
        self.handler._orders[1] = order_record

        # Handle fill
        success = self.handler.handle_fill(order_id=1, quantity=100, price=150.50, commission=1.0)

        self.assertTrue(success)
        self.assertEqual(order_record.filled_quantity, 100)
        self.assertEqual(order_record.status, OrderStatus.FILLED)
        self.assertEqual(len(order_record.fills), 1)

    def test_handle_fill_partial(self):
        """Test handling partial fills"""
        # Create an order first
        order_record = OrderRecord(
            order_id=1,
            symbol="AAPL",
            action="BUY",
            total_quantity=100,
            order_type="MARKET",
            status=OrderStatus.SUBMITTED,
        )
        self.handler._orders[1] = order_record

        # First partial fill
        success1 = self.handler.handle_fill(order_id=1, quantity=50, price=150.00)

        self.assertTrue(success1)
        self.assertEqual(order_record.filled_quantity, 50)
        self.assertEqual(order_record.status, OrderStatus.PARTIALLY_FILLED)

        # Second partial fill
        success2 = self.handler.handle_fill(order_id=1, quantity=50, price=151.00)

        self.assertTrue(success2)
        self.assertEqual(order_record.filled_quantity, 100)
        self.assertEqual(order_record.status, OrderStatus.FILLED)
        self.assertEqual(len(order_record.fills), 2)

    def test_handle_error(self):
        """Test handling order errors"""
        # Create an order first
        order_record = OrderRecord(
            order_id=1,
            symbol="AAPL",
            action="BUY",
            total_quantity=100,
            order_type="MARKET",
            status=OrderStatus.SUBMITTED,
        )
        self.handler._orders[1] = order_record

        # Handle error
        success = self.handler.handle_error(order_id=1, error_code=201, error_message="Order rejected")

        self.assertTrue(success)
        self.assertEqual(order_record.status, OrderStatus.ERROR)
        self.assertIn("Order rejected", order_record.error_message)
        # Retry is scheduled, so retry_count should be incremented
        self.assertEqual(order_record.retry_count, 1)

    def test_callbacks_fill(self):
        """Test fill callbacks are triggered"""
        callback_called = []

        def fill_callback(record):
            callback_called.append(record)

        self.handler.register_fill_callback(fill_callback)

        # Create order and handle fill
        order_record = OrderRecord(order_id=1, symbol="AAPL", action="BUY", total_quantity=100, order_type="MARKET")
        self.handler._orders[1] = order_record

        self.handler.handle_fill(1, 100, 150.50)

        self.assertEqual(len(callback_called), 1)
        self.assertEqual(callback_called[0].order_id, 1)

    def test_callbacks_error(self):
        """Test error callbacks are triggered"""
        callback_called = []

        def error_callback(record, message):
            callback_called.append((record, message))

        self.handler.register_error_callback(error_callback)

        # Create order and handle error
        order_record = OrderRecord(order_id=1, symbol="AAPL", action="BUY", total_quantity=100, order_type="MARKET")
        self.handler._orders[1] = order_record

        self.handler.handle_error(1, 201, "Order rejected")

        self.assertEqual(len(callback_called), 1)
        self.assertEqual(callback_called[0][0].order_id, 1)
        self.assertIn("Order rejected", callback_called[0][1])

    def test_get_order(self):
        """Test getting order by ID"""
        order_record = OrderRecord(order_id=1, symbol="AAPL", action="BUY", total_quantity=100, order_type="MARKET")
        self.handler._orders[1] = order_record

        retrieved = self.handler.get_order(1)
        self.assertIsNotNone(retrieved)
        self.assertEqual(retrieved.order_id, 1)

        not_found = self.handler.get_order(999)
        self.assertIsNone(not_found)

    def test_get_all_orders(self):
        """Test getting all orders"""
        order1 = OrderRecord(order_id=1, symbol="AAPL", action="BUY", total_quantity=100, order_type="MARKET")
        order2 = OrderRecord(
            order_id=2, symbol="GOOGL", action="SELL", total_quantity=50, order_type="LIMIT", limit_price=140.0
        )

        self.handler._orders[1] = order1
        self.handler._orders[2] = order2

        all_orders = self.handler.get_all_orders()
        self.assertEqual(len(all_orders), 2)

    def test_get_active_orders(self):
        """Test getting only active orders"""
        order1 = OrderRecord(
            order_id=1,
            symbol="AAPL",
            action="BUY",
            total_quantity=100,
            order_type="MARKET",
            status=OrderStatus.SUBMITTED,
        )
        order2 = OrderRecord(
            order_id=2, symbol="GOOGL", action="SELL", total_quantity=50, order_type="MARKET", status=OrderStatus.FILLED
        )
        order3 = OrderRecord(
            order_id=3,
            symbol="MSFT",
            action="BUY",
            total_quantity=75,
            order_type="MARKET",
            status=OrderStatus.CANCELLED,
        )

        self.handler._orders[1] = order1
        self.handler._orders[2] = order2
        self.handler._orders[3] = order3

        active_orders = self.handler.get_active_orders()
        self.assertEqual(len(active_orders), 1)
        self.assertEqual(active_orders[0].order_id, 1)

    @patch("copilot_quant.brokers.order_execution_handler.Trade")
    def test_update_order_status(self, mock_trade_class):
        """Test updating order status from Trade object"""
        # Create order
        order_record = OrderRecord(
            order_id=1, symbol="AAPL", action="BUY", total_quantity=100, order_type="MARKET", status=OrderStatus.PENDING
        )
        self.handler._orders[1] = order_record

        # Create mock trade with status
        mock_trade = MagicMock()
        mock_trade.order.orderId = 1
        mock_trade.orderStatus.status = "Submitted"

        self.handler.update_order_status(1, mock_trade)

        self.assertEqual(order_record.status, OrderStatus.SUBMITTED)


if __name__ == "__main__":
    unittest.main()
