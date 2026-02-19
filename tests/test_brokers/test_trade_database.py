"""
Tests for Trade Database Module

These tests verify database storage and retrieval functionality.
"""

import unittest
from datetime import datetime, date

from copilot_quant.brokers.trade_database import (
    TradeDatabase,
    OrderModel,
    FillModel,
    ReconciliationReportModel,
    DiscrepancyModel
)
from copilot_quant.brokers.order_execution_handler import (
    OrderRecord,
    OrderStatus,
    Fill
)
from copilot_quant.brokers.trade_reconciliation import (
    ReconciliationReport,
    Discrepancy,
    DiscrepancyType,
    IBKRFill,
    LocalFill
)


class TestTradeDatabase(unittest.TestCase):
    """Test TradeDatabase class"""
    
    def setUp(self):
        """Set up test database"""
        # Use in-memory SQLite for testing
        self.db = TradeDatabase("sqlite:///:memory:")
    
    def test_initialization(self):
        """Test database initialization"""
        self.assertIsNotNone(self.db)
        self.assertIsNotNone(self.db.engine)
        self.assertIsNotNone(self.db.SessionLocal)
    
    def test_store_order_new(self):
        """Test storing a new order"""
        order = OrderRecord(
            order_id=1,
            symbol="AAPL",
            action="BUY",
            total_quantity=100,
            order_type="MARKET",
            status=OrderStatus.SUBMITTED
        )
        
        db_id = self.db.store_order(order)
        self.assertIsNotNone(db_id)
        self.assertGreater(db_id, 0)
        
        # Verify it's in database
        retrieved = self.db.get_order_by_id(1)
        self.assertIsNotNone(retrieved)
        self.assertEqual(retrieved.symbol, "AAPL")
        self.assertEqual(retrieved.action, "BUY")
    
    def test_store_order_update(self):
        """Test updating an existing order"""
        order = OrderRecord(
            order_id=1,
            symbol="AAPL",
            action="BUY",
            total_quantity=100,
            order_type="MARKET",
            status=OrderStatus.SUBMITTED
        )
        
        # Store initial
        db_id1 = self.db.store_order(order)
        
        # Update status
        order.status = OrderStatus.FILLED
        order.filled_quantity = 100
        
        # Store again
        db_id2 = self.db.store_order(order)
        
        # Should update same record
        self.assertEqual(db_id1, db_id2)
        
        # Verify update
        retrieved = self.db.get_order_by_id(1)
        self.assertEqual(retrieved.status, "Filled")
        self.assertEqual(retrieved.filled_quantity, 100)
    
    def test_store_fill(self):
        """Test storing a fill"""
        # First store the order
        order = OrderRecord(
            order_id=1,
            symbol="AAPL",
            action="BUY",
            total_quantity=100,
            order_type="MARKET"
        )
        self.db.store_order(order)
        
        # Store fill
        fill = Fill(
            fill_id="fill-123",
            order_id=1,
            symbol="AAPL",
            quantity=100,
            price=150.50,
            timestamp=datetime.now(),
            commission=1.0
        )
        
        db_id = self.db.store_fill(fill, order_id=1)
        self.assertIsNotNone(db_id)
        
        # Verify it's in database
        fills = self.db.get_fills_by_order(1)
        self.assertEqual(len(fills), 1)
        self.assertEqual(fills[0].fill_id, "fill-123")
        self.assertEqual(fills[0].quantity, 100)
    
    def test_store_fill_duplicate(self):
        """Test storing duplicate fill"""
        fill = Fill(
            fill_id="fill-123",
            order_id=1,
            symbol="AAPL",
            quantity=100,
            price=150.50,
            timestamp=datetime.now(),
            commission=1.0
        )
        
        # Store twice
        db_id1 = self.db.store_fill(fill, order_id=1)
        db_id2 = self.db.store_fill(fill, order_id=1)
        
        # Should return same ID
        self.assertEqual(db_id1, db_id2)
        
        # Should only have one fill
        fills = self.db.get_fills_by_order(1)
        self.assertEqual(len(fills), 1)
    
    def test_store_reconciliation_report(self):
        """Test storing reconciliation report"""
        report = ReconciliationReport(
            reconciliation_date=date.today()
        )
        
        # Add some fills
        report.ibkr_fills.append(IBKRFill(
            execution_id="exec-1",
            order_id=1,
            symbol="AAPL",
            side="BUY",
            quantity=100,
            price=150.0,
            commission=1.0,
            timestamp=datetime.now()
        ))
        
        report.local_fills.append(LocalFill(
            fill_id="fill-1",
            order_id=1,
            symbol="AAPL",
            side="BUY",
            quantity=100,
            price=150.0,
            commission=1.0,
            timestamp=datetime.now()
        ))
        
        report.matched_order_ids.add(1)
        
        db_id = self.db.store_reconciliation_report(report)
        self.assertIsNotNone(db_id)
        
        # Verify in database
        reports = self.db.get_reconciliation_reports(
            start_date=date.today(),
            end_date=date.today()
        )
        self.assertEqual(len(reports), 1)
        self.assertEqual(reports[0].total_ibkr_fills, 1)
        self.assertEqual(reports[0].total_local_fills, 1)
    
    def test_store_reconciliation_with_discrepancies(self):
        """Test storing reconciliation report with discrepancies"""
        report = ReconciliationReport(
            reconciliation_date=date.today()
        )
        
        # Add discrepancy
        report.discrepancies.append(Discrepancy(
            type=DiscrepancyType.MISSING_LOCAL,
            order_id=1,
            symbol="AAPL",
            description="Missing in local logs",
            ibkr_fill=IBKRFill(
                execution_id="exec-1",
                order_id=1,
                symbol="AAPL",
                side="BUY",
                quantity=100,
                price=150.0,
                commission=1.0,
                timestamp=datetime.now()
            )
        ))
        
        self.db.store_reconciliation_report(report)
        
        # Verify discrepancies
        discrepancies = self.db.get_discrepancies_by_type(
            DiscrepancyType.MISSING_LOCAL
        )
        self.assertEqual(len(discrepancies), 1)
        self.assertEqual(discrepancies[0].order_id, 1)
    
    def test_get_orders_by_date(self):
        """Test retrieving orders by date"""
        today = date.today()
        
        # Store orders
        for i in range(3):
            order = OrderRecord(
                order_id=i+1,
                symbol="AAPL",
                action="BUY",
                total_quantity=100,
                order_type="MARKET",
                submission_time=datetime.combine(today, datetime.min.time())
            )
            self.db.store_order(order)
        
        # Retrieve
        orders = self.db.get_orders_by_date(today)
        self.assertEqual(len(orders), 3)
    
    def test_get_orders_by_symbol(self):
        """Test retrieving orders by symbol"""
        # Store orders for different symbols
        order_id = 1
        for symbol in ["AAPL", "GOOGL", "AAPL"]:
            order = OrderRecord(
                order_id=order_id,
                symbol=symbol,
                action="BUY",
                total_quantity=100,
                order_type="MARKET"
            )
            self.db.store_order(order)
            order_id += 1
        
        # Retrieve AAPL orders
        orders = self.db.get_orders_by_symbol("AAPL")
        self.assertEqual(len(orders), 2)
        
        # Retrieve GOOGL orders
        orders = self.db.get_orders_by_symbol("GOOGL")
        self.assertEqual(len(orders), 1)
    
    def test_get_fills_by_date(self):
        """Test retrieving fills by date"""
        today = date.today()
        now = datetime.combine(today, datetime.min.time())
        
        # Store fills
        for i in range(2):
            fill = Fill(
                fill_id=f"fill-{i}",
                order_id=1,
                symbol="AAPL",
                quantity=50,
                price=150.0,
                timestamp=now,
                commission=0.5
            )
            self.db.store_fill(fill, order_id=1)
        
        # Retrieve
        fills = self.db.get_fills_by_date(today)
        self.assertEqual(len(fills), 2)
    
    def test_get_audit_trail(self):
        """Test getting complete audit trail"""
        today = date.today()
        now = datetime.combine(today, datetime.min.time())
        
        # Store order
        order = OrderRecord(
            order_id=1,
            symbol="AAPL",
            action="BUY",
            total_quantity=100,
            order_type="MARKET",
            submission_time=now
        )
        self.db.store_order(order)
        
        # Store fill
        fill = Fill(
            fill_id="fill-1",
            order_id=1,
            symbol="AAPL",
            quantity=100,
            price=150.0,
            timestamp=now,
            commission=1.0
        )
        self.db.store_fill(fill, order_id=1)
        
        # Store reconciliation
        report = ReconciliationReport(reconciliation_date=today)
        self.db.store_reconciliation_report(report)
        
        # Get audit trail
        audit = self.db.get_audit_trail(today, today)
        
        self.assertEqual(len(audit['orders']), 1)
        self.assertEqual(len(audit['fills']), 1)
        self.assertEqual(len(audit['reconciliation_reports']), 1)
    
    def test_order_model_to_dict(self):
        """Test OrderModel to_dict method"""
        order = OrderRecord(
            order_id=1,
            symbol="AAPL",
            action="BUY",
            total_quantity=100,
            order_type="MARKET"
        )
        self.db.store_order(order)
        
        order_model = self.db.get_order_by_id(1)
        d = order_model.to_dict()
        
        self.assertEqual(d['order_id'], 1)
        self.assertEqual(d['symbol'], "AAPL")
        self.assertIn('submission_time', d)
    
    def test_fill_model_to_dict(self):
        """Test FillModel to_dict method"""
        fill = Fill(
            fill_id="fill-1",
            order_id=1,
            symbol="AAPL",
            quantity=100,
            price=150.0,
            timestamp=datetime.now(),
            commission=1.0
        )
        self.db.store_fill(fill, order_id=1)
        
        fills = self.db.get_fills_by_order(1)
        d = fills[0].to_dict()
        
        self.assertEqual(d['fill_id'], "fill-1")
        self.assertEqual(d['quantity'], 100)


class TestDatabaseModels(unittest.TestCase):
    """Test database model classes directly"""
    
    def test_order_model_creation(self):
        """Test creating OrderModel"""
        model = OrderModel(
            order_id=1,
            symbol="AAPL",
            action="BUY",
            total_quantity=100,
            order_type="MARKET",
            status="Submitted",
            remaining_quantity=100,
            submission_time=datetime.now(),
            last_update_time=datetime.now()
        )
        
        self.assertEqual(model.order_id, 1)
        self.assertEqual(model.symbol, "AAPL")
    
    def test_fill_model_creation(self):
        """Test creating FillModel"""
        model = FillModel(
            fill_id="fill-1",
            order_id=1,
            symbol="AAPL",
            quantity=100,
            price=150.0,
            timestamp=datetime.now()
        )
        
        self.assertEqual(model.fill_id, "fill-1")
        self.assertEqual(model.quantity, 100)
    
    def test_reconciliation_report_model_creation(self):
        """Test creating ReconciliationReportModel"""
        model = ReconciliationReportModel(
            reconciliation_date=date.today(),
            timestamp=datetime.now(),
            total_ibkr_fills=5,
            total_local_fills=5,
            matched_orders=5,
            total_discrepancies=0
        )
        
        self.assertEqual(model.total_ibkr_fills, 5)
        self.assertEqual(model.total_discrepancies, 0)
    
    def test_discrepancy_model_creation(self):
        """Test creating DiscrepancyModel"""
        model = DiscrepancyModel(
            report_id=1,
            type="MissingLocal",
            order_id=1,
            symbol="AAPL",
            description="Test discrepancy"
        )
        
        self.assertEqual(model.type, "MissingLocal")
        self.assertEqual(model.order_id, 1)


if __name__ == '__main__':
    unittest.main()
