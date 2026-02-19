"""
Tests for Trade Reconciliation Module

These tests verify the trade reconciliation logic using mocks.
"""

import unittest
from unittest.mock import MagicMock
from datetime import datetime, date
import importlib.util
from pathlib import Path

# Import modules directly without going through __init__ to avoid circular imports
broker_path = Path(__file__).parent.parent.parent / "copilot_quant" / "brokers"

# Load trade_reconciliation module directly
spec = importlib.util.spec_from_file_location("trade_reconciliation", broker_path / "trade_reconciliation.py")
trade_reconciliation = importlib.util.module_from_spec(spec)
spec.loader.exec_module(trade_reconciliation)

# Load order_execution_handler module directly  
spec2 = importlib.util.spec_from_file_location("order_execution_handler", broker_path / "order_execution_handler.py")
order_execution = importlib.util.module_from_spec(spec2)
spec2.loader.exec_module(order_execution)

OrderRecord = order_execution.OrderRecord
OrderStatus = order_execution.OrderStatus
Fill = order_execution.Fill


class TestIBKRFill(unittest.TestCase):
    """Test IBKRFill dataclass"""
    
    def test_ibkr_fill_creation(self):
        """Test creating an IBKRFill"""
        fill = trade_reconciliation.trade_reconciliation.IBKRFill(
            execution_id="exec-123",
            order_id=1,
            symbol="AAPL",
            side="BUY",
            quantity=100,
            price=150.50,
            commission=1.0,
            timestamp=datetime.now()
        )
        
        self.assertEqual(fill.execution_id, "exec-123")
        self.assertEqual(fill.order_id, 1)
        self.assertEqual(fill.symbol, "AAPL")
        self.assertEqual(fill.quantity, 100)
    
    def test_ibkr_fill_to_dict(self):
        """Test converting IBKRFill to dictionary"""
        now = datetime.now()
        fill = trade_reconciliation.trade_reconciliation.IBKRFill(
            execution_id="exec-123",
            order_id=1,
            symbol="AAPL",
            side="BUY",
            quantity=100,
            price=150.50,
            commission=1.0,
            timestamp=now
        )
        
        d = fill.to_dict()
        self.assertEqual(d['execution_id'], "exec-123")
        self.assertEqual(d['order_id'], 1)
        self.assertEqual(d['timestamp'], now.isoformat())


class TestLocalFill(unittest.TestCase):
    """Test LocalFill dataclass"""
    
    def test_local_fill_creation(self):
        """Test creating a LocalFill"""
        fill = trade_reconciliation.trade_reconciliation.LocalFill(
            fill_id="fill-456",
            order_id=1,
            symbol="AAPL",
            side="BUY",
            quantity=100,
            price=150.50,
            commission=1.0,
            timestamp=datetime.now()
        )
        
        self.assertEqual(fill.fill_id, "fill-456")
        self.assertEqual(fill.order_id, 1)
        self.assertEqual(fill.symbol, "AAPL")
    
    def test_local_fill_to_dict(self):
        """Test converting LocalFill to dictionary"""
        now = datetime.now()
        fill = trade_reconciliation.trade_reconciliation.LocalFill(
            fill_id="fill-456",
            order_id=1,
            symbol="AAPL",
            side="BUY",
            quantity=100,
            price=150.50,
            commission=1.0,
            timestamp=now
        )
        
        d = fill.to_dict()
        self.assertEqual(d['fill_id'], "fill-456")
        self.assertEqual(d['timestamp'], now.isoformat())


class TestDiscrepancy(unittest.TestCase):
    """Test Discrepancy dataclass"""
    
    def test_discrepancy_creation(self):
        """Test creating a Discrepancy"""
        disc = trade_reconciliation.Discrepancy(
            type=trade_reconciliation.trade_reconciliation.DiscrepancyType.MISSING_LOCAL,
            order_id=1,
            symbol="AAPL",
            description="Missing in local logs"
        )
        
        self.assertEqual(disc.type, trade_reconciliation.trade_reconciliation.DiscrepancyType.MISSING_LOCAL)
        self.assertEqual(disc.order_id, 1)
        self.assertEqual(disc.symbol, "AAPL")
    
    def test_discrepancy_to_dict(self):
        """Test converting Discrepancy to dictionary"""
        disc = trade_reconciliation.Discrepancy(
            type=trade_reconciliation.trade_reconciliation.DiscrepancyType.QUANTITY_MISMATCH,
            order_id=1,
            symbol="AAPL",
            description="Quantities don't match"
        )
        
        d = disc.to_dict()
        self.assertEqual(d['type'], 'QuantityMismatch')
        self.assertEqual(d['order_id'], 1)


class TestReconciliationReport(unittest.TestCase):
    """Test ReconciliationReport"""
    
    def test_report_has_discrepancies(self):
        """Test checking if report has discrepancies"""
        report = trade_reconciliation.trade_reconciliation.ReconciliationReport(reconciliation_date=date.today())
        self.assertFalse(report.has_discrepancies())
        
        report.discrepancies.append(trade_reconciliation.Discrepancy(
            type=trade_reconciliation.trade_reconciliation.DiscrepancyType.MISSING_LOCAL,
            order_id=1,
            symbol="AAPL"
        ))
        self.assertTrue(report.has_discrepancies())
    
    def test_report_summary(self):
        """Test generating report summary"""
        report = trade_reconciliation.trade_reconciliation.ReconciliationReport(
            reconciliation_date=date.today(),
            ibkr_fills=[
                trade_reconciliation.trade_reconciliation.IBKRFill("exec1", 1, "AAPL", "BUY", 100, 150.0, 1.0, datetime.now())
            ],
            local_fills=[
                trade_reconciliation.trade_reconciliation.LocalFill("fill1", 1, "AAPL", "BUY", 100, 150.0, 1.0, datetime.now())
            ]
        )
        report.matched_order_ids.add(1)
        
        summary = report.summary()
        self.assertEqual(summary['total_ibkr_fills'], 1)
        self.assertEqual(summary['total_local_fills'], 1)
        self.assertEqual(summary['matched_orders'], 1)
        self.assertEqual(summary['total_discrepancies'], 0)


class TestTradeReconciliation(unittest.TestCase):
    """Test TradeReconciliation class"""
    
    def setUp(self):
        """Set up test fixtures"""
        # Create mock broker
        self.mock_broker = MagicMock()
        self.mock_broker.is_connected.return_value = True
        
        # Mock IB instance
        self.mock_ib = MagicMock()
        self.mock_broker.ib = self.mock_ib
        
        # Mock order handler
        self.mock_order_handler = MagicMock()
        self.mock_broker.order_handler = self.mock_order_handler
        
        self.reconciler = trade_reconciliation.TradeReconciliation(self.mock_broker)
    
    def test_initialization(self):
        """Test reconciler initialization"""
        self.assertEqual(self.reconciler.broker, self.mock_broker)
        self.assertEqual(self.reconciler.price_tolerance, 0.01)
        self.assertEqual(self.reconciler.commission_tolerance, 0.01)
    
    def test_fetch_ibkr_fills_not_connected(self):
        """Test fetching IBKR fills when not connected"""
        self.mock_broker.is_connected.return_value = False
        
        with self.assertRaises(RuntimeError):
            self.reconciler.fetch_ibkr_fills()
    
    def test_fetch_ibkr_fills_success(self):
        """Test successfully fetching IBKR fills"""
        # Create mock fill
        mock_fill = MagicMock()
        mock_fill.time = datetime.now()
        mock_fill.execution.execId = "exec-123"
        mock_fill.execution.orderId = 1
        mock_fill.execution.side = "BUY"
        mock_fill.execution.shares = 100
        mock_fill.execution.price = 150.50
        mock_fill.contract.symbol = "AAPL"
        mock_fill.commissionReport = MagicMock()
        mock_fill.commissionReport.commission = 1.0
        
        self.mock_ib.fills.return_value = [mock_fill]
        
        fills = self.reconciler.fetch_ibkr_fills()
        
        self.assertEqual(len(fills), 1)
        self.assertEqual(fills[0].execution_id, "exec-123")
        self.assertEqual(fills[0].order_id, 1)
        self.assertEqual(fills[0].symbol, "AAPL")
        self.assertEqual(fills[0].quantity, 100)
        self.assertEqual(fills[0].price, 150.50)
    
    def test_fetch_local_fills_no_handler(self):
        """Test fetching local fills when handler not available"""
        self.mock_broker.order_handler = None
        
        fills = self.reconciler.fetch_local_fills()
        self.assertEqual(len(fills), 0)
    
    def test_fetch_local_fills_success(self):
        """Test successfully fetching local fills"""
        # Create mock order with fill
        mock_order = OrderRecord(
            order_id=1,
            symbol="AAPL",
            action="BUY",
            total_quantity=100,
            order_type="MARKET",
            status=OrderStatus.FILLED
        )
        
        mock_fill = Fill(
            fill_id="fill-456",
            order_id=1,
            symbol="AAPL",
            quantity=100,
            price=150.50,
            timestamp=datetime.now(),
            commission=1.0
        )
        mock_order.fills.append(mock_fill)
        
        self.mock_order_handler.get_all_orders.return_value = [mock_order]
        
        fills = self.reconciler.fetch_local_fills()
        
        self.assertEqual(len(fills), 1)
        self.assertEqual(fills[0].fill_id, "fill-456")
        self.assertEqual(fills[0].order_id, 1)
        self.assertEqual(fills[0].symbol, "AAPL")
    
    def test_reconcile_perfect_match(self):
        """Test reconciliation with perfect match"""
        target_date = date.today()
        now = datetime.combine(target_date, datetime.min.time())
        
        # Create matching fills
        ibkr_fill = trade_reconciliation.IBKRFill(
            execution_id="exec-1",
            order_id=1,
            symbol="AAPL",
            side="BUY",
            quantity=100,
            price=150.50,
            commission=1.0,
            timestamp=now
        )
        
        local_fill = trade_reconciliation.LocalFill(
            fill_id="fill-1",
            order_id=1,
            symbol="AAPL",
            side="BUY",
            quantity=100,
            price=150.50,
            commission=1.0,
            timestamp=now
        )
        
        # Mock fetch methods
        self.reconciler.fetch_ibkr_fills = MagicMock(return_value=[ibkr_fill])
        self.reconciler.fetch_local_fills = MagicMock(return_value=[local_fill])
        
        report = self.reconciler.reconcile(target_date)
        
        self.assertEqual(len(report.ibkr_fills), 1)
        self.assertEqual(len(report.local_fills), 1)
        self.assertEqual(len(report.discrepancies), 0)
        self.assertIn(1, report.matched_order_ids)
    
    def test_reconcile_missing_local(self):
        """Test reconciliation with fill missing locally"""
        target_date = date.today()
        now = datetime.combine(target_date, datetime.min.time())
        
        ibkr_fill = trade_reconciliation.IBKRFill(
            execution_id="exec-1",
            order_id=1,
            symbol="AAPL",
            side="BUY",
            quantity=100,
            price=150.50,
            commission=1.0,
            timestamp=now
        )
        
        self.reconciler.fetch_ibkr_fills = MagicMock(return_value=[ibkr_fill])
        self.reconciler.fetch_local_fills = MagicMock(return_value=[])
        
        report = self.reconciler.reconcile(target_date)
        
        self.assertEqual(len(report.discrepancies), 1)
        self.assertEqual(report.discrepancies[0].type, trade_reconciliation.DiscrepancyType.MISSING_LOCAL)
    
    def test_reconcile_missing_ibkr(self):
        """Test reconciliation with fill missing in IBKR"""
        target_date = date.today()
        now = datetime.combine(target_date, datetime.min.time())
        
        local_fill = trade_reconciliation.LocalFill(
            fill_id="fill-1",
            order_id=1,
            symbol="AAPL",
            side="BUY",
            quantity=100,
            price=150.50,
            commission=1.0,
            timestamp=now
        )
        
        self.reconciler.fetch_ibkr_fills = MagicMock(return_value=[])
        self.reconciler.fetch_local_fills = MagicMock(return_value=[local_fill])
        
        report = self.reconciler.reconcile(target_date)
        
        self.assertEqual(len(report.discrepancies), 1)
        self.assertEqual(report.discrepancies[0].type, trade_reconciliation.DiscrepancyType.MISSING_IBKR)
    
    def test_reconcile_quantity_mismatch(self):
        """Test reconciliation with quantity mismatch"""
        target_date = date.today()
        now = datetime.combine(target_date, datetime.min.time())
        
        ibkr_fill = trade_reconciliation.IBKRFill(
            execution_id="exec-1",
            order_id=1,
            symbol="AAPL",
            side="BUY",
            quantity=100,
            price=150.50,
            commission=1.0,
            timestamp=now
        )
        
        local_fill = trade_reconciliation.LocalFill(
            fill_id="fill-1",
            order_id=1,
            symbol="AAPL",
            side="BUY",
            quantity=50,  # Different quantity
            price=150.50,
            commission=1.0,
            timestamp=now
        )
        
        self.reconciler.fetch_ibkr_fills = MagicMock(return_value=[ibkr_fill])
        self.reconciler.fetch_local_fills = MagicMock(return_value=[local_fill])
        
        report = self.reconciler.reconcile(target_date)
        
        self.assertEqual(len(report.discrepancies), 1)
        self.assertEqual(report.discrepancies[0].type, trade_reconciliation.DiscrepancyType.QUANTITY_MISMATCH)
    
    def test_reconcile_price_mismatch(self):
        """Test reconciliation with price mismatch beyond tolerance"""
        target_date = date.today()
        now = datetime.combine(target_date, datetime.min.time())
        
        ibkr_fill = trade_reconciliation.IBKRFill(
            execution_id="exec-1",
            order_id=1,
            symbol="AAPL",
            side="BUY",
            quantity=100,
            price=150.50,
            commission=1.0,
            timestamp=now
        )
        
        local_fill = trade_reconciliation.LocalFill(
            fill_id="fill-1",
            order_id=1,
            symbol="AAPL",
            side="BUY",
            quantity=100,
            price=151.00,  # Price difference > tolerance
            commission=1.0,
            timestamp=now
        )
        
        self.reconciler.fetch_ibkr_fills = MagicMock(return_value=[ibkr_fill])
        self.reconciler.fetch_local_fills = MagicMock(return_value=[local_fill])
        
        report = self.reconciler.reconcile(target_date)
        
        # Should have price mismatch
        price_mismatches = [d for d in report.discrepancies 
                           if d.type == trade_reconciliation.DiscrepancyType.PRICE_MISMATCH]
        self.assertGreater(len(price_mismatches), 0)
    
    def test_reconcile_today(self):
        """Test reconciling today's trades"""
        self.reconciler.reconcile = MagicMock(return_value=trade_reconciliation.ReconciliationReport(
            reconciliation_date=date.today()
        ))
        
        report = self.reconciler.reconcile_today()
        
        self.reconciler.reconcile.assert_called_once_with(date.today())
        self.assertEqual(report.reconciliation_date, date.today())


if __name__ == '__main__':
    unittest.main()
