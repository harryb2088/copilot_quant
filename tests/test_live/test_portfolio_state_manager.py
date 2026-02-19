"""
Tests for Portfolio State Manager

These tests verify portfolio state persistence and reconciliation functionality.
"""

import unittest
from datetime import date, datetime, timedelta

from copilot_quant.backtest.orders import Position
from copilot_quant.live.portfolio_state_manager import (
    PortfolioSnapshot,
    PortfolioSnapshotModel,
    PortfolioStateManager,
    PositionSnapshotModel,
)


class MockBrokerAdapter:
    """Mock broker adapter for testing"""

    def __init__(self):
        self.account_value = 100000.0
        self.cash_balance = 50000.0
        self.positions = {}
        self.connected = True

    def is_connected(self):
        return self.connected

    def get_account_value(self):
        return self.account_value

    def get_cash_balance(self):
        return self.cash_balance

    def get_positions(self):
        return self.positions


class TestPortfolioStateManager(unittest.TestCase):
    """Test PortfolioStateManager class"""

    def setUp(self):
        """Set up test fixtures"""
        self.broker = MockBrokerAdapter()
        self.manager = PortfolioStateManager(
            broker=self.broker, database_url="sqlite:///:memory:", sync_interval_minutes=5, snapshot_interval_minutes=15
        )

    def test_initialization(self):
        """Test manager initialization"""
        self.assertIsNotNone(self.manager)
        self.assertIsNotNone(self.manager.engine)
        self.assertIsNotNone(self.manager.SessionLocal)
        self.assertEqual(self.manager.sync_interval_minutes, 5)
        self.assertEqual(self.manager.snapshot_interval_minutes, 15)
        self.assertFalse(self.manager._initialized)

    def test_initialize_success(self):
        """Test successful initialization"""
        result = self.manager.initialize()

        self.assertTrue(result)
        self.assertTrue(self.manager._initialized)
        self.assertIsNotNone(self.manager._last_sync_time)
        self.assertIsNotNone(self.manager._last_snapshot_time)

    def test_initialize_disconnected(self):
        """Test initialization when broker is disconnected"""
        self.broker.connected = False
        result = self.manager.initialize()

        self.assertFalse(result)
        self.assertFalse(self.manager._initialized)

    def test_sync_with_broker(self):
        """Test syncing with broker"""
        result = self.manager.sync_with_broker()

        self.assertTrue(result)
        self.assertIsNotNone(self.manager._last_sync_time)

    def test_sync_with_broker_disconnected(self):
        """Test sync when broker is disconnected"""
        self.broker.connected = False
        result = self.manager.sync_with_broker()

        self.assertFalse(result)

    def test_take_snapshot_success(self):
        """Test taking a portfolio snapshot"""
        # Add some positions
        position = Position(symbol="AAPL", quantity=10, avg_entry_price=150.0, unrealized_pnl=50.0, realized_pnl=0.0)

        self.broker.positions = {"AAPL": position}

        result = self.manager.take_snapshot()

        self.assertTrue(result)
        self.assertIsNotNone(self.manager._last_snapshot_time)

        # Verify snapshot was stored
        state = self.manager.get_current_state()
        self.assertIsNotNone(state)
        self.assertEqual(state.nav, 100000.0)
        self.assertEqual(state.cash, 50000.0)
        self.assertEqual(state.num_positions, 1)

    def test_take_snapshot_disconnected(self):
        """Test snapshot when broker is disconnected"""
        self.broker.connected = False
        result = self.manager.take_snapshot()

        self.assertFalse(result)

    def test_should_sync(self):
        """Test sync timing logic"""
        # Should sync initially
        self.assertTrue(self.manager.should_sync())

        # Set last sync time to now
        self.manager._last_sync_time = datetime.now()

        # Should not sync immediately
        self.assertFalse(self.manager.should_sync())

        # Set last sync time to past
        self.manager._last_sync_time = datetime.now() - timedelta(minutes=10)

        # Should sync now
        self.assertTrue(self.manager.should_sync())

    def test_should_snapshot(self):
        """Test snapshot timing logic"""
        # Should snapshot initially
        self.assertTrue(self.manager.should_snapshot())

        # Set last snapshot time to now
        self.manager._last_snapshot_time = datetime.now()

        # Should not snapshot immediately
        self.assertFalse(self.manager.should_snapshot())

        # Set last snapshot time to past
        self.manager._last_snapshot_time = datetime.now() - timedelta(minutes=20)

        # Should snapshot now
        self.assertTrue(self.manager.should_snapshot())

    def test_get_current_state(self):
        """Test getting current portfolio state"""
        # No snapshots initially
        state = self.manager.get_current_state()
        self.assertIsNone(state)

        # Take a snapshot
        self.manager.take_snapshot()

        # Should have state now
        state = self.manager.get_current_state()
        self.assertIsNotNone(state)
        self.assertIsInstance(state, PortfolioSnapshot)
        self.assertEqual(state.nav, 100000.0)

    def test_get_equity_curve(self):
        """Test getting equity curve"""
        # Take multiple snapshots with different NAVs
        for i in range(5):
            self.broker.account_value = 100000.0 + (i * 1000)
            self.manager.take_snapshot()

        # Get equity curve
        curve = self.manager.get_equity_curve(days=30)

        self.assertIsNotNone(curve)
        self.assertEqual(len(curve), 5)
        self.assertIn("nav", curve.columns)
        self.assertIn("drawdown", curve.columns)
        self.assertIn("daily_pnl", curve.columns)

    def test_get_equity_curve_empty(self):
        """Test getting equity curve with no data"""
        curve = self.manager.get_equity_curve(days=30)

        self.assertTrue(curve.empty)

    def test_drawdown_calculation(self):
        """Test drawdown calculation"""
        # Set high NAV
        self.broker.account_value = 100000.0
        self.manager.take_snapshot()

        # Drop NAV
        self.broker.account_value = 90000.0
        self.manager.take_snapshot()

        # Get current state
        state = self.manager.get_current_state()

        # Should show 10% drawdown
        self.assertAlmostEqual(state.drawdown, 0.1, places=2)

    def test_peak_nav_tracking(self):
        """Test peak NAV tracking"""
        # Initial NAV
        self.broker.account_value = 100000.0
        self.manager.take_snapshot()
        self.assertEqual(self.manager._peak_nav, 100000.0)

        # Higher NAV
        self.broker.account_value = 110000.0
        self.manager.take_snapshot()
        self.assertEqual(self.manager._peak_nav, 110000.0)

        # Lower NAV (peak should not change)
        self.broker.account_value = 105000.0
        self.manager.take_snapshot()
        self.assertEqual(self.manager._peak_nav, 110000.0)

    def test_reconciliation_logging(self):
        """Test reconciliation logging"""
        # Sync with broker
        self.manager.sync_with_broker()

        # Get reconciliation history
        history = self.manager.get_reconciliation_history(days=7)

        self.assertIsNotNone(history)
        self.assertEqual(len(history), 1)
        self.assertEqual(history[0].ibkr_nav, 100000.0)


class TestPortfolioSnapshotModel(unittest.TestCase):
    """Test PortfolioSnapshotModel"""

    def test_to_dict(self):
        """Test conversion to dictionary"""
        snapshot = PortfolioSnapshotModel(
            timestamp=datetime.now(),
            snapshot_date=date.today(),
            nav=100000.0,
            cash=50000.0,
            equity_value=50000.0,
            num_positions=5,
            drawdown=0.05,
            daily_pnl=1000.0,
            peak_nav=105000.0,
        )

        data = snapshot.to_dict()

        self.assertEqual(data["nav"], 100000.0)
        self.assertEqual(data["cash"], 50000.0)
        self.assertEqual(data["num_positions"], 5)
        self.assertIn("timestamp", data)


class TestPositionSnapshotModel(unittest.TestCase):
    """Test PositionSnapshotModel"""

    def test_to_dict(self):
        """Test conversion to dictionary"""
        position = PositionSnapshotModel(
            portfolio_snapshot_id=1,
            symbol="AAPL",
            quantity=10,
            avg_cost=150.0,
            current_price=155.0,
            market_value=1550.0,
            unrealized_pnl=50.0,
            realized_pnl=0.0,
        )

        data = position.to_dict()

        self.assertEqual(data["symbol"], "AAPL")
        self.assertEqual(data["quantity"], 10)
        self.assertEqual(data["avg_cost"], 150.0)
        self.assertEqual(data["market_value"], 1550.0)


if __name__ == "__main__":
    unittest.main()
