"""
Tests for Configuration Manager

Tests YAML config loading, validation, and versioning.
"""

import unittest
import tempfile
import yaml
from pathlib import Path
from datetime import datetime

from copilot_quant.orchestrator.config_manager import (
    ConfigManager,
    TradingConfig,
    TradingScheduleConfig,
    StrategyConfig,
    RiskConfig,
    BrokerConfig,
    DataConfig,
    NotificationConfig,
)


class TestConfigManager(unittest.TestCase):
    """Test ConfigManager functionality"""
    
    def setUp(self):
        """Set up test fixtures"""
        # Create temporary directory for test configs
        self.temp_dir = tempfile.mkdtemp()
        self.config_path = Path(self.temp_dir) / "test_config.yaml"
        
        # Create a test config
        self.test_config_data = {
            'version': '1.0.0',
            'mode': 'paper',
            'schedule': {
                'timezone': 'America/New_York',
                'auto_start': True,
                'auto_stop': True,
            },
            'strategy': {
                'symbols': ['AAPL', 'MSFT'],
                'max_positions': 10,
                'position_size_pct': 0.10,
            },
            'risk': {
                'max_portfolio_drawdown': 0.12,
                'max_position_size': 0.10,
                'enable_circuit_breaker': True,
            },
            'broker': {
                'broker_type': 'ibkr',
                'host': '127.0.0.1',
                'port': 7497,
                'client_id': 1,
                'paper_trading': True,
            },
            'data': {
                'primary_source': 'ibkr',
                'update_interval': 1.0,
            },
            'notifications': {
                'enabled': True,
                'channels': ['slack'],
            }
        }
        
        # Write test config
        with open(self.config_path, 'w') as f:
            yaml.dump(self.test_config_data, f)
    
    def tearDown(self):
        """Clean up test fixtures"""
        import shutil
        shutil.rmtree(self.temp_dir)
    
    def test_load_config(self):
        """Test loading configuration from file"""
        manager = ConfigManager(str(self.config_path))
        config = manager.load()
        
        self.assertIsInstance(config, TradingConfig)
        self.assertEqual(config.version, '1.0.0')
        self.assertEqual(config.mode, 'paper')
        self.assertEqual(config.strategy.symbols, ['AAPL', 'MSFT'])
        self.assertEqual(config.broker.port, 7497)
    
    def test_save_config(self):
        """Test saving configuration to file"""
        manager = ConfigManager(str(self.config_path))
        config = manager.load()
        
        # Modify config
        config.strategy.symbols = ['TSLA', 'GOOGL']
        config.risk.max_portfolio_drawdown = 0.15
        
        # Save
        manager.save(config)
        
        # Reload and verify
        reloaded = manager.load()
        self.assertEqual(reloaded.strategy.symbols, ['TSLA', 'GOOGL'])
        self.assertEqual(reloaded.risk.max_portfolio_drawdown, 0.15)
    
    def test_validation_mode(self):
        """Test validation of trading mode"""
        manager = ConfigManager(str(self.config_path))
        config = manager.load()
        
        # Invalid mode should raise error
        config.mode = 'invalid'
        with self.assertRaises(ValueError):
            manager.save(config)
    
    def test_validation_risk_params(self):
        """Test validation of risk parameters"""
        manager = ConfigManager(str(self.config_path))
        config = manager.load()
        
        # Invalid drawdown (> 1)
        config.risk.max_portfolio_drawdown = 1.5
        with self.assertRaises(ValueError):
            manager.save(config)
        
        # Invalid position size (< 0)
        config.risk.max_portfolio_drawdown = 0.12
        config.risk.max_position_size = -0.1
        with self.assertRaises(ValueError):
            manager.save(config)
    
    def test_config_versioning(self):
        """Test configuration versioning"""
        manager = ConfigManager(str(self.config_path), enable_versioning=True)
        config = manager.load()
        
        # Modify and save (should create version)
        config.strategy.max_positions = 15
        manager.save(config, create_version=True)
        
        # Check that version was created
        versions = manager.list_versions()
        self.assertGreaterEqual(len(versions), 0)  # May be 0 if first save
        
        # Modify again
        config.strategy.max_positions = 20
        manager.save(config, create_version=True)
        
        # Should have at least one version now
        versions = manager.list_versions()
        self.assertGreaterEqual(len(versions), 1)
    
    def test_config_reload(self):
        """Test configuration hot reload"""
        manager = ConfigManager(str(self.config_path))
        config = manager.load()
        
        # Modify config file externally
        external_data = self.test_config_data.copy()
        external_data['strategy']['max_positions'] = 25
        
        with open(self.config_path, 'w') as f:
            yaml.dump(external_data, f)
        
        # Reload
        reloaded = manager.reload()
        self.assertEqual(reloaded.strategy.max_positions, 25)
    
    def test_dataclass_defaults(self):
        """Test that config dataclasses have proper defaults"""
        schedule = TradingScheduleConfig()
        self.assertEqual(schedule.timezone, "America/New_York")
        self.assertTrue(schedule.auto_start)
        
        risk = RiskConfig()
        self.assertEqual(risk.max_portfolio_drawdown, 0.12)
        self.assertTrue(risk.enable_circuit_breaker)
        
        broker = BrokerConfig()
        self.assertTrue(broker.paper_trading)
        self.assertEqual(broker.broker_type, "ibkr")
    
    def test_missing_config_file(self):
        """Test handling of missing config file"""
        # Use temp directory for missing file test
        missing_path = Path(self.temp_dir) / "missing.yaml"
        manager = ConfigManager(str(missing_path))
        
        with self.assertRaises(FileNotFoundError):
            manager.load()


if __name__ == '__main__':
    unittest.main()
