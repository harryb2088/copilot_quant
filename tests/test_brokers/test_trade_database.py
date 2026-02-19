"""
Tests for Trade Database Module

These tests verify database storage and retrieval functionality.
"""

import unittest
from datetime import date, datetime

from copilot_quant.brokers.order_execution_handler import Fill, OrderRecord, OrderStatus
from copilot_quant.brokers.trade_database import (
    DiscrepancyModel,
    FillModel,
    OrderModel,
    ReconciliationReportModel,
    TradeDatabase,
)
from copilot_quant.brokers.trade_reconciliation import (
    Discrepancy,
    DiscrepancyType,
    IBKRFill,
    LocalFill,
    ReconciliationReport,
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
            status=OrderStatus.SUBMITTED,
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
            status=OrderStatus.SUBMITTED,
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
        order = OrderRecord(order_id=1, symbol="AAPL", action="BUY", total_quantity=100, order_type="MARKET")
        self.db.store_order(order)

        # Store fill
        fill = Fill(
            fill_id="fill-123",
            order_id=1,
            symbol="AAPL",
            quantity=100,
            price=150.50,
            timestamp=datetime.now(),
            commission=1.0,
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
            commission=1.0,
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
        report = ReconciliationReport(reconciliation_date=date.today())

        # Add some fills
        report.ibkr_fills.append(
            IBKRFill(
                execution_id="exec-1",
                order_id=1,
                symbol="AAPL",
                side="BUY",
                quantity=100,
                price=150.0,
                commission=1.0,
                timestamp=datetime.now(),
            )
        )

        report.local_fills.append(
            LocalFill(
                fill_id="fill-1",
                order_id=1,
                symbol="AAPL",
                side="BUY",
                quantity=100,
                price=150.0,
                commission=1.0,
                timestamp=datetime.now(),
            )
        )

        report.matched_order_ids.add(1)

        db_id = self.db.store_reconciliation_report(report)
        self.assertIsNotNone(db_id)

        # Verify in database
        reports = self.db.get_reconciliation_reports(start_date=date.today(), end_date=date.today())
        self.assertEqual(len(reports), 1)
        self.assertEqual(reports[0].total_ibkr_fills, 1)
        self.assertEqual(reports[0].total_local_fills, 1)

    def test_store_reconciliation_with_discrepancies(self):
        """Test storing reconciliation report with discrepancies"""
        report = ReconciliationReport(reconciliation_date=date.today())

        # Add discrepancy
        report.discrepancies.append(
            Discrepancy(
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
                    timestamp=datetime.now(),
                ),
            )
        )

        self.db.store_reconciliation_report(report)

        # Verify discrepancies
        discrepancies = self.db.get_discrepancies_by_type(DiscrepancyType.MISSING_LOCAL)
        self.assertEqual(len(discrepancies), 1)
        self.assertEqual(discrepancies[0].order_id, 1)

    def test_get_orders_by_date(self):
        """Test retrieving orders by date"""
        today = date.today()

        # Store orders
        for i in range(3):
            order = OrderRecord(
                order_id=i + 1,
                symbol="AAPL",
                action="BUY",
                total_quantity=100,
                order_type="MARKET",
                submission_time=datetime.combine(today, datetime.min.time()),
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
            order = OrderRecord(order_id=order_id, symbol=symbol, action="BUY", total_quantity=100, order_type="MARKET")
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
                fill_id=f"fill-{i}", order_id=1, symbol="AAPL", quantity=50, price=150.0, timestamp=now, commission=0.5
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
            order_id=1, symbol="AAPL", action="BUY", total_quantity=100, order_type="MARKET", submission_time=now
        )
        self.db.store_order(order)

        # Store fill
        fill = Fill(
            fill_id="fill-1", order_id=1, symbol="AAPL", quantity=100, price=150.0, timestamp=now, commission=1.0
        )
        self.db.store_fill(fill, order_id=1)

        # Store reconciliation
        report = ReconciliationReport(reconciliation_date=today)
        self.db.store_reconciliation_report(report)

        # Get audit trail
        audit = self.db.get_audit_trail(today, today)

        self.assertEqual(len(audit["orders"]), 1)
        self.assertEqual(len(audit["fills"]), 1)
        self.assertEqual(len(audit["reconciliation_reports"]), 1)

    def test_order_model_to_dict(self):
        """Test OrderModel to_dict method"""
        order = OrderRecord(order_id=1, symbol="AAPL", action="BUY", total_quantity=100, order_type="MARKET")
        self.db.store_order(order)

        order_model = self.db.get_order_by_id(1)
        d = order_model.to_dict()

        self.assertEqual(d["order_id"], 1)
        self.assertEqual(d["symbol"], "AAPL")
        self.assertIn("submission_time", d)

    def test_fill_model_to_dict(self):
        """Test FillModel to_dict method"""
        fill = Fill(
            fill_id="fill-1",
            order_id=1,
            symbol="AAPL",
            quantity=100,
            price=150.0,
            timestamp=datetime.now(),
            commission=1.0,
        )
        self.db.store_fill(fill, order_id=1)

        fills = self.db.get_fills_by_order(1)
        d = fills[0].to_dict()

        self.assertEqual(d["fill_id"], "fill-1")
        self.assertEqual(d["quantity"], 100)


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
            last_update_time=datetime.now(),
        )

        self.assertEqual(model.order_id, 1)
        self.assertEqual(model.symbol, "AAPL")

    def test_fill_model_creation(self):
        """Test creating FillModel"""
        model = FillModel(
            fill_id="fill-1", order_id=1, symbol="AAPL", quantity=100, price=150.0, timestamp=datetime.now()
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
            total_discrepancies=0,
        )

        self.assertEqual(model.total_ibkr_fills, 5)
        self.assertEqual(model.total_discrepancies, 0)

    def test_discrepancy_model_creation(self):
        """Test creating DiscrepancyModel"""
        model = DiscrepancyModel(
            report_id=1, type="MissingLocal", order_id=1, symbol="AAPL", description="Test discrepancy"
        )

        self.assertEqual(model.type, "MissingLocal")
        self.assertEqual(model.order_id, 1)




class TestPortfolioSnapshotQueries(unittest.TestCase):
    """Test portfolio snapshot query methods in TradeDatabase"""

    def setUp(self):
        """Set up test database with portfolio snapshot support"""
        # Import models to ensure they're available
        try:
            from copilot_quant.live.portfolio_state_manager import (
                PortfolioSnapshotModel,
                PositionSnapshotModel,
                Base as PortfolioBase,
            )

            # Use in-memory SQLite for testing
            from sqlalchemy import create_engine
            from sqlalchemy.orm import sessionmaker
            from sqlalchemy.pool import StaticPool

            # Create engine with both TradeDatabase and PortfolioStateManager schemas
            self.engine = create_engine(
                "sqlite:///:memory:", connect_args={"check_same_thread": False}, poolclass=StaticPool
            )

            # Create tables from both modules
            from copilot_quant.brokers.trade_database import Base as TradeBase

            TradeBase.metadata.create_all(bind=self.engine)
            PortfolioBase.metadata.create_all(bind=self.engine)

            # Create TradeDatabase with existing engine
            self.db = TradeDatabase("sqlite:///:memory:")
            # Replace its engine with our combined one
            self.db.engine = self.engine
            self.db.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)

            self.portfolio_snapshot_available = True

        except ImportError:
            self.portfolio_snapshot_available = False
            self.db = TradeDatabase("sqlite:///:memory:")

    def test_get_portfolio_snapshots_empty(self):
        """Test getting portfolio snapshots when none exist"""
        if not self.portfolio_snapshot_available:
            self.skipTest("Portfolio snapshot models not available")

        snapshots = self.db.get_portfolio_snapshots()
        self.assertEqual(len(snapshots), 0)

    def test_get_portfolio_snapshots_with_data(self):
        """Test getting portfolio snapshots with data"""
        if not self.portfolio_snapshot_available:
            self.skipTest("Portfolio snapshot models not available")

        from copilot_quant.live.portfolio_state_manager import PortfolioSnapshotModel

        # Add test snapshots
        session = self.db.SessionLocal()
        try:
            for i in range(3):
                snapshot = PortfolioSnapshotModel(
                    timestamp=datetime.now(),
                    snapshot_date=date.today(),
                    nav=100000.0 + i * 1000,
                    cash=10000.0,
                    equity_value=90000.0 + i * 1000,
                    num_positions=5,
                    drawdown=0.01 * i,
                    daily_pnl=500.0,
                    peak_nav=100000.0 + i * 1000,
                )
                session.add(snapshot)
            session.commit()
        finally:
            session.close()

        # Query snapshots
        snapshots = self.db.get_portfolio_snapshots()
        self.assertEqual(len(snapshots), 3)
        self.assertIn("nav", snapshots[0])
        self.assertIn("drawdown", snapshots[0])

    def test_get_portfolio_snapshots_with_date_filter(self):
        """Test getting portfolio snapshots with date filtering"""
        if not self.portfolio_snapshot_available:
            self.skipTest("Portfolio snapshot models not available")

        from copilot_quant.live.portfolio_state_manager import PortfolioSnapshotModel
        from datetime import timedelta

        # Add test snapshots for different dates
        session = self.db.SessionLocal()
        try:
            today = date.today()
            for i in range(5):
                snapshot_date = today - timedelta(days=i)
                snapshot = PortfolioSnapshotModel(
                    timestamp=datetime.combine(snapshot_date, datetime.min.time()),
                    snapshot_date=snapshot_date,
                    nav=100000.0,
                    cash=10000.0,
                    equity_value=90000.0,
                    num_positions=5,
                    drawdown=0.0,
                    daily_pnl=0.0,
                    peak_nav=100000.0,
                )
                session.add(snapshot)
            session.commit()
        finally:
            session.close()

        # Query with date filter
        start_date = today - timedelta(days=2)
        snapshots = self.db.get_portfolio_snapshots(start_date=start_date)

        # Should get 3 snapshots: today, -1 day, -2 days
        self.assertEqual(len(snapshots), 3)

    def test_get_portfolio_snapshots_with_limit(self):
        """Test getting portfolio snapshots with limit"""
        if not self.portfolio_snapshot_available:
            self.skipTest("Portfolio snapshot models not available")

        from copilot_quant.live.portfolio_state_manager import PortfolioSnapshotModel

        # Add 10 test snapshots
        session = self.db.SessionLocal()
        try:
            for i in range(10):
                snapshot = PortfolioSnapshotModel(
                    timestamp=datetime.now(),
                    snapshot_date=date.today(),
                    nav=100000.0,
                    cash=10000.0,
                    equity_value=90000.0,
                    num_positions=5,
                    drawdown=0.0,
                    daily_pnl=0.0,
                    peak_nav=100000.0,
                )
                session.add(snapshot)
            session.commit()
        finally:
            session.close()

        # Query with limit
        snapshots = self.db.get_portfolio_snapshots(limit=5)
        self.assertEqual(len(snapshots), 5)

    def test_get_portfolio_snapshot_by_id(self):
        """Test getting a specific portfolio snapshot by ID"""
        if not self.portfolio_snapshot_available:
            self.skipTest("Portfolio snapshot models not available")

        from copilot_quant.live.portfolio_state_manager import PortfolioSnapshotModel

        # Add test snapshot
        session = self.db.SessionLocal()
        try:
            snapshot = PortfolioSnapshotModel(
                timestamp=datetime.now(),
                snapshot_date=date.today(),
                nav=100000.0,
                cash=10000.0,
                equity_value=90000.0,
                num_positions=5,
                drawdown=0.05,
                daily_pnl=250.0,
                peak_nav=105000.0,
            )
            session.add(snapshot)
            session.commit()
            snapshot_id = snapshot.id
        finally:
            session.close()

        # Query by ID
        result = self.db.get_portfolio_snapshot_by_id(snapshot_id)
        self.assertIsNotNone(result)
        self.assertEqual(result["nav"], 100000.0)
        self.assertEqual(result["drawdown"], 0.05)

        # Query non-existent ID
        result = self.db.get_portfolio_snapshot_by_id(99999)
        self.assertIsNone(result)

    def test_get_equity_curve(self):
        """Test getting equity curve data"""
        if not self.portfolio_snapshot_available:
            self.skipTest("Portfolio snapshot models not available")

        from copilot_quant.live.portfolio_state_manager import PortfolioSnapshotModel
        from datetime import timedelta

        # Add test snapshots
        session = self.db.SessionLocal()
        try:
            today = date.today()
            for i in range(5):
                snapshot_date = today - timedelta(days=4 - i)
                snapshot = PortfolioSnapshotModel(
                    timestamp=datetime.combine(snapshot_date, datetime.min.time()),
                    snapshot_date=snapshot_date,
                    nav=100000.0 + i * 500,
                    cash=10000.0,
                    equity_value=90000.0 + i * 500,
                    num_positions=5,
                    drawdown=0.0,
                    daily_pnl=500.0 if i > 0 else 0.0,
                    peak_nav=100000.0 + i * 500,
                )
                session.add(snapshot)
            session.commit()
        finally:
            session.close()

        # Query equity curve
        equity_curve = self.db.get_equity_curve()
        self.assertEqual(len(equity_curve), 5)
        self.assertIn("timestamp", equity_curve[0])
        self.assertIn("nav", equity_curve[0])
        self.assertIn("drawdown", equity_curve[0])
        self.assertIn("daily_pnl", equity_curve[0])

        # Verify ordering (should be chronological)
        navs = [point["nav"] for point in equity_curve]
        self.assertEqual(navs, sorted(navs))

    def test_get_equity_curve_with_date_range(self):
        """Test getting equity curve with date range"""
        if not self.portfolio_snapshot_available:
            self.skipTest("Portfolio snapshot models not available")

        from copilot_quant.live.portfolio_state_manager import PortfolioSnapshotModel
        from datetime import timedelta

        # Add test snapshots
        session = self.db.SessionLocal()
        try:
            today = date.today()
            for i in range(10):
                snapshot_date = today - timedelta(days=9 - i)
                snapshot = PortfolioSnapshotModel(
                    timestamp=datetime.combine(snapshot_date, datetime.min.time()),
                    snapshot_date=snapshot_date,
                    nav=100000.0,
                    cash=10000.0,
                    equity_value=90000.0,
                    num_positions=5,
                    drawdown=0.0,
                    daily_pnl=0.0,
                    peak_nav=100000.0,
                )
                session.add(snapshot)
            session.commit()
        finally:
            session.close()

        # Query with date range
        start_date = today - timedelta(days=4)
        end_date = today
        equity_curve = self.db.get_equity_curve(start_date=start_date, end_date=end_date)

        # Should get 5 points
        self.assertEqual(len(equity_curve), 5)

    def test_get_position_snapshots(self):
        """Test getting position snapshots"""
        if not self.portfolio_snapshot_available:
            self.skipTest("Portfolio snapshot models not available")

        from copilot_quant.live.portfolio_state_manager import (
            PortfolioSnapshotModel,
            PositionSnapshotModel,
        )

        # Add test data
        session = self.db.SessionLocal()
        try:
            portfolio_snapshot = PortfolioSnapshotModel(
                timestamp=datetime.now(),
                snapshot_date=date.today(),
                nav=100000.0,
                cash=10000.0,
                equity_value=90000.0,
                num_positions=2,
                drawdown=0.0,
                daily_pnl=0.0,
                peak_nav=100000.0,
            )
            session.add(portfolio_snapshot)
            session.flush()

            # Add position snapshots
            for symbol in ["AAPL", "GOOGL"]:
                pos_snapshot = PositionSnapshotModel(
                    portfolio_snapshot_id=portfolio_snapshot.id,
                    symbol=symbol,
                    quantity=100,
                    avg_cost=150.0,
                    current_price=155.0,
                    market_value=15500.0,
                    unrealized_pnl=500.0,
                    realized_pnl=0.0,
                )
                session.add(pos_snapshot)

            session.commit()
            snapshot_id = portfolio_snapshot.id
        finally:
            session.close()

        # Query all position snapshots
        positions = self.db.get_position_snapshots()
        self.assertEqual(len(positions), 2)

        # Query by snapshot ID
        positions = self.db.get_position_snapshots(snapshot_id=snapshot_id)
        self.assertEqual(len(positions), 2)

        # Query by symbol
        positions = self.db.get_position_snapshots(symbol="AAPL")
        self.assertEqual(len(positions), 1)
        self.assertEqual(positions[0]["symbol"], "AAPL")

    def test_get_latest_portfolio_snapshot(self):
        """Test getting the latest portfolio snapshot"""
        if not self.portfolio_snapshot_available:
            self.skipTest("Portfolio snapshot models not available")

        from copilot_quant.live.portfolio_state_manager import PortfolioSnapshotModel
        from datetime import timedelta
        import time

        # Add test snapshots
        session = self.db.SessionLocal()
        try:
            for i in range(3):
                snapshot = PortfolioSnapshotModel(
                    timestamp=datetime.now(),
                    snapshot_date=date.today(),
                    nav=100000.0 + i * 1000,
                    cash=10000.0,
                    equity_value=90000.0 + i * 1000,
                    num_positions=5,
                    drawdown=0.0,
                    daily_pnl=0.0,
                    peak_nav=100000.0 + i * 1000,
                )
                session.add(snapshot)
                session.flush()
                # Small delay to ensure different timestamps
                time.sleep(0.01)
            session.commit()
        finally:
            session.close()

        # Get latest
        latest = self.db.get_latest_portfolio_snapshot()
        self.assertIsNotNone(latest)
        # Should be the last one added (highest NAV)
        self.assertEqual(latest["nav"], 102000.0)

    def test_portfolio_snapshot_not_available(self):
        """Test error handling when portfolio snapshot models are not available"""
        # Create a mock database that will fail the import
        # We'll test this by temporarily renaming the module (not actually possible)
        # Instead, we'll just verify the error is raised when models are missing
        
        # This test verifies that the error message is correct
        # In a real scenario where portfolio_state_manager is not installed,
        # the methods would raise RuntimeError
        
        # We can't easily simulate missing module in the test,
        # so we just verify the methods work when module is available
        if not self.portfolio_snapshot_available:
            # If module not available, verify it raises error
            with self.assertRaises(RuntimeError) as context:
                self.db.get_portfolio_snapshots()
            self.assertIn("not available", str(context.exception))
        else:
            # If module is available, verify methods work
            snapshots = self.db.get_portfolio_snapshots()
            self.assertIsInstance(snapshots, list)


if __name__ == "__main__":
    unittest.main()
