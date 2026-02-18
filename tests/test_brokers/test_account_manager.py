"""
Tests for IBKR Account Manager

These tests use mocking to avoid requiring an actual IBKR connection.
"""

import unittest
from unittest.mock import Mock, MagicMock, patch
from datetime import datetime

from copilot_quant.brokers.account_manager import (
    IBKRAccountManager,
    AccountSummary
)


class TestAccountSummary(unittest.TestCase):
    """Test AccountSummary dataclass"""
    
    def test_account_summary_creation(self):
        """Test creating an AccountSummary"""
        summary = AccountSummary(
            account_id="DU123456",
            net_liquidation=100000.0,
            total_cash_value=50000.0,
            buying_power=200000.0,
            unrealized_pnl=5000.0,
            realized_pnl=1000.0
        )
        
        self.assertEqual(summary.account_id, "DU123456")
        self.assertEqual(summary.net_liquidation, 100000.0)
        self.assertEqual(summary.total_cash_value, 50000.0)
        self.assertEqual(summary.buying_power, 200000.0)
        self.assertEqual(summary.unrealized_pnl, 5000.0)
        self.assertEqual(summary.realized_pnl, 1000.0)
        self.assertIsInstance(summary.timestamp, datetime)


class TestIBKRAccountManager(unittest.TestCase):
    """Test cases for IBKRAccountManager"""
    
    def setUp(self):
        """Set up test fixtures"""
        # Create mock connection manager
        self.mock_conn_mgr = MagicMock()
        self.mock_ib = MagicMock()
        
        self.mock_conn_mgr.is_connected.return_value = True
        self.mock_conn_mgr.get_ib.return_value = self.mock_ib
        
        # Mock managed accounts
        self.mock_ib.managedAccounts.return_value = ['DU123456']
        
        # Mock event attributes
        self.mock_ib.accountValueEvent = MagicMock()
        self.mock_ib.accountValueEvent.__iadd__ = Mock(return_value=self.mock_ib.accountValueEvent)
        self.mock_ib.accountValueEvent.__isub__ = Mock(return_value=self.mock_ib.accountValueEvent)
    
    def _create_mock_account_value(self, tag, value, currency="USD", account="DU123456"):
        """Helper to create mock AccountValue"""
        av = MagicMock()
        av.tag = tag
        av.value = str(value)
        av.currency = currency
        av.account = account
        return av
    
    def test_initialization_requires_connection(self):
        """Test that initialization requires connected manager"""
        self.mock_conn_mgr.is_connected.return_value = False
        
        with self.assertRaises(RuntimeError) as context:
            IBKRAccountManager(self.mock_conn_mgr)
        
        self.assertIn("must be connected", str(context.exception))
    
    def test_initialization_success(self):
        """Test successful initialization"""
        # Mock account values for auto_sync
        self.mock_ib.accountValues.return_value = [
            self._create_mock_account_value('NetLiquidation', 100000.0),
            self._create_mock_account_value('TotalCashValue', 50000.0),
            self._create_mock_account_value('BuyingPower', 200000.0),
        ]
        
        mgr = IBKRAccountManager(self.mock_conn_mgr)
        
        self.assertEqual(mgr.account_id, 'DU123456')
        self.assertIsNotNone(mgr.last_summary)
        self.assertEqual(mgr.last_summary.account_id, 'DU123456')
    
    def test_initialization_without_auto_sync(self):
        """Test initialization without auto sync"""
        mgr = IBKRAccountManager(self.mock_conn_mgr, auto_sync=False)
        
        self.assertEqual(mgr.account_id, 'DU123456')
        self.assertIsNone(mgr.last_summary)
        self.mock_ib.accountValues.assert_not_called()
    
    def test_sync_account_state_success(self):
        """Test successful account state sync"""
        # Mock account values
        account_values = [
            self._create_mock_account_value('NetLiquidation', 100000.0),
            self._create_mock_account_value('TotalCashValue', 50000.0),
            self._create_mock_account_value('BuyingPower', 200000.0),
            self._create_mock_account_value('UnrealizedPnL', 5000.0),
            self._create_mock_account_value('RealizedPnL', 1000.0),
            self._create_mock_account_value('GrossPositionValue', 50000.0),
            self._create_mock_account_value('AvailableFunds', 150000.0),
        ]
        self.mock_ib.accountValues.return_value = account_values
        
        mgr = IBKRAccountManager(self.mock_conn_mgr, auto_sync=False)
        result = mgr.sync_account_state()
        
        self.assertTrue(result)
        self.assertIsNotNone(mgr.last_summary)
        self.assertEqual(mgr.last_summary.net_liquidation, 100000.0)
        self.assertEqual(mgr.last_summary.total_cash_value, 50000.0)
        self.assertEqual(mgr.last_summary.buying_power, 200000.0)
        self.assertEqual(mgr.last_summary.unrealized_pnl, 5000.0)
        self.assertEqual(mgr.last_summary.realized_pnl, 1000.0)
    
    def test_sync_account_state_no_values(self):
        """Test sync with no account values returned"""
        self.mock_ib.accountValues.return_value = []
        
        mgr = IBKRAccountManager(self.mock_conn_mgr, auto_sync=False)
        result = mgr.sync_account_state()
        
        self.assertFalse(result)
        self.assertIsNone(mgr.last_summary)
    
    def test_sync_account_state_error(self):
        """Test sync with error"""
        self.mock_ib.accountValues.side_effect = Exception("Connection error")
        
        mgr = IBKRAccountManager(self.mock_conn_mgr, auto_sync=False)
        result = mgr.sync_account_state()
        
        self.assertFalse(result)
    
    def test_get_account_summary(self):
        """Test getting account summary"""
        account_values = [
            self._create_mock_account_value('NetLiquidation', 100000.0),
            self._create_mock_account_value('TotalCashValue', 50000.0),
        ]
        self.mock_ib.accountValues.return_value = account_values
        
        mgr = IBKRAccountManager(self.mock_conn_mgr)
        summary = mgr.get_account_summary()
        
        self.assertIsNotNone(summary)
        self.assertEqual(summary.net_liquidation, 100000.0)
    
    def test_get_account_summary_force_refresh(self):
        """Test getting account summary with force refresh"""
        account_values = [
            self._create_mock_account_value('NetLiquidation', 100000.0),
        ]
        self.mock_ib.accountValues.return_value = account_values
        
        mgr = IBKRAccountManager(self.mock_conn_mgr, auto_sync=False)
        
        # First call should trigger sync
        summary = mgr.get_account_summary(force_refresh=True)
        
        self.assertIsNotNone(summary)
        self.mock_ib.accountValues.assert_called()
    
    def test_get_account_value(self):
        """Test getting specific account value"""
        account_values = [
            self._create_mock_account_value('NetLiquidation', 100000.0),
            self._create_mock_account_value('BuyingPower', 200000.0),
        ]
        self.mock_ib.accountValues.return_value = account_values
        
        mgr = IBKRAccountManager(self.mock_conn_mgr)
        
        net_liq = mgr.get_account_value('NetLiquidation')
        buying_power = mgr.get_account_value('BuyingPower')
        
        self.assertEqual(net_liq, 100000.0)
        self.assertEqual(buying_power, 200000.0)
    
    def test_get_account_value_not_found(self):
        """Test getting account value that doesn't exist"""
        self.mock_ib.accountValues.return_value = []
        
        mgr = IBKRAccountManager(self.mock_conn_mgr)
        value = mgr.get_account_value('NonExistent')
        
        self.assertIsNone(value)
    
    def test_get_all_account_values(self):
        """Test getting all account values"""
        account_values = [
            self._create_mock_account_value('NetLiquidation', 100000.0),
            self._create_mock_account_value('BuyingPower', 200000.0),
            self._create_mock_account_value('SomeString', 'NotANumber'),
        ]
        self.mock_ib.accountValues.return_value = account_values
        
        mgr = IBKRAccountManager(self.mock_conn_mgr)
        all_values = mgr.get_all_account_values()
        
        self.assertIn('NetLiquidation', all_values)
        self.assertIn('BuyingPower', all_values)
        self.assertEqual(all_values['NetLiquidation'], 100000.0)
        self.assertEqual(all_values['BuyingPower'], 200000.0)
        self.assertEqual(all_values['SomeString'], 'NotANumber')
    
    def test_start_monitoring(self):
        """Test starting account monitoring"""
        mgr = IBKRAccountManager(self.mock_conn_mgr, auto_sync=False)
        
        result = mgr.start_monitoring()
        
        self.assertTrue(result)
        self.assertTrue(mgr._monitoring_active)
        self.mock_ib.reqAccountUpdates.assert_called_once()
    
    def test_start_monitoring_already_active(self):
        """Test starting monitoring when already active"""
        mgr = IBKRAccountManager(self.mock_conn_mgr, auto_sync=False)
        
        mgr.start_monitoring()
        result = mgr.start_monitoring()
        
        self.assertTrue(result)
        # Should only call once
        self.assertEqual(self.mock_ib.reqAccountUpdates.call_count, 1)
    
    def test_stop_monitoring(self):
        """Test stopping account monitoring"""
        mgr = IBKRAccountManager(self.mock_conn_mgr, auto_sync=False)
        
        mgr.start_monitoring()
        result = mgr.stop_monitoring()
        
        self.assertTrue(result)
        self.assertFalse(mgr._monitoring_active)
    
    def test_register_update_callback(self):
        """Test registering update callback"""
        mgr = IBKRAccountManager(self.mock_conn_mgr, auto_sync=False)
        
        callback = Mock()
        mgr.register_update_callback(callback)
        
        self.assertIn(callback, mgr._update_callbacks)
    
    def test_unregister_update_callback(self):
        """Test unregistering update callback"""
        mgr = IBKRAccountManager(self.mock_conn_mgr, auto_sync=False)
        
        callback = Mock()
        mgr.register_update_callback(callback)
        mgr.unregister_update_callback(callback)
        
        self.assertNotIn(callback, mgr._update_callbacks)
    
    def test_update_callback_called_on_sync(self):
        """Test that callbacks are called on sync"""
        account_values = [
            self._create_mock_account_value('NetLiquidation', 100000.0),
        ]
        self.mock_ib.accountValues.return_value = account_values
        
        mgr = IBKRAccountManager(self.mock_conn_mgr, auto_sync=False)
        
        callback = Mock()
        mgr.register_update_callback(callback)
        
        mgr.sync_account_state()
        
        callback.assert_called_once()
        self.assertIsInstance(callback.call_args[0][0], AccountSummary)
    
    def test_change_detection(self):
        """Test change detection between syncs"""
        # First sync
        account_values_1 = [
            self._create_mock_account_value('NetLiquidation', 100000.0),
            self._create_mock_account_value('UnrealizedPnL', 0.0),
        ]
        self.mock_ib.accountValues.return_value = account_values_1
        
        mgr = IBKRAccountManager(self.mock_conn_mgr)
        
        # Second sync with changes
        account_values_2 = [
            self._create_mock_account_value('NetLiquidation', 105000.0),
            self._create_mock_account_value('UnrealizedPnL', 5000.0),
        ]
        self.mock_ib.accountValues.return_value = account_values_2
        
        mgr.sync_account_state()
        
        # Check change log
        changes = mgr.get_change_log()
        self.assertGreater(len(changes), 0)
        
        # Verify changes were detected
        net_liq_change = [c for c in changes if c['field'] == 'Net Liquidation']
        self.assertEqual(len(net_liq_change), 1)
        self.assertEqual(net_liq_change[0]['previous'], 100000.0)
        self.assertEqual(net_liq_change[0]['current'], 105000.0)
    
    def test_change_log_size_limit(self):
        """Test that change log doesn't grow unbounded"""
        account_values = [
            self._create_mock_account_value('NetLiquidation', 100000.0),
        ]
        self.mock_ib.accountValues.return_value = account_values
        
        mgr = IBKRAccountManager(self.mock_conn_mgr)
        
        # Simulate many changes
        for i in range(1100):
            account_values = [
                self._create_mock_account_value('NetLiquidation', 100000.0 + i),
            ]
            self.mock_ib.accountValues.return_value = account_values
            mgr.sync_account_state()
        
        # Change log should be capped
        changes = mgr.get_change_log()
        self.assertLessEqual(len(changes), 1000)
    
    def test_repr(self):
        """Test string representation"""
        mgr = IBKRAccountManager(self.mock_conn_mgr, auto_sync=False)
        
        repr_str = repr(mgr)
        
        self.assertIn('IBKRAccountManager', repr_str)
        self.assertIn('DU123456', repr_str)
        self.assertIn('inactive', repr_str)


if __name__ == '__main__':
    unittest.main()
