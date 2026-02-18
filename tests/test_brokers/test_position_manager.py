"""
Tests for IBKR Position Manager

These tests use mocking to avoid requiring an actual IBKR connection.
"""

import unittest
from unittest.mock import Mock, MagicMock, patch
from datetime import datetime

from copilot_quant.brokers.position_manager import (
    IBKRPositionManager,
    Position,
    PositionChange
)


class TestPosition(unittest.TestCase):
    """Test Position dataclass"""
    
    def test_position_creation(self):
        """Test creating a Position"""
        pos = Position(
            symbol="AAPL",
            quantity=100.0,
            avg_cost=150.0,
            market_price=160.0,
            market_value=16000.0,
            unrealized_pnl=1000.0
        )
        
        self.assertEqual(pos.symbol, "AAPL")
        self.assertEqual(pos.quantity, 100.0)
        self.assertEqual(pos.avg_cost, 150.0)
        self.assertEqual(pos.market_price, 160.0)
        self.assertEqual(pos.unrealized_pnl, 1000.0)
    
    def test_cost_basis_property(self):
        """Test cost_basis property calculation"""
        pos = Position(
            symbol="AAPL",
            quantity=100.0,
            avg_cost=150.0
        )
        
        self.assertEqual(pos.cost_basis, 15000.0)
    
    def test_pnl_percentage_property(self):
        """Test pnl_percentage property calculation"""
        pos = Position(
            symbol="AAPL",
            quantity=100.0,
            avg_cost=150.0,
            unrealized_pnl=1500.0  # 10% gain
        )
        
        self.assertAlmostEqual(pos.pnl_percentage, 10.0, places=2)
    
    def test_pnl_percentage_zero_cost_basis(self):
        """Test pnl_percentage with zero cost basis"""
        pos = Position(
            symbol="AAPL",
            quantity=0.0,
            avg_cost=150.0,
            unrealized_pnl=1000.0
        )
        
        self.assertEqual(pos.pnl_percentage, 0.0)


class TestPositionChange(unittest.TestCase):
    """Test PositionChange dataclass"""
    
    def test_position_change_creation(self):
        """Test creating a PositionChange"""
        change = PositionChange(
            timestamp=datetime.now(),
            symbol="AAPL",
            change_type="opened",
            previous_quantity=0.0,
            new_quantity=100.0
        )
        
        self.assertEqual(change.symbol, "AAPL")
        self.assertEqual(change.change_type, "opened")
        self.assertEqual(change.previous_quantity, 0.0)
        self.assertEqual(change.new_quantity, 100.0)


class TestIBKRPositionManager(unittest.TestCase):
    """Test cases for IBKRPositionManager"""
    
    def setUp(self):
        """Set up test fixtures"""
        # Create mock connection manager
        self.mock_conn_mgr = MagicMock()
        self.mock_ib = MagicMock()
        
        self.mock_conn_mgr.is_connected.return_value = True
        self.mock_conn_mgr.get_ib.return_value = self.mock_ib
        
        # Mock event attributes
        self.mock_ib.positionEvent = MagicMock()
        self.mock_ib.positionEvent.__iadd__ = Mock(return_value=self.mock_ib.positionEvent)
        self.mock_ib.positionEvent.__isub__ = Mock(return_value=self.mock_ib.positionEvent)
    
    def _create_mock_position(self, symbol, quantity, avg_cost, account="DU123456"):
        """Helper to create mock Position from ib_insync"""
        pos = MagicMock()
        pos.contract = MagicMock()
        pos.contract.symbol = symbol
        pos.position = quantity
        pos.avgCost = avg_cost
        pos.account = account
        return pos
    
    def test_initialization_requires_connection(self):
        """Test that initialization requires connected manager"""
        self.mock_conn_mgr.is_connected.return_value = False
        
        with self.assertRaises(RuntimeError) as context:
            IBKRPositionManager(self.mock_conn_mgr)
        
        self.assertIn("must be connected", str(context.exception))
    
    def test_initialization_success(self):
        """Test successful initialization"""
        # Mock positions for auto_sync
        self.mock_ib.positions.return_value = [
            self._create_mock_position("AAPL", 100.0, 150.0),
            self._create_mock_position("GOOGL", 50.0, 2800.0),
        ]
        
        # Mock market data
        self.mock_ib.reqMktData = MagicMock()
        self.mock_ib.cancelMktData = MagicMock()
        self.mock_ib.sleep = MagicMock()
        
        mgr = IBKRPositionManager(self.mock_conn_mgr)
        
        self.assertEqual(len(mgr.positions), 2)
        self.assertIn("AAPL", mgr.positions)
        self.assertIn("GOOGL", mgr.positions)
    
    def test_initialization_without_auto_sync(self):
        """Test initialization without auto sync"""
        mgr = IBKRPositionManager(self.mock_conn_mgr, auto_sync=False)
        
        self.assertEqual(len(mgr.positions), 0)
        self.mock_ib.positions.assert_not_called()
    
    def test_sync_positions_success(self):
        """Test successful position sync"""
        ib_positions = [
            self._create_mock_position("AAPL", 100.0, 150.0),
            self._create_mock_position("MSFT", 200.0, 300.0),
        ]
        self.mock_ib.positions.return_value = ib_positions
        
        # Mock market data
        self.mock_ib.reqMktData = MagicMock()
        self.mock_ib.cancelMktData = MagicMock()
        self.mock_ib.sleep = MagicMock()
        
        mgr = IBKRPositionManager(self.mock_conn_mgr, auto_sync=False)
        result = mgr.sync_positions()
        
        self.assertTrue(result)
        self.assertEqual(len(mgr.positions), 2)
        
        aapl = mgr.positions["AAPL"]
        self.assertEqual(aapl.symbol, "AAPL")
        self.assertEqual(aapl.quantity, 100.0)
        self.assertEqual(aapl.avg_cost, 150.0)
    
    def test_sync_positions_empty(self):
        """Test sync with no positions"""
        self.mock_ib.positions.return_value = []
        
        mgr = IBKRPositionManager(self.mock_conn_mgr, auto_sync=False)
        result = mgr.sync_positions()
        
        self.assertTrue(result)
        self.assertEqual(len(mgr.positions), 0)
    
    def test_sync_positions_error(self):
        """Test sync with error"""
        self.mock_ib.positions.side_effect = Exception("Connection error")
        
        mgr = IBKRPositionManager(self.mock_conn_mgr, auto_sync=False)
        result = mgr.sync_positions()
        
        self.assertFalse(result)
    
    def test_get_positions(self):
        """Test getting all positions"""
        ib_positions = [
            self._create_mock_position("AAPL", 100.0, 150.0),
            self._create_mock_position("GOOGL", 50.0, 2800.0),
        ]
        self.mock_ib.positions.return_value = ib_positions
        self.mock_ib.reqMktData = MagicMock()
        self.mock_ib.cancelMktData = MagicMock()
        self.mock_ib.sleep = MagicMock()
        
        mgr = IBKRPositionManager(self.mock_conn_mgr)
        positions = mgr.get_positions()
        
        self.assertEqual(len(positions), 2)
        symbols = [p.symbol for p in positions]
        self.assertIn("AAPL", symbols)
        self.assertIn("GOOGL", symbols)
    
    def test_get_positions_force_refresh(self):
        """Test getting positions with force refresh"""
        self.mock_ib.positions.return_value = []
        self.mock_ib.reqMktData = MagicMock()
        self.mock_ib.cancelMktData = MagicMock()
        self.mock_ib.sleep = MagicMock()
        
        mgr = IBKRPositionManager(self.mock_conn_mgr, auto_sync=False)
        
        # Add a position manually
        mgr.positions["AAPL"] = Position("AAPL", 100.0, 150.0)
        
        # Force refresh should clear and resync
        positions = mgr.get_positions(force_refresh=True)
        
        self.assertEqual(len(positions), 0)
        self.mock_ib.positions.assert_called()
    
    def test_get_position(self):
        """Test getting specific position"""
        ib_positions = [
            self._create_mock_position("AAPL", 100.0, 150.0),
        ]
        self.mock_ib.positions.return_value = ib_positions
        self.mock_ib.reqMktData = MagicMock()
        self.mock_ib.cancelMktData = MagicMock()
        self.mock_ib.sleep = MagicMock()
        
        mgr = IBKRPositionManager(self.mock_conn_mgr)
        
        aapl = mgr.get_position("AAPL")
        
        self.assertIsNotNone(aapl)
        self.assertEqual(aapl.symbol, "AAPL")
        self.assertEqual(aapl.quantity, 100.0)
    
    def test_get_position_not_found(self):
        """Test getting position that doesn't exist"""
        self.mock_ib.positions.return_value = []
        
        mgr = IBKRPositionManager(self.mock_conn_mgr)
        
        pos = mgr.get_position("NONEXISTENT")
        
        self.assertIsNone(pos)
    
    def test_has_position(self):
        """Test checking if position exists"""
        mgr = IBKRPositionManager(self.mock_conn_mgr, auto_sync=False)
        mgr.positions["AAPL"] = Position("AAPL", 100.0, 150.0)
        
        self.assertTrue(mgr.has_position("AAPL"))
        self.assertFalse(mgr.has_position("GOOGL"))
    
    def test_get_total_market_value(self):
        """Test calculating total market value"""
        mgr = IBKRPositionManager(self.mock_conn_mgr, auto_sync=False)
        
        mgr.positions["AAPL"] = Position("AAPL", 100.0, 150.0, market_value=16000.0)
        mgr.positions["GOOGL"] = Position("GOOGL", 50.0, 2800.0, market_value=145000.0)
        
        total_value = mgr.get_total_market_value()
        
        self.assertEqual(total_value, 161000.0)
    
    def test_get_total_unrealized_pnl(self):
        """Test calculating total unrealized P&L"""
        mgr = IBKRPositionManager(self.mock_conn_mgr, auto_sync=False)
        
        mgr.positions["AAPL"] = Position("AAPL", 100.0, 150.0, unrealized_pnl=1000.0)
        mgr.positions["GOOGL"] = Position("GOOGL", 50.0, 2800.0, unrealized_pnl=-2000.0)
        
        total_pnl = mgr.get_total_unrealized_pnl()
        
        self.assertEqual(total_pnl, -1000.0)
    
    def test_get_long_positions(self):
        """Test getting long positions only"""
        mgr = IBKRPositionManager(self.mock_conn_mgr, auto_sync=False)
        
        mgr.positions["AAPL"] = Position("AAPL", 100.0, 150.0)
        mgr.positions["GOOGL"] = Position("GOOGL", -50.0, 2800.0)
        mgr.positions["MSFT"] = Position("MSFT", 200.0, 300.0)
        
        long_positions = mgr.get_long_positions()
        
        self.assertEqual(len(long_positions), 2)
        symbols = [p.symbol for p in long_positions]
        self.assertIn("AAPL", symbols)
        self.assertIn("MSFT", symbols)
        self.assertNotIn("GOOGL", symbols)
    
    def test_get_short_positions(self):
        """Test getting short positions only"""
        mgr = IBKRPositionManager(self.mock_conn_mgr, auto_sync=False)
        
        mgr.positions["AAPL"] = Position("AAPL", 100.0, 150.0)
        mgr.positions["GOOGL"] = Position("GOOGL", -50.0, 2800.0)
        mgr.positions["TSLA"] = Position("TSLA", -10.0, 700.0)
        
        short_positions = mgr.get_short_positions()
        
        self.assertEqual(len(short_positions), 2)
        symbols = [p.symbol for p in short_positions]
        self.assertIn("GOOGL", symbols)
        self.assertIn("TSLA", symbols)
        self.assertNotIn("AAPL", symbols)
    
    def test_start_monitoring(self):
        """Test starting position monitoring"""
        mgr = IBKRPositionManager(self.mock_conn_mgr, auto_sync=False)
        
        result = mgr.start_monitoring()
        
        self.assertTrue(result)
        self.assertTrue(mgr._monitoring_active)
    
    def test_stop_monitoring(self):
        """Test stopping position monitoring"""
        mgr = IBKRPositionManager(self.mock_conn_mgr, auto_sync=False)
        
        mgr.start_monitoring()
        result = mgr.stop_monitoring()
        
        self.assertTrue(result)
        self.assertFalse(mgr._monitoring_active)
    
    def test_register_update_callback(self):
        """Test registering update callback"""
        mgr = IBKRPositionManager(self.mock_conn_mgr, auto_sync=False)
        
        callback = Mock()
        mgr.register_update_callback(callback)
        
        self.assertIn(callback, mgr._update_callbacks)
    
    def test_unregister_update_callback(self):
        """Test unregistering update callback"""
        mgr = IBKRPositionManager(self.mock_conn_mgr, auto_sync=False)
        
        callback = Mock()
        mgr.register_update_callback(callback)
        mgr.unregister_update_callback(callback)
        
        self.assertNotIn(callback, mgr._update_callbacks)
    
    def test_update_callback_called_on_sync(self):
        """Test that callbacks are called on sync"""
        ib_positions = [
            self._create_mock_position("AAPL", 100.0, 150.0),
        ]
        self.mock_ib.positions.return_value = ib_positions
        self.mock_ib.reqMktData = MagicMock()
        self.mock_ib.cancelMktData = MagicMock()
        self.mock_ib.sleep = MagicMock()
        
        mgr = IBKRPositionManager(self.mock_conn_mgr, auto_sync=False)
        
        callback = Mock()
        mgr.register_update_callback(callback)
        
        mgr.sync_positions()
        
        callback.assert_called_once()
        self.assertIsInstance(callback.call_args[0][0], list)
    
    def test_flag_discrepancy(self):
        """Test flagging position discrepancy"""
        mgr = IBKRPositionManager(self.mock_conn_mgr, auto_sync=False)
        
        mgr.flag_discrepancy("AAPL", expected_quantity=100.0, actual_quantity=95.0)
        
        changes = mgr.get_change_log()
        self.assertEqual(len(changes), 1)
        self.assertEqual(changes[0].symbol, "AAPL")
        self.assertEqual(changes[0].change_type, "discrepancy")
        self.assertEqual(changes[0].previous_quantity, 100.0)
        self.assertEqual(changes[0].new_quantity, 95.0)
    
    def test_change_detection_new_position(self):
        """Test detection of new position"""
        # First sync - empty
        self.mock_ib.positions.return_value = []
        mgr = IBKRPositionManager(self.mock_conn_mgr)
        
        # Second sync - new position
        ib_positions = [
            self._create_mock_position("AAPL", 100.0, 150.0),
        ]
        self.mock_ib.positions.return_value = ib_positions
        self.mock_ib.reqMktData = MagicMock()
        self.mock_ib.cancelMktData = MagicMock()
        self.mock_ib.sleep = MagicMock()
        
        mgr.sync_positions()
        
        changes = mgr.get_change_log()
        opened = [c for c in changes if c.change_type == "opened"]
        self.assertEqual(len(opened), 1)
        self.assertEqual(opened[0].symbol, "AAPL")
    
    def test_change_detection_closed_position(self):
        """Test detection of closed position"""
        # First sync - has position
        ib_positions = [
            self._create_mock_position("AAPL", 100.0, 150.0),
        ]
        self.mock_ib.positions.return_value = ib_positions
        self.mock_ib.reqMktData = MagicMock()
        self.mock_ib.cancelMktData = MagicMock()
        self.mock_ib.sleep = MagicMock()
        
        mgr = IBKRPositionManager(self.mock_conn_mgr)
        
        # Second sync - position closed
        self.mock_ib.positions.return_value = []
        mgr.sync_positions()
        
        changes = mgr.get_change_log()
        closed = [c for c in changes if c.change_type == "closed"]
        self.assertEqual(len(closed), 1)
        self.assertEqual(closed[0].symbol, "AAPL")
    
    def test_change_detection_quantity_change(self):
        """Test detection of quantity change"""
        # First sync
        ib_positions = [
            self._create_mock_position("AAPL", 100.0, 150.0),
        ]
        self.mock_ib.positions.return_value = ib_positions
        self.mock_ib.reqMktData = MagicMock()
        self.mock_ib.cancelMktData = MagicMock()
        self.mock_ib.sleep = MagicMock()
        
        mgr = IBKRPositionManager(self.mock_conn_mgr)
        
        # Second sync - quantity increased
        ib_positions = [
            self._create_mock_position("AAPL", 150.0, 150.0),
        ]
        self.mock_ib.positions.return_value = ib_positions
        mgr.sync_positions()
        
        changes = mgr.get_change_log()
        increased = [c for c in changes if c.change_type == "increased"]
        self.assertEqual(len(increased), 1)
        self.assertEqual(increased[0].symbol, "AAPL")
        self.assertEqual(increased[0].previous_quantity, 100.0)
        self.assertEqual(increased[0].new_quantity, 150.0)
    
    def test_change_log_size_limit(self):
        """Test that change log doesn't grow unbounded"""
        mgr = IBKRPositionManager(self.mock_conn_mgr, auto_sync=False)
        
        # Add many discrepancies
        for i in range(1100):
            mgr.flag_discrepancy("AAPL", 100.0, 100.0 + i)
        
        # Change log should be capped
        changes = mgr.get_change_log()
        self.assertLessEqual(len(changes), 1000)
    
    def test_repr(self):
        """Test string representation"""
        mgr = IBKRPositionManager(self.mock_conn_mgr, auto_sync=False)
        mgr.positions["AAPL"] = Position("AAPL", 100.0, 150.0)
        
        repr_str = repr(mgr)
        
        self.assertIn('IBKRPositionManager', repr_str)
        self.assertIn('positions=1', repr_str)
        self.assertIn('inactive', repr_str)


if __name__ == '__main__':
    unittest.main()
