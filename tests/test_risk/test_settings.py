"""Tests for RiskSettings configuration."""

import json
import tempfile
from pathlib import Path

import pytest

from src.risk.settings import RiskSettings


class TestRiskSettings:
    """Test RiskSettings dataclass and validation."""

    def test_default_settings(self):
        """Test that default settings are valid."""
        settings = RiskSettings()

        assert settings.max_portfolio_drawdown == 0.12
        assert settings.max_position_size == 0.10
        assert settings.min_cash_buffer == 0.20
        assert settings.max_cash_buffer == 0.80
        assert settings.position_stop_loss == 0.05
        assert settings.enable_volatility_targeting is True
        assert settings.target_portfolio_volatility == 0.15
        assert settings.max_correlation == 0.80
        assert settings.max_positions == 10
        assert settings.enable_circuit_breaker is True
        assert settings.circuit_breaker_threshold == 0.10

    def test_conservative_profile(self):
        """Test conservative profile matches defaults."""
        settings = RiskSettings.get_conservative_profile()
        default_settings = RiskSettings()

        assert settings.to_dict() == default_settings.to_dict()

    def test_balanced_profile(self):
        """Test balanced profile has expected values."""
        settings = RiskSettings.get_balanced_profile()

        assert settings.max_portfolio_drawdown == 0.15
        assert settings.max_position_size == 0.15
        assert settings.min_cash_buffer == 0.15
        assert settings.position_stop_loss == 0.07
        assert settings.max_positions == 15

    def test_aggressive_profile(self):
        """Test aggressive profile has expected values."""
        settings = RiskSettings.get_aggressive_profile()

        assert settings.max_portfolio_drawdown == 0.20
        assert settings.max_position_size == 0.20
        assert settings.min_cash_buffer == 0.10
        assert settings.position_stop_loss == 0.10
        assert settings.max_positions == 20

    def test_invalid_max_portfolio_drawdown(self):
        """Test that invalid drawdown raises ValueError."""
        with pytest.raises(ValueError, match="max_portfolio_drawdown must be between 0 and 1"):
            RiskSettings(max_portfolio_drawdown=-0.1)

        with pytest.raises(ValueError, match="max_portfolio_drawdown must be between 0 and 1"):
            RiskSettings(max_portfolio_drawdown=1.5)

        with pytest.raises(ValueError, match="max_portfolio_drawdown must be between 0 and 1"):
            RiskSettings(max_portfolio_drawdown=0)

    def test_invalid_cash_buffer(self):
        """Test that invalid cash buffer raises ValueError."""
        with pytest.raises(ValueError, match="min_cash_buffer must be between 0 and 1"):
            RiskSettings(min_cash_buffer=-0.1)

        with pytest.raises(ValueError, match="max_cash_buffer must be between 0 and 1"):
            RiskSettings(max_cash_buffer=1.5)

    def test_min_greater_than_max_cash(self):
        """Test that min cash > max cash raises ValueError."""
        with pytest.raises(ValueError, match="min_cash_buffer.*cannot be greater than max_cash_buffer"):
            RiskSettings(min_cash_buffer=0.5, max_cash_buffer=0.3)

    def test_invalid_position_size(self):
        """Test that invalid position size raises ValueError."""
        with pytest.raises(ValueError, match="max_position_size must be between 0 and 1"):
            RiskSettings(max_position_size=0)

        with pytest.raises(ValueError, match="max_position_size must be between 0 and 1"):
            RiskSettings(max_position_size=1.5)

    def test_invalid_stop_loss(self):
        """Test that invalid stop loss raises ValueError."""
        with pytest.raises(ValueError, match="position_stop_loss must be between 0 and 1"):
            RiskSettings(position_stop_loss=0)

        with pytest.raises(ValueError, match="position_stop_loss must be between 0 and 1"):
            RiskSettings(position_stop_loss=1.5)

    def test_invalid_correlation(self):
        """Test that invalid correlation raises ValueError."""
        with pytest.raises(ValueError, match="max_correlation must be between 0 and 1"):
            RiskSettings(max_correlation=-0.1)

        with pytest.raises(ValueError, match="max_correlation must be between 0 and 1"):
            RiskSettings(max_correlation=1.5)

    def test_invalid_volatility(self):
        """Test that invalid volatility raises ValueError."""
        with pytest.raises(ValueError, match="target_portfolio_volatility must be between 0 and 1"):
            RiskSettings(target_portfolio_volatility=0)

        with pytest.raises(ValueError, match="target_portfolio_volatility must be between 0 and 1"):
            RiskSettings(target_portfolio_volatility=1.5)

    def test_invalid_max_positions(self):
        """Test that invalid max positions raises ValueError."""
        with pytest.raises(ValueError, match="max_positions must be at least 1"):
            RiskSettings(max_positions=0)

    def test_circuit_breaker_exceeds_drawdown(self):
        """Test that circuit breaker > max drawdown raises ValueError."""
        with pytest.raises(ValueError, match="circuit_breaker_threshold.*cannot exceed max_portfolio_drawdown"):
            RiskSettings(max_portfolio_drawdown=0.10, circuit_breaker_threshold=0.15)

    def test_to_dict(self):
        """Test conversion to dictionary."""
        settings = RiskSettings()
        settings_dict = settings.to_dict()

        assert isinstance(settings_dict, dict)
        assert settings_dict["max_portfolio_drawdown"] == 0.12
        assert settings_dict["max_position_size"] == 0.10
        assert settings_dict["enable_circuit_breaker"] is True

    def test_from_dict(self):
        """Test creation from dictionary."""
        data = {
            "max_portfolio_drawdown": 0.15,
            "max_position_size": 0.12,
            "min_cash_buffer": 0.25,
            "max_cash_buffer": 0.75,
            "position_stop_loss": 0.06,
            "enable_volatility_targeting": False,
            "target_portfolio_volatility": 0.18,
            "max_correlation": 0.75,
            "max_positions": 12,
            "enable_circuit_breaker": False,
            "circuit_breaker_threshold": 0.10,
            "max_correlated_positions": 3,
        }

        settings = RiskSettings.from_dict(data)

        assert settings.max_portfolio_drawdown == 0.15
        assert settings.max_position_size == 0.12
        assert settings.enable_volatility_targeting is False
        assert settings.enable_circuit_breaker is False

    def test_save_and_load(self):
        """Test saving and loading settings."""
        settings = RiskSettings(
            max_portfolio_drawdown=0.15,
            max_position_size=0.12,
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            filepath = Path(tmpdir) / "test_settings.json"

            # Save
            settings.save(filepath)
            assert filepath.exists()

            # Load
            loaded_settings = RiskSettings.load(filepath)
            assert loaded_settings.max_portfolio_drawdown == 0.15
            assert loaded_settings.max_position_size == 0.12

    def test_load_nonexistent_file(self):
        """Test loading from nonexistent file raises FileNotFoundError."""
        with pytest.raises(FileNotFoundError):
            RiskSettings.load("/tmp/nonexistent_file.json")

    def test_save_creates_parent_directory(self):
        """Test that save creates parent directory if it doesn't exist."""
        with tempfile.TemporaryDirectory() as tmpdir:
            filepath = Path(tmpdir) / "subdir" / "test_settings.json"

            settings = RiskSettings()
            settings.save(filepath)

            assert filepath.exists()
            assert filepath.parent.exists()

    def test_json_format(self):
        """Test that saved JSON is properly formatted."""
        settings = RiskSettings()

        with tempfile.TemporaryDirectory() as tmpdir:
            filepath = Path(tmpdir) / "test_settings.json"
            settings.save(filepath)

            # Read and verify JSON
            with open(filepath, "r") as f:
                data = json.load(f)

            assert isinstance(data, dict)
            assert "max_portfolio_drawdown" in data
            assert "enable_circuit_breaker" in data
