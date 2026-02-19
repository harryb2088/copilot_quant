"""Tests for RiskManager class."""

import pandas as pd
import pytest

from src.risk.portfolio_risk import RiskCheckResult, RiskManager
from src.risk.settings import RiskSettings


class TestRiskCheckResult:
    """Test RiskCheckResult dataclass."""

    def test_creation(self):
        """Test creating a RiskCheckResult."""
        result = RiskCheckResult(approved=True, reason="All checks passed", details={"value": 100})

        assert result.approved is True
        assert result.reason == "All checks passed"
        assert result.details == {"value": 100}
        assert result.timestamp is not None

    def test_timestamp_auto_set(self):
        """Test that timestamp is automatically set if not provided."""
        result = RiskCheckResult(approved=True, reason="Test")
        assert result.timestamp is not None


class TestRiskManager:
    """Test RiskManager class."""

    def test_initialization_default(self):
        """Test RiskManager initialization with default settings."""
        manager = RiskManager()

        assert manager.settings is not None
        assert manager.settings.max_portfolio_drawdown == 0.12
        assert not manager.is_circuit_breaker_active()

    def test_initialization_custom_settings(self):
        """Test RiskManager initialization with custom settings."""
        settings = RiskSettings(max_portfolio_drawdown=0.15)
        manager = RiskManager(settings)

        assert manager.settings.max_portfolio_drawdown == 0.15

    def test_check_portfolio_risk_zero_portfolio(self):
        """Test portfolio check with zero portfolio value."""
        manager = RiskManager()
        result = manager.check_portfolio_risk(portfolio_value=0, peak_value=100000, cash=0)

        assert not result.approved
        assert "must be positive" in result.reason

    def test_check_portfolio_risk_negative_portfolio(self):
        """Test portfolio check with negative portfolio value."""
        manager = RiskManager()
        result = manager.check_portfolio_risk(portfolio_value=-1000, peak_value=100000, cash=0)

        assert not result.approved
        assert "must be positive" in result.reason

    def test_check_portfolio_risk_acceptable(self):
        """Test portfolio check with acceptable values."""
        manager = RiskManager()
        result = manager.check_portfolio_risk(
            portfolio_value=95000,
            peak_value=100000,
            cash=25000,  # 26.3% cash
        )

        assert result.approved
        assert result.details["current_drawdown"] == pytest.approx(0.05)
        assert result.details["cash_pct"] == pytest.approx(0.263, rel=0.01)

    def test_check_portfolio_risk_exceeds_max_drawdown(self):
        """Test portfolio check when drawdown exceeds maximum."""
        manager = RiskManager()
        result = manager.check_portfolio_risk(
            portfolio_value=85000,  # 15% drawdown
            peak_value=100000,
            cash=20000,
        )

        assert not result.approved
        assert "drawdown" in result.reason.lower()
        assert result.details["current_drawdown"] == 0.15

    def test_check_portfolio_risk_below_min_cash(self):
        """Test portfolio check when cash is below minimum."""
        manager = RiskManager()
        result = manager.check_portfolio_risk(
            portfolio_value=100000,
            peak_value=100000,
            cash=15000,  # 15% < 20% min
        )

        assert not result.approved
        assert "cash buffer" in result.reason.lower()
        assert "below minimum" in result.reason.lower()

    def test_check_portfolio_risk_above_max_cash(self):
        """Test portfolio check when cash exceeds maximum."""
        manager = RiskManager()
        result = manager.check_portfolio_risk(
            portfolio_value=100000,
            peak_value=100000,
            cash=85000,  # 85% > 80% max
        )

        assert not result.approved
        assert "cash buffer" in result.reason.lower()
        assert "exceeds maximum" in result.reason.lower()

    def test_check_portfolio_risk_max_positions_reached(self):
        """Test portfolio check when max positions is reached."""
        manager = RiskManager()
        positions = [{"symbol": f"SYM{i}"} for i in range(10)]  # 10 positions (max)

        result = manager.check_portfolio_risk(
            portfolio_value=100000, peak_value=100000, cash=25000, positions=positions
        )

        assert not result.approved
        assert "maximum number of positions" in result.reason.lower()

    def test_check_position_risk_acceptable(self):
        """Test position check with acceptable values."""
        manager = RiskManager()
        result = manager.check_position_risk(
            position_value=8000,  # 8% of portfolio
            portfolio_value=100000,
            entry_price=100,
            current_price=102,
        )

        assert result.approved
        assert result.details["position_pct"] == pytest.approx(0.08)

    def test_check_position_risk_exceeds_max_size(self):
        """Test position check when size exceeds maximum."""
        manager = RiskManager()
        result = manager.check_position_risk(
            position_value=12000,  # 12% > 10% max
            portfolio_value=100000,
            entry_price=100,
            current_price=102,
        )

        assert not result.approved
        assert "position size" in result.reason.lower()
        assert "exceeds maximum" in result.reason.lower()

    def test_check_position_risk_stop_loss_triggered(self):
        """Test position check when stop loss is triggered."""
        manager = RiskManager()
        result = manager.check_position_risk(
            position_value=8000,
            portfolio_value=100000,
            entry_price=100,
            current_price=92,  # 8% loss > 5% stop
        )

        assert not result.approved
        assert "stop loss" in result.reason.lower()
        assert result.details["position_return"] == pytest.approx(-0.08)

    def test_calculate_position_size_basic(self):
        """Test basic position size calculation."""
        manager = RiskManager()
        size = manager.calculate_position_size(signal_strength=1.0, portfolio_value=100000, volatility=None)

        # Should be max position size with full signal strength
        assert size == pytest.approx(10000)  # 10% of 100k

    def test_calculate_position_size_half_signal(self):
        """Test position size with half signal strength."""
        manager = RiskManager()
        size = manager.calculate_position_size(signal_strength=0.5, portfolio_value=100000, volatility=None)

        assert size == pytest.approx(5000)  # 5% of 100k

    def test_calculate_position_size_zero_signal(self):
        """Test position size with zero signal strength."""
        manager = RiskManager()
        size = manager.calculate_position_size(signal_strength=0.0, portfolio_value=100000, volatility=None)

        assert size == 0.0

    def test_calculate_position_size_invalid_signal(self):
        """Test that invalid signal strength raises error."""
        manager = RiskManager()

        with pytest.raises(ValueError, match="signal_strength must be between 0 and 1"):
            manager.calculate_position_size(signal_strength=1.5, portfolio_value=100000)

        with pytest.raises(ValueError, match="signal_strength must be between 0 and 1"):
            manager.calculate_position_size(signal_strength=-0.5, portfolio_value=100000)

    def test_calculate_position_size_zero_portfolio(self):
        """Test position size with zero portfolio."""
        manager = RiskManager()
        size = manager.calculate_position_size(signal_strength=1.0, portfolio_value=0)

        assert size == 0.0

    def test_calculate_position_size_with_volatility_targeting(self):
        """Test position size with volatility targeting enabled."""
        manager = RiskManager()

        # High volatility should reduce position size
        size_high_vol = manager.calculate_position_size(
            signal_strength=1.0,
            portfolio_value=100000,
            volatility=0.30,  # 30% volatility (high)
        )

        # Low volatility should increase position size (up to cap)
        size_low_vol = manager.calculate_position_size(
            signal_strength=1.0,
            portfolio_value=100000,
            volatility=0.10,  # 10% volatility (low)
        )

        assert size_high_vol < 10000  # Less than max
        assert size_low_vol >= size_high_vol  # Low vol >= high vol

    def test_calculate_position_size_volatility_disabled(self):
        """Test position size with volatility targeting disabled."""
        settings = RiskSettings(enable_volatility_targeting=False)
        manager = RiskManager(settings)

        size = manager.calculate_position_size(
            signal_strength=1.0,
            portfolio_value=100000,
            volatility=0.50,  # Even with high volatility, should ignore it
        )

        assert size == pytest.approx(10000)  # Should be max regardless of volatility

    def test_check_correlation_no_positions(self):
        """Test correlation check with no existing positions."""
        manager = RiskManager()
        price_data = pd.DataFrame(
            {
                "AAPL": [100, 101, 102],
                "MSFT": [200, 201, 202],
            }
        )

        result = manager.check_correlation(new_symbol="AAPL", existing_positions=[], price_data=price_data)

        assert result.approved
        assert "no existing positions" in result.reason.lower()

    def test_check_correlation_acceptable(self):
        """Test correlation check with acceptable correlation."""
        manager = RiskManager()

        # Create uncorrelated price data with fixed seed for deterministic results
        import numpy as np

        np.random.seed(42)

        price_data = pd.DataFrame(
            {
                "AAPL": np.random.randn(100).cumsum() + 100,
                "TSLA": np.random.randn(100).cumsum() + 200,
            }
        )

        result = manager.check_correlation(
            new_symbol="TSLA", existing_positions=[{"symbol": "AAPL"}], price_data=price_data
        )

        # With fixed seed and uncorrelated data, should be approved
        assert result.approved
        assert "correlation within acceptable limits" in result.reason.lower()

    def test_check_correlation_high_correlation(self):
        """Test correlation check with high correlation."""
        manager = RiskManager()

        # Create highly correlated price data
        import numpy as np

        base = np.array([100, 101, 102, 103, 104, 105])

        price_data = pd.DataFrame(
            {
                "AAPL": base,
                "MSFT": base * 2,  # Perfectly correlated
                "GOOGL": base * 1.5,  # Perfectly correlated
            }
        )

        existing_positions = [
            {"symbol": "AAPL"},
            {"symbol": "GOOGL"},
        ]

        result = manager.check_correlation(
            new_symbol="MSFT", existing_positions=existing_positions, price_data=price_data
        )

        assert not result.approved
        assert "correlated" in result.reason.lower()

    def test_circuit_breaker_trigger(self):
        """Test circuit breaker activation."""
        manager = RiskManager()

        result = manager.trigger_circuit_breaker(portfolio_value=90000, peak_value=100000, current_drawdown=0.10)

        assert not result.approved
        assert "circuit breaker" in result.reason.lower()
        assert manager.is_circuit_breaker_active()

    def test_circuit_breaker_prevents_trades(self):
        """Test that circuit breaker prevents new trades."""
        manager = RiskManager()

        # Trigger circuit breaker
        manager.trigger_circuit_breaker(portfolio_value=90000, peak_value=100000, current_drawdown=0.10)

        # Try to check portfolio risk
        result = manager.check_portfolio_risk(portfolio_value=95000, peak_value=100000, cash=25000)

        assert not result.approved
        assert "circuit breaker is active" in result.reason.lower()

    def test_circuit_breaker_reset(self):
        """Test resetting the circuit breaker."""
        manager = RiskManager()

        # Trigger
        manager.trigger_circuit_breaker(portfolio_value=90000, peak_value=100000, current_drawdown=0.10)
        assert manager.is_circuit_breaker_active()

        # Reset
        manager.reset_circuit_breaker()
        assert not manager.is_circuit_breaker_active()

    def test_circuit_breaker_automatic_trigger(self):
        """Test automatic circuit breaker trigger from portfolio check."""
        manager = RiskManager()

        result = manager.check_portfolio_risk(
            portfolio_value=90000,  # 10% drawdown = threshold
            peak_value=100000,
            cash=25000,
        )

        assert not result.approved
        assert "circuit breaker" in result.reason.lower()
        assert manager.is_circuit_breaker_active()

    def test_breach_log(self):
        """Test breach logging."""
        manager = RiskManager()

        # Trigger some breaches
        manager.check_portfolio_risk(
            portfolio_value=85000,  # Exceeds max drawdown
            peak_value=100000,
            cash=20000,
        )

        manager.check_position_risk(
            position_value=8000,
            portfolio_value=100000,
            entry_price=100,
            current_price=92,  # Triggers stop loss
        )

        # Check breach log
        log = manager.get_breach_log()
        assert len(log) >= 2

        # Verify log entries have required fields
        for entry in log:
            assert "breach_type" in entry or "event" in entry
            assert "timestamp" in entry

    def test_clear_breach_log(self):
        """Test clearing the breach log."""
        manager = RiskManager()

        # Create a breach
        manager.check_portfolio_risk(portfolio_value=85000, peak_value=100000, cash=20000)

        assert len(manager.get_breach_log()) > 0

        # Clear log
        manager.clear_breach_log()
        assert len(manager.get_breach_log()) == 0

    def test_edge_case_100_percent_drawdown(self):
        """Test edge case with 100% drawdown."""
        manager = RiskManager()

        result = manager.check_portfolio_risk(
            portfolio_value=1,  # Almost complete loss
            peak_value=100000,
            cash=0,
        )

        assert not result.approved

    def test_edge_case_no_peak_value(self):
        """Test edge case with zero peak value."""
        manager = RiskManager()

        result = manager.check_portfolio_risk(portfolio_value=100000, peak_value=0, cash=25000)

        # With zero peak, drawdown should be 0, and cash checks should pass
        assert result.approved
        assert result.details["current_drawdown"] == 0.0
        assert result.details["cash_pct"] == 0.25
