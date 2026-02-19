"""
Tests for IBKR Connection Manager

These tests use mocking to avoid requiring an actual IBKR connection.
"""

import unittest
from datetime import datetime
from unittest.mock import MagicMock, Mock, patch

from copilot_quant.brokers.connection_manager import ConnectionState, IBKRConnectionManager, get_error_tips


class TestIBKRConnectionManager(unittest.TestCase):
    """Test cases for IBKRConnectionManager"""

    def setUp(self):
        """Set up test fixtures"""
        # Patch IB class to avoid actual connection
        self.ib_patcher = patch("copilot_quant.brokers.connection_manager.IB")
        self.mock_ib_class = self.ib_patcher.start()
        self.mock_ib = MagicMock()
        self.mock_ib_class.return_value = self.mock_ib

        # Mock connection status
        self.mock_ib.isConnected.return_value = False

        # Mock event attributes
        self.mock_ib.errorEvent = MagicMock()
        self.mock_ib.disconnectedEvent = MagicMock()
        self.mock_ib.connectedEvent = MagicMock()
        self.mock_ib.errorEvent.__iadd__ = Mock(return_value=self.mock_ib.errorEvent)
        self.mock_ib.disconnectedEvent.__iadd__ = Mock(return_value=self.mock_ib.disconnectedEvent)
        self.mock_ib.connectedEvent.__iadd__ = Mock(return_value=self.mock_ib.connectedEvent)

    def tearDown(self):
        """Clean up after tests"""
        self.ib_patcher.stop()

    def test_initialization_defaults(self):
        """Test manager initialization with default parameters"""
        manager = IBKRConnectionManager()

        self.assertEqual(manager.paper_trading, True)
        self.assertEqual(manager.host, "127.0.0.1")
        self.assertEqual(manager.port, 7497)  # Paper TWS
        self.assertEqual(manager.client_id, 1)
        self.assertEqual(manager.use_gateway, False)
        self.assertEqual(manager.auto_reconnect, True)
        self.assertEqual(manager.state, ConnectionState.DISCONNECTED)

    def test_initialization_custom_params(self):
        """Test manager initialization with custom parameters"""
        manager = IBKRConnectionManager(
            paper_trading=False, host="192.168.1.100", port=7496, client_id=5, use_gateway=True, auto_reconnect=False
        )

        self.assertEqual(manager.paper_trading, False)
        self.assertEqual(manager.host, "192.168.1.100")
        self.assertEqual(manager.port, 7496)
        self.assertEqual(manager.client_id, 5)
        self.assertEqual(manager.use_gateway, True)
        self.assertEqual(manager.auto_reconnect, False)

    def test_port_auto_detection(self):
        """Test automatic port detection based on trading mode"""
        # Paper TWS
        manager = IBKRConnectionManager(paper_trading=True, use_gateway=False)
        self.assertEqual(manager.port, 7497)

        # Live TWS
        manager = IBKRConnectionManager(paper_trading=False, use_gateway=False)
        self.assertEqual(manager.port, 7496)

        # Paper Gateway
        manager = IBKRConnectionManager(paper_trading=True, use_gateway=True)
        self.assertEqual(manager.port, 4002)

        # Live Gateway
        manager = IBKRConnectionManager(paper_trading=False, use_gateway=True)
        self.assertEqual(manager.port, 4001)

    @patch.dict("os.environ", {"IB_HOST": "10.0.0.1", "IB_PORT": "8888", "IB_CLIENT_ID": "99"})
    def test_initialization_from_env(self):
        """Test initialization from environment variables"""
        manager = IBKRConnectionManager()

        self.assertEqual(manager.host, "10.0.0.1")
        self.assertEqual(manager.port, 8888)
        self.assertEqual(manager.client_id, 99)

    def test_connect_success(self):
        """Test successful connection"""
        manager = IBKRConnectionManager()

        # Mock successful connection
        self.mock_ib.isConnected.return_value = True
        self.mock_ib.managedAccounts.return_value = ["DU123456"]

        result = manager.connect(retry_count=1)

        self.assertTrue(result)
        self.assertTrue(manager.is_connected())
        self.assertEqual(manager.state, ConnectionState.CONNECTED)
        self.assertIsNotNone(manager._connected_at)
        self.mock_ib.connect.assert_called_once()

    def test_connect_failure(self):
        """Test connection failure"""
        manager = IBKRConnectionManager()

        # Mock connection failure
        self.mock_ib.isConnected.return_value = False

        with self.assertRaises(ConnectionError):
            manager.connect(retry_count=1)

        self.assertFalse(manager.is_connected())
        self.assertEqual(manager.state, ConnectionState.FAILED)

    def test_connect_retry_logic(self):
        """Test connection retry with exponential backoff"""
        manager = IBKRConnectionManager()

        # Mock first two attempts fail, third succeeds
        self.mock_ib.isConnected.side_effect = [False, False, True]
        self.mock_ib.managedAccounts.return_value = ["DU123456"]

        with patch("copilot_quant.brokers.connection_manager.time.sleep"):
            result = manager.connect(retry_count=3)

        self.assertTrue(result)
        self.assertEqual(self.mock_ib.connect.call_count, 3)

    def test_connect_state_transitions(self):
        """Test state transitions during connection"""
        manager = IBKRConnectionManager()

        # Initial state
        self.assertEqual(manager.state, ConnectionState.DISCONNECTED)

        # Mock successful connection
        self.mock_ib.isConnected.return_value = True
        self.mock_ib.managedAccounts.return_value = ["DU123456"]

        manager.connect(retry_count=1)

        # Should be connected
        self.assertEqual(manager.state, ConnectionState.CONNECTED)

    def test_disconnect(self):
        """Test disconnection"""
        manager = IBKRConnectionManager()

        # Setup connected state
        manager.state = ConnectionState.CONNECTED
        self.mock_ib.isConnected.return_value = True

        manager.disconnect()

        self.assertEqual(manager.state, ConnectionState.DISCONNECTED)
        self.assertIsNotNone(manager._last_disconnect_at)
        self.mock_ib.disconnect.assert_called_once()

    def test_disconnect_when_not_connected(self):
        """Test disconnect when not connected doesn't error"""
        manager = IBKRConnectionManager()

        # Not connected
        self.mock_ib.isConnected.return_value = False

        # Should not raise error
        manager.disconnect()

        self.mock_ib.disconnect.assert_not_called()

    def test_reconnect_success(self):
        """Test successful reconnection"""
        manager = IBKRConnectionManager()

        # Mock successful reconnection
        self.mock_ib.isConnected.side_effect = [True, False, True]  # disconnect check, then reconnect
        self.mock_ib.managedAccounts.return_value = ["DU123456"]

        with patch("copilot_quant.brokers.connection_manager.time.sleep"):
            result = manager.reconnect()

        self.assertTrue(result)
        self.assertEqual(manager.state, ConnectionState.CONNECTED)
        self.assertEqual(manager._reconnect_count, 1)

    def test_reconnect_failure(self):
        """Test reconnection failure"""
        manager = IBKRConnectionManager()

        # Mock failed reconnection
        self.mock_ib.isConnected.return_value = False

        with patch("copilot_quant.brokers.connection_manager.time.sleep"):
            result = manager.reconnect()

        self.assertFalse(result)

    def test_reconnect_count_increments(self):
        """Test reconnect count increments on each attempt"""
        manager = IBKRConnectionManager()

        # Mock disconnected state for both reconnect attempts
        self.mock_ib.isConnected.return_value = False

        with patch("copilot_quant.brokers.connection_manager.time.sleep"):
            manager.reconnect()
            self.assertEqual(manager._reconnect_count, 1)

            manager.reconnect()
            self.assertEqual(manager._reconnect_count, 2)

    def test_is_connected(self):
        """Test is_connected method"""
        manager = IBKRConnectionManager()

        # Initially not connected
        self.assertFalse(manager.is_connected())

        # Mock connected state
        manager.state = ConnectionState.CONNECTED
        self.mock_ib.isConnected.return_value = True

        self.assertTrue(manager.is_connected())

        # Mock disconnected
        self.mock_ib.isConnected.return_value = False

        self.assertFalse(manager.is_connected())

    def test_get_ib_when_connected(self):
        """Test getting IB instance when connected"""
        manager = IBKRConnectionManager()

        # Mock connected state
        manager.state = ConnectionState.CONNECTED
        self.mock_ib.isConnected.return_value = True

        ib = manager.get_ib()

        self.assertIs(ib, self.mock_ib)

    def test_get_ib_when_not_connected(self):
        """Test getting IB instance when not connected raises error"""
        manager = IBKRConnectionManager()

        with self.assertRaises(RuntimeError) as context:
            manager.get_ib()

        self.assertIn("Not connected", str(context.exception))

    def test_get_status_disconnected(self):
        """Test getting status when disconnected"""
        manager = IBKRConnectionManager()

        status = manager.get_status()

        self.assertEqual(status["state"], "disconnected")
        self.assertFalse(status["connected"])
        self.assertEqual(status["host"], "127.0.0.1")
        self.assertEqual(status["port"], 7497)
        self.assertEqual(status["client_id"], 1)
        self.assertTrue(status["paper_trading"])
        self.assertIsNone(status["connected_at"])
        self.assertIsNone(status["uptime_seconds"])
        self.assertEqual(status["reconnect_count"], 0)
        self.assertIsNone(status["accounts"])

    def test_get_status_connected(self):
        """Test getting status when connected"""
        manager = IBKRConnectionManager()

        # Mock connected state
        manager.state = ConnectionState.CONNECTED
        self.mock_ib.isConnected.return_value = True
        self.mock_ib.managedAccounts.return_value = ["DU123456", "DU789012"]
        manager._connected_at = datetime.now()
        manager._reconnect_count = 2

        status = manager.get_status()

        self.assertEqual(status["state"], "connected")
        self.assertTrue(status["connected"])
        self.assertIsNotNone(status["connected_at"])
        self.assertIsNotNone(status["uptime_seconds"])
        self.assertGreaterEqual(status["uptime_seconds"], 0)
        self.assertEqual(status["reconnect_count"], 2)
        self.assertEqual(status["accounts"], ["DU123456", "DU789012"])

    def test_disconnect_handlers(self):
        """Test disconnect handler registration and calling"""
        manager = IBKRConnectionManager()

        # Register handlers
        handler1 = Mock()
        handler2 = Mock()
        manager.add_disconnect_handler(handler1)
        manager.add_disconnect_handler(handler2)

        # Trigger disconnect event
        manager._on_disconnect()

        # Check handlers were called
        handler1.assert_called_once()
        handler2.assert_called_once()

    def test_connect_handlers(self):
        """Test connect handler registration and calling"""
        manager = IBKRConnectionManager()

        # Register handlers
        handler1 = Mock()
        handler2 = Mock()
        manager.add_connect_handler(handler1)
        manager.add_connect_handler(handler2)

        # Trigger connect event
        manager._on_connect()

        # Check handlers were called
        handler1.assert_called_once()
        handler2.assert_called_once()

    def test_handler_error_doesnt_break_flow(self):
        """Test that errors in handlers don't break the flow"""
        manager = IBKRConnectionManager()

        # Register handlers, one that raises an error
        handler1 = Mock(side_effect=Exception("Handler error"))
        handler2 = Mock()
        manager.add_disconnect_handler(handler1)
        manager.add_disconnect_handler(handler2)

        # Trigger disconnect event - should not raise
        manager._on_disconnect()

        # Both handlers should have been called
        handler1.assert_called_once()
        handler2.assert_called_once()

    def test_on_disconnect_updates_state(self):
        """Test disconnect event handler updates state"""
        manager = IBKRConnectionManager(auto_reconnect=False)
        manager.state = ConnectionState.CONNECTED

        manager._on_disconnect()

        self.assertEqual(manager.state, ConnectionState.DISCONNECTED)
        self.assertIsNotNone(manager._last_disconnect_at)

    def test_on_disconnect_auto_reconnect(self):
        """Test auto-reconnect on disconnect"""
        manager = IBKRConnectionManager(auto_reconnect=True)

        # Mock successful reconnection
        self.mock_ib.isConnected.side_effect = [True, False, True]
        self.mock_ib.managedAccounts.return_value = ["DU123456"]

        with patch("copilot_quant.brokers.connection_manager.time.sleep"):
            manager._on_disconnect()

        # Should have attempted reconnection
        self.assertEqual(manager._reconnect_count, 1)

    def test_on_connect_updates_state(self):
        """Test connect event handler updates state"""
        manager = IBKRConnectionManager()

        manager._on_connect()

        self.assertEqual(manager.state, ConnectionState.CONNECTED)
        self.assertIsNotNone(manager._connected_at)

    def test_error_handling_info_messages(self):
        """Test error handler filters info messages correctly"""
        manager = IBKRConnectionManager()

        # Info messages should be logged as debug
        manager._on_error(1, 2104, "Market data farm connection is OK", None)
        manager._on_error(1, 2106, "HMDS data farm connection is OK", None)
        manager._on_error(1, 2158, "Sec-def data farm connection is OK", None)

        # Should not change state
        self.assertEqual(manager.state, ConnectionState.DISCONNECTED)

    def test_error_handling_connection_lost(self):
        """Test error handler for connection lost"""
        manager = IBKRConnectionManager()
        manager.state = ConnectionState.CONNECTED

        # Connection lost error
        manager._on_error(1, 1100, "Connectivity lost", None)

        self.assertEqual(manager.state, ConnectionState.DISCONNECTED)

    def test_error_handling_connection_restored(self):
        """Test error handler for connection restored"""
        manager = IBKRConnectionManager()
        manager.state = ConnectionState.DISCONNECTED

        # Connection restored
        manager._on_error(1, 1101, "Connectivity restored", None)

        self.assertEqual(manager.state, ConnectionState.CONNECTED)

    def test_error_handling_connection_error(self):
        """Test error handler for connection errors"""
        manager = IBKRConnectionManager()

        # Connection error
        manager._on_error(1, 502, "Couldn't connect to TWS", None)

        self.assertEqual(manager.state, ConnectionState.FAILED)

    def test_context_manager(self):
        """Test using manager as context manager"""
        self.mock_ib.isConnected.return_value = True
        self.mock_ib.managedAccounts.return_value = ["DU123456"]

        with IBKRConnectionManager() as manager:
            self.assertTrue(manager.is_connected())

        self.mock_ib.connect.assert_called()
        self.mock_ib.disconnect.assert_called()

    def test_repr(self):
        """Test string representation"""
        manager = IBKRConnectionManager(host="127.0.0.1", port=7497, paper_trading=True)

        repr_str = repr(manager)

        self.assertIn("IBKRConnectionManager", repr_str)
        self.assertIn("127.0.0.1", repr_str)
        self.assertIn("7497", repr_str)
        self.assertIn("paper_trading=True", repr_str)


class TestErrorPatterns(unittest.TestCase):
    """Test error pattern documentation"""

    def test_get_error_tips_known_error(self):
        """Test getting tips for known error code"""
        tips = get_error_tips(502)

        self.assertIn("description", tips)
        self.assertIn("tips", tips)
        self.assertEqual(tips["description"], "Couldn't connect to TWS")
        self.assertIsInstance(tips["tips"], list)
        self.assertGreater(len(tips["tips"]), 0)

    def test_get_error_tips_unknown_error(self):
        """Test getting tips for unknown error code"""
        tips = get_error_tips(99999)

        self.assertEqual(tips, {})

    def test_error_patterns_comprehensive(self):
        """Test that common error codes are documented"""
        from copilot_quant.brokers.connection_manager import ERROR_PATTERNS

        # Check common error codes are present
        self.assertIn(502, ERROR_PATTERNS)  # Can't connect to TWS
        self.assertIn(504, ERROR_PATTERNS)  # Not connected
        self.assertIn(1100, ERROR_PATTERNS)  # Connection lost
        self.assertIn(1101, ERROR_PATTERNS)  # Connection restored
        self.assertIn(200, ERROR_PATTERNS)  # No security definition

        # Check each pattern has required fields
        for _code, pattern in ERROR_PATTERNS.items():
            self.assertIn("description", pattern)
            self.assertIn("tips", pattern)
            self.assertIsInstance(pattern["tips"], list)


class TestConnectionManagerWithTradingModeConfig(unittest.TestCase):
    """Test cases for IBKRConnectionManager with TradingModeConfig"""

    def setUp(self):
        """Set up test fixtures"""
        # Patch IB class to avoid actual connection
        self.ib_patcher = patch("copilot_quant.brokers.connection_manager.IB")
        self.mock_ib_class = self.ib_patcher.start()
        self.mock_ib = MagicMock()
        self.mock_ib_class.return_value = self.mock_ib

        # Mock connection status
        self.mock_ib.isConnected.return_value = False

        # Mock event attributes
        self.mock_ib.errorEvent = MagicMock()
        self.mock_ib.disconnectedEvent = MagicMock()
        self.mock_ib.connectedEvent = MagicMock()
        self.mock_ib.errorEvent.__iadd__ = Mock(return_value=self.mock_ib.errorEvent)
        self.mock_ib.disconnectedEvent.__iadd__ = Mock(return_value=self.mock_ib.disconnectedEvent)
        self.mock_ib.connectedEvent.__iadd__ = Mock(return_value=self.mock_ib.connectedEvent)

    def tearDown(self):
        """Clean up after tests"""
        self.ib_patcher.stop()

    def test_connection_manager_with_paper_config(self):
        """Test connection manager initialized with paper trading config"""
        from copilot_quant.config.trading_mode import TradingMode, TradingModeConfig

        config = TradingModeConfig(
            mode=TradingMode.PAPER, host="127.0.0.1", port=7497, client_id=1, account_number="DU123456"
        )

        manager = IBKRConnectionManager(trading_mode_config=config)

        self.assertEqual(manager.host, "127.0.0.1")
        self.assertEqual(manager.port, 7497)
        self.assertEqual(manager.client_id, 1)
        self.assertTrue(manager.paper_trading)
        self.assertFalse(manager.use_gateway)

    def test_connection_manager_with_live_config(self):
        """Test connection manager initialized with live trading config"""
        from copilot_quant.config.trading_mode import TradingMode, TradingModeConfig

        config = TradingModeConfig(
            mode=TradingMode.LIVE,
            host="127.0.0.1",
            port=7496,
            client_id=2,
            account_number="U7654321",
            use_gateway=False,
        )

        manager = IBKRConnectionManager(trading_mode_config=config)

        self.assertEqual(manager.host, "127.0.0.1")
        self.assertEqual(manager.port, 7496)
        self.assertEqual(manager.client_id, 2)
        self.assertFalse(manager.paper_trading)
        self.assertFalse(manager.use_gateway)

    def test_config_overrides_individual_params(self):
        """Test that trading_mode_config overrides individual parameters"""
        from copilot_quant.config.trading_mode import TradingMode, TradingModeConfig

        config = TradingModeConfig(mode=TradingMode.LIVE, host="192.168.1.100", port=9999, client_id=99)

        # Pass both config and individual params - config should win
        manager = IBKRConnectionManager(
            trading_mode_config=config,
            paper_trading=True,  # Should be overridden
            host="10.0.0.1",  # Should be overridden
            port=8888,  # Should be overridden
            client_id=1,  # Should be overridden
        )

        # Config values should be used
        self.assertEqual(manager.host, "192.168.1.100")
        self.assertEqual(manager.port, 9999)
        self.assertEqual(manager.client_id, 99)
        self.assertFalse(manager.paper_trading)  # From config (LIVE mode)


if __name__ == "__main__":
    unittest.main()
