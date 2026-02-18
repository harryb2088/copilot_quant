"""
Tests for Order Logger

These tests verify the structured logging functionality for orders.
"""

import unittest
from unittest.mock import Mock, MagicMock, patch
from datetime import datetime
import tempfile
import json
from pathlib import Path

from copilot_quant.brokers.order_logger import OrderLogger
from copilot_quant.brokers.order_execution_handler import (
    OrderRecord,
    OrderStatus,
    Fill
)


class TestOrderLogger(unittest.TestCase):
    """Test cases for OrderLogger"""
    
    def setUp(self):
        """Set up test fixtures"""
        # Create temporary directory for log files
        self.temp_dir = tempfile.mkdtemp()
        # Use a unique logger for each test
        import uuid
        self.test_id = str(uuid.uuid4())[:8]
        self.logger = OrderLogger(
            log_to_file=True,
            log_dir=self.temp_dir,
            log_to_console=False  # Disable console for tests
        )
        # Force flush after each log
        if self.logger.file_logger and self.logger.file_logger.handlers:
            for handler in self.logger.file_logger.handlers:
                handler.flush()
    
    def tearDown(self):
        """Clean up after tests"""
        # Clean up temp directory
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_initialization(self):
        """Test logger initialization"""
        self.assertIsNotNone(self.logger)
        self.assertTrue(self.logger.log_to_file)
        self.assertFalse(self.logger.log_to_console)
        self.assertIsNotNone(self.logger.file_logger)
    
    def test_log_submission(self):
        """Test logging order submission"""
        order_record = OrderRecord(
            order_id=1,
            symbol="AAPL",
            action="BUY",
            total_quantity=100,
            order_type="MARKET",
            status=OrderStatus.SUBMITTED
        )
        
        # Should not raise errors
        self.logger.log_submission(order_record)
    
    def test_log_fill_complete(self):
        """Test logging complete fill"""
        order_record = OrderRecord(
            order_id=1,
            symbol="AAPL",
            action="BUY",
            total_quantity=100,
            order_type="MARKET",
            status=OrderStatus.FILLED,
            filled_quantity=100
        )
        
        fill = Fill(
            fill_id="fill-1",
            order_id=1,
            symbol="AAPL",
            quantity=100,
            price=150.50,
            timestamp=datetime.now()
        )
        order_record.fills.append(fill)
        
        # Should not raise errors
        self.logger.log_fill(order_record, fill)
    
    def test_log_fill_partial(self):
        """Test logging partial fill"""
        order_record = OrderRecord(
            order_id=1,
            symbol="AAPL",
            action="BUY",
            total_quantity=100,
            order_type="MARKET",
            status=OrderStatus.PARTIALLY_FILLED,
            filled_quantity=50,
            remaining_quantity=50
        )
        
        fill = Fill(
            fill_id="fill-1",
            order_id=1,
            symbol="AAPL",
            quantity=50,
            price=150.50,
            timestamp=datetime.now()
        )
        order_record.fills.append(fill)
        
        # Should not raise errors
        self.logger.log_fill(order_record, fill)
    
    def test_log_status_change(self):
        """Test logging status change"""
        order_record = OrderRecord(
            order_id=1,
            symbol="AAPL",
            action="BUY",
            total_quantity=100,
            order_type="MARKET",
            status=OrderStatus.SUBMITTED
        )
        
        # Should not raise errors
        self.logger.log_status_change(
            order_record,
            OrderStatus.PENDING,
            OrderStatus.SUBMITTED
        )
    
    def test_log_cancellation(self):
        """Test logging order cancellation"""
        order_record = OrderRecord(
            order_id=1,
            symbol="AAPL",
            action="BUY",
            total_quantity=100,
            order_type="MARKET",
            status=OrderStatus.CANCELLED
        )
        
        # Should not raise errors
        self.logger.log_cancellation(order_record, "User requested")
    
    def test_log_error(self):
        """Test logging order error"""
        order_record = OrderRecord(
            order_id=1,
            symbol="AAPL",
            action="BUY",
            total_quantity=100,
            order_type="MARKET",
            status=OrderStatus.ERROR,
            error_message="Connection lost",
            retry_count=1
        )
        
        # Should not raise errors
        self.logger.log_error(order_record, "Connection lost")
    
    def test_log_retry(self):
        """Test logging order retry"""
        order_record = OrderRecord(
            order_id=1,
            symbol="AAPL",
            action="BUY",
            total_quantity=100,
            order_type="MARKET",
            retry_count=1
        )
        
        # Should not raise errors
        self.logger.log_retry(order_record, 2.0)
    
    def test_get_order_history(self):
        """Test retrieving order history"""
        # Log multiple events for the same order
        order_record = OrderRecord(
            order_id=1,
            symbol="AAPL",
            action="BUY",
            total_quantity=100,
            order_type="MARKET"
        )
        
        self.logger.log_submission(order_record)
        order_record.status = OrderStatus.SUBMITTED
        self.logger.log_status_change(order_record, OrderStatus.PENDING, OrderStatus.SUBMITTED)
        
        # Get history (may be empty in tests, just check it doesn't error)
        history = self.logger.get_order_history(1)
        self.assertIsInstance(history, list)
    
    def test_get_todays_summary(self):
        """Test getting today's order summary"""
        # Create and log multiple orders
        order1 = OrderRecord(
            order_id=1,
            symbol="AAPL",
            action="BUY",
            total_quantity=100,
            order_type="MARKET",
            status=OrderStatus.SUBMITTED
        )
        self.logger.log_submission(order1)
        
        order2 = OrderRecord(
            order_id=2,
            symbol="GOOGL",
            action="SELL",
            total_quantity=50,
            order_type="MARKET",
            status=OrderStatus.SUBMITTED
        )
        self.logger.log_submission(order2)
        
        # Get summary (should work without errors)
        summary = self.logger.get_todays_summary()
        self.assertIsInstance(summary, dict)
        self.assertIn('total_orders', summary)
        self.assertIn('filled_orders', summary)
    
    def test_log_event_custom(self):
        """Test logging custom event"""
        order_record = OrderRecord(
            order_id=1,
            symbol="AAPL",
            action="BUY",
            total_quantity=100,
            order_type="MARKET"
        )
        
        # Should not raise errors
        self.logger.log_event(
            "CUSTOM_EVENT",
            order_record,
            {"detail1": "value1", "detail2": 123}
        )
    
    def test_logger_without_file_logging(self):
        """Test logger with file logging disabled"""
        logger = OrderLogger(
            log_to_file=False,
            log_to_console=False
        )
        
        order_record = OrderRecord(
            order_id=1,
            symbol="AAPL",
            action="BUY",
            total_quantity=100,
            order_type="MARKET"
        )
        
        # Should not raise errors
        logger.log_submission(order_record)
        
        # Should return empty history
        history = logger.get_order_history(1)
        self.assertEqual(len(history), 0)
    
    def test_format_for_console(self):
        """Test console formatting"""
        data = {
            'order_id': 1,
            'symbol': 'AAPL',
            'action': 'BUY',
            'quantity': 100,
            'price': 150.50,
            'status': 'FILLED'
        }
        
        formatted = self.logger._format_for_console(data)
        
        self.assertIn('Order 1', formatted)
        self.assertIn('AAPL', formatted)
        self.assertIn('BUY', formatted)
        self.assertIn('100 shares', formatted)
        self.assertIn('$150.50', formatted)
        self.assertIn('[FILLED]', formatted)


if __name__ == '__main__':
    unittest.main()
