"""
Tests for Trading Mode Configuration

Tests the trading mode configuration module including separate
paper/live configurations and mode switching.
"""

import os
import unittest
from unittest.mock import patch

from copilot_quant.config.trading_mode import (
    TradingMode,
    TradingModeConfig,
    TradingModeManager,
    get_trading_mode_config,
)


class TestTradingModeConfig(unittest.TestCase):
    """Test cases for TradingModeConfig"""

    def test_paper_config_creation(self):
        """Test creating a paper trading configuration"""
        config = TradingModeConfig(mode=TradingMode.PAPER, host="127.0.0.1", port=7497, client_id=1)

        self.assertEqual(config.mode, TradingMode.PAPER)
        self.assertTrue(config.is_paper)
        self.assertFalse(config.is_live)
        self.assertEqual(config.host, "127.0.0.1")
        self.assertEqual(config.port, 7497)
        self.assertEqual(config.client_id, 1)

    def test_live_config_creation(self):
        """Test creating a live trading configuration"""
        config = TradingModeConfig(
            mode=TradingMode.LIVE, host="127.0.0.1", port=7496, client_id=2, account_number="U1234567"
        )

        self.assertEqual(config.mode, TradingMode.LIVE)
        self.assertFalse(config.is_paper)
        self.assertTrue(config.is_live)
        self.assertEqual(config.port, 7496)
        self.assertEqual(config.account_number, "U1234567")

    def test_gateway_config(self):
        """Test configuration with IB Gateway"""
        config = TradingModeConfig(mode=TradingMode.PAPER, host="127.0.0.1", port=4002, client_id=1, use_gateway=True)

        self.assertTrue(config.use_gateway)
        self.assertEqual(config.port, 4002)

    def test_to_dict(self):
        """Test converting configuration to dictionary"""
        config = TradingModeConfig(
            mode=TradingMode.PAPER, host="127.0.0.1", port=7497, client_id=1, account_number="DU123456"
        )

        config_dict = config.to_dict()

        self.assertEqual(config_dict["mode"], "paper")
        self.assertEqual(config_dict["host"], "127.0.0.1")
        self.assertEqual(config_dict["port"], 7497)
        self.assertEqual(config_dict["client_id"], 1)
        self.assertEqual(config_dict["account_number"], "DU123456")

    def test_invalid_mode(self):
        """Test that invalid mode raises error"""
        with self.assertRaises(ValueError):
            TradingModeConfig(
                mode="invalid",  # Should be TradingMode enum
                host="127.0.0.1",
                port=7497,
                client_id=1,
            )


class TestGetTradingModeConfig(unittest.TestCase):
    """Test cases for get_trading_mode_config function"""

    @patch.dict(os.environ, {}, clear=True)
    def test_paper_config_defaults(self):
        """Test paper config with default values"""
        config = get_trading_mode_config(TradingMode.PAPER)

        self.assertEqual(config.mode, TradingMode.PAPER)
        self.assertEqual(config.host, "127.0.0.1")
        self.assertEqual(config.port, 7497)  # Default TWS paper port
        self.assertEqual(config.client_id, 1)
        self.assertFalse(config.use_gateway)

    @patch.dict(os.environ, {}, clear=True)
    def test_live_config_defaults(self):
        """Test live config with default values"""
        config = get_trading_mode_config(TradingMode.LIVE)

        self.assertEqual(config.mode, TradingMode.LIVE)
        self.assertEqual(config.host, "127.0.0.1")
        self.assertEqual(config.port, 7496)  # Default TWS live port
        self.assertEqual(config.client_id, 2)
        self.assertFalse(config.use_gateway)

    @patch.dict(
        os.environ,
        {
            "IB_PAPER_HOST": "192.168.1.100",
            "IB_PAPER_PORT": "8888",
            "IB_PAPER_CLIENT_ID": "10",
            "IB_PAPER_ACCOUNT": "DU123456",
        },
    )
    def test_paper_config_from_env(self):
        """Test paper config loaded from environment variables"""
        config = get_trading_mode_config(TradingMode.PAPER)

        self.assertEqual(config.host, "192.168.1.100")
        self.assertEqual(config.port, 8888)
        self.assertEqual(config.client_id, 10)
        self.assertEqual(config.account_number, "DU123456")

    @patch.dict(
        os.environ,
        {"IB_LIVE_HOST": "10.0.0.1", "IB_LIVE_PORT": "9999", "IB_LIVE_CLIENT_ID": "20", "IB_LIVE_ACCOUNT": "U7654321"},
    )
    def test_live_config_from_env(self):
        """Test live config loaded from environment variables"""
        config = get_trading_mode_config(TradingMode.LIVE)

        self.assertEqual(config.host, "10.0.0.1")
        self.assertEqual(config.port, 9999)
        self.assertEqual(config.client_id, 20)
        self.assertEqual(config.account_number, "U7654321")

    @patch.dict(os.environ, {"IB_HOST": "192.168.1.100", "IB_PORT": "7777", "IB_CLIENT_ID": "5"})
    def test_legacy_env_vars_fallback(self):
        """Test that legacy env vars work as fallback for paper mode"""
        config = get_trading_mode_config(TradingMode.PAPER)

        # Should use legacy vars as fallback
        self.assertEqual(config.host, "192.168.1.100")
        self.assertEqual(config.port, 7777)
        self.assertEqual(config.client_id, 5)

    @patch.dict(os.environ, {"IB_PAPER_USE_GATEWAY": "true"})
    def test_gateway_mode_from_env(self):
        """Test gateway mode configuration from env"""
        config = get_trading_mode_config(TradingMode.PAPER)

        self.assertTrue(config.use_gateway)
        self.assertEqual(config.port, 4002)  # Gateway paper port

    @patch.dict(os.environ, {"IB_LIVE_USE_GATEWAY": "true"})
    def test_live_gateway_mode_from_env(self):
        """Test live gateway mode configuration from env"""
        config = get_trading_mode_config(TradingMode.LIVE)

        self.assertTrue(config.use_gateway)
        self.assertEqual(config.port, 4001)  # Gateway live port


class TestTradingModeManager(unittest.TestCase):
    """Test cases for TradingModeManager"""

    def test_initialization_defaults_to_paper(self):
        """Test manager initializes to paper mode by default"""
        manager = TradingModeManager()

        self.assertEqual(manager.current_mode, TradingMode.PAPER)
        self.assertTrue(manager.is_paper_mode())
        self.assertFalse(manager.is_live_mode())

    def test_initialization_with_custom_mode(self):
        """Test manager can initialize with custom mode"""
        manager = TradingModeManager(default_mode=TradingMode.LIVE)

        self.assertEqual(manager.current_mode, TradingMode.LIVE)
        self.assertTrue(manager.is_live_mode())
        self.assertFalse(manager.is_paper_mode())

    def test_get_current_config(self):
        """Test getting configuration for current mode"""
        manager = TradingModeManager()
        config = manager.current_config

        self.assertIsInstance(config, TradingModeConfig)
        self.assertEqual(config.mode, TradingMode.PAPER)

    def test_switch_to_paper_mode(self):
        """Test switching to paper mode"""
        manager = TradingModeManager(default_mode=TradingMode.LIVE)

        # Switch from live to paper (no confirmation needed)
        result = manager.switch_mode(TradingMode.PAPER)

        self.assertTrue(result)
        self.assertEqual(manager.current_mode, TradingMode.PAPER)
        self.assertTrue(manager.is_paper_mode())

    def test_switch_to_live_mode_requires_confirmation(self):
        """Test switching to live mode requires confirmation"""
        manager = TradingModeManager()

        # Attempt to switch without confirmation should raise error
        with self.assertRaises(ValueError) as context:
            manager.switch_mode(TradingMode.LIVE, confirmed=False)

        self.assertIn("requires explicit confirmation", str(context.exception))
        # Mode should remain paper
        self.assertEqual(manager.current_mode, TradingMode.PAPER)

    def test_switch_to_live_mode_with_confirmation(self):
        """Test switching to live mode with confirmation"""
        manager = TradingModeManager()

        # Switch with confirmation should succeed
        result = manager.switch_mode(TradingMode.LIVE, confirmed=True)

        self.assertTrue(result)
        self.assertEqual(manager.current_mode, TradingMode.LIVE)
        self.assertTrue(manager.is_live_mode())

    def test_switch_to_same_mode_returns_false(self):
        """Test switching to current mode returns False"""
        manager = TradingModeManager()

        # Try to switch to paper when already in paper
        result = manager.switch_mode(TradingMode.PAPER)

        self.assertFalse(result)
        self.assertEqual(manager.current_mode, TradingMode.PAPER)

    def test_mode_history_tracking(self):
        """Test that mode changes are tracked in history"""
        manager = TradingModeManager()

        # Initial state should have one entry
        history = manager.get_mode_history()
        self.assertEqual(len(history), 1)
        self.assertEqual(history[0][1], TradingMode.PAPER)

        # Switch to live
        manager.switch_mode(TradingMode.LIVE, confirmed=True)
        history = manager.get_mode_history()
        self.assertEqual(len(history), 2)
        self.assertEqual(history[1][1], TradingMode.LIVE)

        # Switch back to paper
        manager.switch_mode(TradingMode.PAPER)
        history = manager.get_mode_history()
        self.assertEqual(len(history), 3)
        self.assertEqual(history[2][1], TradingMode.PAPER)

    def test_mode_history_includes_timestamps(self):
        """Test that mode history includes timestamps"""
        manager = TradingModeManager()
        history = manager.get_mode_history()

        # Each entry should be a tuple of (datetime, mode)
        self.assertEqual(len(history[0]), 2)
        self.assertIsNotNone(history[0][0])  # Timestamp
        self.assertEqual(history[0][1], TradingMode.PAPER)  # Mode


if __name__ == "__main__":
    unittest.main()
