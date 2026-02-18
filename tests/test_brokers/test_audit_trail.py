"""
Tests for Audit Trail Module

These tests verify the unified audit trail interface.
"""

import unittest
from unittest.mock import MagicMock, Mock, patch
from datetime import datetime, date
import json

from copilot_quant.brokers.audit_trail import AuditTrail
from copilot_quant.brokers.order_execution_handler import (
    OrderRecord,
    OrderStatus,
    Fill
)
from copilot_quant.brokers.trade_reconciliation import (
    ReconciliationReport,
    Discrepancy,
    DiscrepancyType
)


class TestAuditTrail(unittest.TestCase):
    """Test AuditTrail class"""
    
    def setUp(self):
        """Set up test fixtures"""
        # Create mock broker
        self.mock_broker = MagicMock()
        self.mock_broker.is_connected.return_value = True
        
        # Mock order handler
        self.mock_order_handler = MagicMock()
        self.mock_broker.order_handler = self.mock_order_handler
        
        # Create audit trail with in-memory database
        self.audit = AuditTrail(
            self.mock_broker,
            database_url="sqlite:///:memory:"
        )
    
    def test_initialization(self):
        """Test audit trail initialization"""
        self.assertIsNotNone(self.audit)
        self.assertEqual(self.audit.broker, self.mock_broker)
        self.assertIsNotNone(self.audit.database)
        self.assertIsNotNone(self.audit.reconciler)
        self.assertFalse(self.audit.is_enabled())
    
    def test_enable(self):
        """Test enabling audit trail"""
        self.audit.enable()
        
        self.assertTrue(self.audit.is_enabled())
        
        # Verify callbacks were registered
        self.mock_order_handler.register_fill_callback.assert_called_once()
        self.mock_order_handler.register_status_callback.assert_called_once()
    
    def test_enable_without_order_handler(self):
        """Test enabling without order handler raises error"""
        self.mock_broker.order_handler = None
        
        with self.assertRaises(RuntimeError):
            self.audit.enable()
    
    def test_enable_already_enabled(self):
        """Test enabling when already enabled"""
        self.audit.enable()
        
        # Should handle gracefully
        self.audit.enable()
        self.assertTrue(self.audit.is_enabled())
    
    def test_disable(self):
        """Test disabling audit trail"""
        self.audit.enable()
        self.audit.disable()
        
        self.assertFalse(self.audit.is_enabled())
    
    def test_reconcile_today(self):
        """Test reconciling today's trades"""
        mock_report = ReconciliationReport(reconciliation_date=date.today())
        self.audit.reconciler.reconcile_today = MagicMock(return_value=mock_report)
        
        report = self.audit.reconcile_today()
        
        self.assertEqual(report, mock_report)
        self.audit.reconciler.reconcile_today.assert_called_once()
        
        # Verify report was stored
        reports = self.audit.database.get_reconciliation_reports(
            start_date=date.today(),
            end_date=date.today()
        )
        self.assertEqual(len(reports), 1)
    
    def test_reconcile_date(self):
        """Test reconciling specific date"""
        target_date = date.today()
        mock_report = ReconciliationReport(reconciliation_date=target_date)
        self.audit.reconciler.reconcile = MagicMock(return_value=mock_report)
        
        report = self.audit.reconcile_date(target_date)
        
        self.assertEqual(report, mock_report)
        self.audit.reconciler.reconcile.assert_called_once_with(target_date)
    
    def test_get_orders_by_date(self):
        """Test getting orders by date"""
        # Store an order
        order = OrderRecord(
            order_id=1,
            symbol="AAPL",
            action="BUY",
            total_quantity=100,
            order_type="MARKET",
            submission_time=datetime.combine(date.today(), datetime.min.time())
        )
        self.audit.database.store_order(order)
        
        orders = self.audit.get_orders_by_date(date.today())
        
        self.assertEqual(len(orders), 1)
        self.assertEqual(orders[0]['order_id'], 1)
    
    def test_get_fills_by_date(self):
        """Test getting fills by date"""
        # Store a fill
        fill = Fill(
            fill_id="fill-1",
            order_id=1,
            symbol="AAPL",
            quantity=100,
            price=150.0,
            timestamp=datetime.combine(date.today(), datetime.min.time()),
            commission=1.0
        )
        self.audit.database.store_fill(fill, order_id=1)
        
        fills = self.audit.get_fills_by_date(date.today())
        
        self.assertEqual(len(fills), 1)
        self.assertEqual(fills[0]['fill_id'], "fill-1")
    
    def test_get_order_history(self):
        """Test getting order history"""
        # Store order and fill
        order = OrderRecord(
            order_id=1,
            symbol="AAPL",
            action="BUY",
            total_quantity=100,
            order_type="MARKET"
        )
        self.audit.database.store_order(order)
        
        fill = Fill(
            fill_id="fill-1",
            order_id=1,
            symbol="AAPL",
            quantity=100,
            price=150.0,
            timestamp=datetime.now(),
            commission=1.0
        )
        self.audit.database.store_fill(fill, order_id=1)
        
        history = self.audit.get_order_history(1)
        
        self.assertIn('order', history)
        self.assertIn('fills', history)
        self.assertEqual(history['fill_count'], 1)
    
    def test_get_order_history_not_found(self):
        """Test getting history for non-existent order"""
        history = self.audit.get_order_history(999)
        
        self.assertIn('error', history)
    
    def test_generate_compliance_report_json(self):
        """Test generating JSON compliance report"""
        # Store some data
        order = OrderRecord(
            order_id=1,
            symbol="AAPL",
            action="BUY",
            total_quantity=100,
            order_type="MARKET",
            submission_time=datetime.combine(date.today(), datetime.min.time())
        )
        self.audit.database.store_order(order)
        
        report = self.audit.generate_compliance_report(
            date.today(),
            date.today(),
            format='json'
        )
        
        # Should be valid JSON
        data = json.loads(report)
        self.assertIn('orders', data)
        self.assertEqual(len(data['orders']), 1)
    
    def test_generate_compliance_report_text(self):
        """Test generating text compliance report"""
        # Store some data
        order = OrderRecord(
            order_id=1,
            symbol="AAPL",
            action="BUY",
            total_quantity=100,
            order_type="MARKET",
            submission_time=datetime.combine(date.today(), datetime.min.time())
        )
        self.audit.database.store_order(order)
        
        report = self.audit.generate_compliance_report(
            date.today(),
            date.today(),
            format='text'
        )
        
        # Should be text format
        self.assertIsInstance(report, str)
        self.assertIn('TRADE AUDIT REPORT', report)
        self.assertIn('AAPL', report)
    
    def test_generate_compliance_report_invalid_format(self):
        """Test generating report with invalid format"""
        with self.assertRaises(ValueError):
            self.audit.generate_compliance_report(
                date.today(),
                date.today(),
                format='xml'
            )
    
    def test_export_audit_trail_json(self):
        """Test exporting audit trail to JSON file"""
        import tempfile
        import os
        
        # Store some data
        order = OrderRecord(
            order_id=1,
            symbol="AAPL",
            action="BUY",
            total_quantity=100,
            order_type="MARKET",
            submission_time=datetime.combine(date.today(), datetime.min.time())
        )
        self.audit.database.store_order(order)
        
        # Export to temp file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            temp_file = f.name
        
        try:
            self.audit.export_audit_trail(
                date.today(),
                date.today(),
                output_file=temp_file
            )
            
            # Verify file exists and contains data
            self.assertTrue(os.path.exists(temp_file))
            
            with open(temp_file, 'r') as f:
                data = json.load(f)
                self.assertIn('orders', data)
        finally:
            if os.path.exists(temp_file):
                os.unlink(temp_file)
    
    def test_export_audit_trail_text(self):
        """Test exporting audit trail to text file"""
        import tempfile
        import os
        
        # Store some data
        order = OrderRecord(
            order_id=1,
            symbol="AAPL",
            action="BUY",
            total_quantity=100,
            order_type="MARKET",
            submission_time=datetime.combine(date.today(), datetime.min.time())
        )
        self.audit.database.store_order(order)
        
        # Export to temp file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            temp_file = f.name
        
        try:
            self.audit.export_audit_trail(
                date.today(),
                date.today(),
                output_file=temp_file
            )
            
            # Verify file exists and contains data
            self.assertTrue(os.path.exists(temp_file))
            
            with open(temp_file, 'r') as f:
                content = f.read()
                self.assertIn('TRADE AUDIT REPORT', content)
        finally:
            if os.path.exists(temp_file):
                os.unlink(temp_file)
    
    def test_get_reconciliation_summary(self):
        """Test getting reconciliation summary"""
        # Store a reconciliation report
        report = ReconciliationReport(reconciliation_date=date.today())
        report.matched_order_ids.add(1)
        self.audit.database.store_reconciliation_report(report)
        
        summary = self.audit.get_reconciliation_summary(
            start_date=date.today(),
            end_date=date.today()
        )
        
        self.assertEqual(summary['total_reports'], 1)
        self.assertEqual(summary['total_matched_orders'], 1)
    
    def test_check_compliance_pass(self):
        """Test compliance check that passes"""
        # Store reconciliation with no discrepancies
        report = ReconciliationReport(reconciliation_date=date.today())
        report.matched_order_ids.add(1)
        self.audit.database.store_reconciliation_report(report)
        
        status = self.audit.check_compliance(
            date.today(),
            date.today(),
            max_discrepancies=0
        )
        
        self.assertTrue(status['compliant'])
        self.assertEqual(status['total_discrepancies'], 0)
    
    def test_check_compliance_fail(self):
        """Test compliance check that fails"""
        # Store reconciliation with discrepancy
        report = ReconciliationReport(reconciliation_date=date.today())
        report.discrepancies.append(Discrepancy(
            type=DiscrepancyType.MISSING_LOCAL,
            order_id=1,
            symbol="AAPL",
            description="Test discrepancy"
        ))
        self.audit.database.store_reconciliation_report(report)
        
        status = self.audit.check_compliance(
            date.today(),
            date.today(),
            max_discrepancies=0
        )
        
        self.assertFalse(status['compliant'])
        self.assertEqual(status['total_discrepancies'], 1)
    
    def test_automatic_capture_fill(self):
        """Test that fills are automatically captured when enabled"""
        self.audit.enable()
        
        # Get the registered fill callback
        fill_callback = self.mock_order_handler.register_fill_callback.call_args[0][0]
        
        # Create order and fill
        order = OrderRecord(
            order_id=1,
            symbol="AAPL",
            action="BUY",
            total_quantity=100,
            order_type="MARKET"
        )
        
        fill = Fill(
            fill_id="fill-1",
            order_id=1,
            symbol="AAPL",
            quantity=100,
            price=150.0,
            timestamp=datetime.now(),
            commission=1.0
        )
        order.fills.append(fill)
        
        # Trigger callback
        fill_callback(order)
        
        # Verify order and fill were stored
        stored_order = self.audit.database.get_order_by_id(1)
        self.assertIsNotNone(stored_order)
        
        stored_fills = self.audit.database.get_fills_by_order(1)
        self.assertEqual(len(stored_fills), 1)


if __name__ == '__main__':
    unittest.main()
