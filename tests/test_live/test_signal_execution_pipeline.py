"""
Tests for SignalExecutionPipeline
"""

from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, Mock, patch

import pytest

from copilot_quant.backtest.signals import TradingSignal
from copilot_quant.brokers.order_execution_handler import OrderRecord, OrderStatus
from copilot_quant.live.signal_execution_pipeline import (
    ExecutionResult,
    SignalExecutionPipeline,
    SignalStatus,
)
from copilot_quant.orchestrator.notifiers.base import AlertLevel, NotificationMessage
from src.risk.portfolio_risk import RiskCheckResult, RiskManager
from src.risk.settings import RiskSettings


class MockPortfolioState:
    """Mock portfolio state for testing"""

    def __init__(
        self,
        portfolio_value=100000,
        peak_value=100000,
        cash=50000,
        positions=None
    ):
        self._portfolio_value = portfolio_value
        self._peak_value = peak_value
        self._cash = cash
        self._positions = positions or {}

    def get_portfolio_value(self):
        return self._portfolio_value

    def get_peak_value(self):
        return self._peak_value

    def get_cash(self):
        return self._cash

    def get_positions(self):
        return self._positions


class MockPosition:
    """Mock position for testing"""

    def __init__(self, symbol, quantity=100, avg_entry_price=150.0):
        self.symbol = symbol
        self.quantity = quantity
        self.avg_entry_price = avg_entry_price


@pytest.fixture
def mock_portfolio_state():
    """Fixture for mock portfolio state"""
    return MockPortfolioState()


@pytest.fixture
def mock_risk_manager():
    """Fixture for mock risk manager"""
    settings = RiskSettings()
    return RiskManager(settings)


@pytest.fixture
def mock_order_handler():
    """Fixture for mock order handler"""
    from copilot_quant.brokers.order_execution_handler import OrderExecutionHandler
    return OrderExecutionHandler()


@pytest.fixture
def mock_notifier():
    """Fixture for mock notifier"""
    notifier = Mock()
    notifier.notify = Mock(return_value=True)
    return notifier


@pytest.fixture
def mock_ib_connection():
    """Fixture for mock IB connection"""
    return Mock()


@pytest.fixture
def pipeline(
    mock_risk_manager,
    mock_order_handler,
    mock_portfolio_state,
    mock_notifier,
    mock_ib_connection
):
    """Fixture for SignalExecutionPipeline"""
    return SignalExecutionPipeline(
        risk_manager=mock_risk_manager,
        order_handler=mock_order_handler,
        portfolio_state=mock_portfolio_state,
        notifier=mock_notifier,
        ib_connection=mock_ib_connection,
        max_position_pct=0.025,
        max_portfolio_deployment=0.80
    )


@pytest.fixture
def sample_signal():
    """Fixture for a sample trading signal"""
    return TradingSignal(
        symbol="AAPL",
        side="buy",
        confidence=0.8,
        sharpe_estimate=1.5,
        entry_price=150.0,
        stop_loss=145.0,
        take_profit=160.0,
        strategy_name="TestStrategy"
    )


class TestExecutionResult:
    """Test ExecutionResult dataclass"""

    def test_creation(self, sample_signal):
        """Test creating an ExecutionResult"""
        result = ExecutionResult(
            signal=sample_signal,
            status=SignalStatus.PENDING
        )

        assert result.signal == sample_signal
        assert result.status == SignalStatus.PENDING
        assert result.timestamp is not None
        assert result.risk_check_passed is False
        assert result.position_size == 0

    def test_to_dict(self, sample_signal):
        """Test converting ExecutionResult to dict"""
        result = ExecutionResult(
            signal=sample_signal,
            status=SignalStatus.EXECUTED,
            risk_check_passed=True,
            position_size=100,
            position_value=15000.0
        )

        data = result.to_dict()

        assert data['signal']['symbol'] == 'AAPL'
        assert data['status'] == 'executed'
        assert data['risk_check_passed'] is True
        assert data['position_size'] == 100
        assert data['position_value'] == 15000.0

    def test_to_json(self, sample_signal):
        """Test converting ExecutionResult to JSON"""
        result = ExecutionResult(
            signal=sample_signal,
            status=SignalStatus.REJECTED,
            rejection_reason="Test rejection"
        )

        json_str = result.to_json()

        assert isinstance(json_str, str)
        assert 'AAPL' in json_str
        assert 'rejected' in json_str
        assert 'Test rejection' in json_str


class TestSignalExecutionPipeline:
    """Test SignalExecutionPipeline class"""

    def test_initialization(self, pipeline):
        """Test pipeline initialization"""
        assert pipeline.max_position_pct == 0.025
        assert pipeline.max_portfolio_deployment == 0.80
        assert pipeline.stats['total_processed'] == 0
        assert pipeline.stats['approved'] == 0
        assert pipeline.stats['rejected'] == 0

    @pytest.mark.asyncio
    async def test_process_signal_success(self, pipeline, sample_signal):
        """Test successful signal processing"""
        # Mock order submission
        mock_order = OrderRecord(
            order_id=12345,
            symbol="AAPL",
            action="BUY",
            total_quantity=100,
            order_type="MARKET",
            status=OrderStatus.SUBMITTED
        )

        with patch.object(pipeline.order_handler, 'submit_order', return_value=mock_order):
            result = await pipeline.process_signal(sample_signal)

        assert result.status == SignalStatus.EXECUTED
        assert result.risk_check_passed is True
        assert result.position_size > 0
        assert result.order_id == 12345
        assert pipeline.stats['executed'] == 1

    @pytest.mark.asyncio
    async def test_process_signal_low_quality_rejected(self, pipeline):
        """Test signal rejection due to low quality score"""
        low_quality_signal = TradingSignal(
            symbol="AAPL",
            side="buy",
            confidence=0.2,  # Low confidence
            sharpe_estimate=0.5,  # Low Sharpe
            entry_price=150.0,
            strategy_name="TestStrategy"
        )

        result = await pipeline.process_signal(low_quality_signal)

        assert result.status == SignalStatus.REJECTED
        assert result.risk_check_passed is False
        assert "quality score" in result.rejection_reason.lower()
        assert pipeline.stats['rejected'] == 1

    @pytest.mark.asyncio
    async def test_process_signal_circuit_breaker_active(
        self,
        mock_risk_manager,
        mock_order_handler,
        mock_portfolio_state,
        mock_notifier,
        mock_ib_connection,
        sample_signal
    ):
        """Test signal rejection when circuit breaker is active"""
        # Trigger circuit breaker
        mock_risk_manager.trigger_circuit_breaker(
            portfolio_value=88000,
            peak_value=100000,
            current_drawdown=0.12
        )

        pipeline = SignalExecutionPipeline(
            risk_manager=mock_risk_manager,
            order_handler=mock_order_handler,
            portfolio_state=mock_portfolio_state,
            notifier=mock_notifier,
            ib_connection=mock_ib_connection
        )

        result = await pipeline.process_signal(sample_signal)

        assert result.status == SignalStatus.REJECTED
        assert "circuit breaker" in result.rejection_reason.lower()
        assert pipeline.stats['rejected'] == 1

    @pytest.mark.asyncio
    async def test_process_signal_deployment_limit(self, pipeline, sample_signal):
        """Test signal rejection when deployment limit reached"""
        # Set portfolio state to high deployment but above min cash buffer
        pipeline.portfolio_state._cash = 20000  # 20% cash (min) = 80% deployed
        pipeline.portfolio_state._portfolio_value = 100000

        # Now set cash to just above threshold but below deployment would breach it
        pipeline.max_portfolio_deployment = 0.79  # Set limit to 79%

        result = await pipeline.process_signal(sample_signal)

        assert result.status == SignalStatus.REJECTED
        assert "deployment" in result.rejection_reason.lower()

    @pytest.mark.asyncio
    async def test_process_signal_order_submission_failed(self, pipeline, sample_signal):
        """Test signal when order submission fails"""
        # Mock order submission to return None (failure)
        with patch.object(pipeline.order_handler, 'submit_order', return_value=None):
            result = await pipeline.process_signal(sample_signal)

        assert result.status == SignalStatus.FAILED
        assert "submission failed" in result.rejection_reason.lower()
        assert pipeline.stats['failed'] == 1

    @pytest.mark.asyncio
    async def test_process_signal_sends_notifications(
        self,
        pipeline,
        sample_signal,
        mock_notifier
    ):
        """Test that notifications are sent on execution"""
        mock_order = OrderRecord(
            order_id=12345,
            symbol="AAPL",
            action="BUY",
            total_quantity=100,
            order_type="MARKET",
            status=OrderStatus.SUBMITTED
        )

        with patch.object(pipeline.order_handler, 'submit_order', return_value=mock_order):
            result = await pipeline.process_signal(sample_signal)

        assert result.status == SignalStatus.EXECUTED

        # Check that notification was sent
        mock_notifier.notify.assert_called()
        call_args = mock_notifier.notify.call_args[0][0]
        assert isinstance(call_args, NotificationMessage)
        assert call_args.level == AlertLevel.INFO
        assert "AAPL" in call_args.message

    @pytest.mark.asyncio
    async def test_process_signal_rejection_notification(self, pipeline, mock_notifier):
        """Test that rejection notifications are sent"""
        low_quality_signal = TradingSignal(
            symbol="AAPL",
            side="buy",
            confidence=0.2,
            sharpe_estimate=0.5,
            entry_price=150.0,
            strategy_name="TestStrategy"
        )

        result = await pipeline.process_signal(low_quality_signal)

        assert result.status == SignalStatus.REJECTED

        # Check that rejection notification was sent
        mock_notifier.notify.assert_called()
        call_args = mock_notifier.notify.call_args[0][0]
        assert isinstance(call_args, NotificationMessage)
        assert call_args.level == AlertLevel.WARNING

    @pytest.mark.asyncio
    async def test_process_batch_empty(self, pipeline):
        """Test processing empty batch"""
        results = await pipeline.process_batch([])

        assert len(results) == 0

    @pytest.mark.asyncio
    async def test_process_batch_ranking(self, pipeline):
        """Test that batch processing ranks signals by quality score"""
        signals = [
            TradingSignal(
                symbol=f"SYM{i}",
                side="buy",
                confidence=0.5 + i * 0.1,
                sharpe_estimate=1.0 + i * 0.2,
                entry_price=100.0,
                strategy_name="TestStrategy"
            )
            for i in range(3)
        ]

        # Mock order submission to succeed
        mock_order = OrderRecord(
            order_id=12345,
            symbol="TEST",
            action="BUY",
            total_quantity=100,
            order_type="MARKET",
            status=OrderStatus.SUBMITTED
        )

        with patch.object(pipeline.order_handler, 'submit_order', return_value=mock_order):
            results = await pipeline.process_batch(signals)

        assert len(results) == 3

        # Verify signals were processed in descending quality order
        # SYM2 should have highest quality score
        assert results[0].signal.symbol == "SYM2"
        assert results[1].signal.symbol == "SYM1"
        assert results[2].signal.symbol == "SYM0"

    @pytest.mark.asyncio
    async def test_process_batch_stops_at_deployment_limit(self, pipeline):
        """Test that batch processing stops when deployment limit reached"""
        # Create multiple signals
        signals = [
            TradingSignal(
                symbol=f"SYM{i}",
                side="buy",
                confidence=0.8,
                sharpe_estimate=1.5,
                entry_price=100.0,
                strategy_name="TestStrategy"
            )
            for i in range(5)
        ]

        # Set high deployment (only 15% cash = 85% deployed)
        pipeline.portfolio_state._cash = 15000

        results = await pipeline.process_batch(signals)

        # All should be rejected due to deployment limit
        assert all(r.status == SignalStatus.REJECTED for r in results)
        assert all("deployment" in r.rejection_reason.lower() for r in results)

    def test_calculate_position_size(self, pipeline, sample_signal):
        """Test position size calculation"""
        shares, value = pipeline._calculate_position_size(sample_signal)

        # Portfolio value = 100k, max_position_pct = 2.5%, quality_score = 0.6
        # Formula: (portfolio_value * max_position_pct * quality_score) / entry_price
        # Expected: (100k * 0.025 * 0.6) / 150 = 1500 / 150 = 10 shares
        assert shares == 10
        assert value == pytest.approx(1500.0, rel=0.01)

    def test_calculate_position_size_high_quality(self, pipeline):
        """Test position size with high quality signal"""
        high_quality_signal = TradingSignal(
            symbol="AAPL",
            side="buy",
            confidence=1.0,
            sharpe_estimate=2.0,  # Max Sharpe for quality score
            entry_price=100.0,
            strategy_name="TestStrategy"
        )

        shares, value = pipeline._calculate_position_size(high_quality_signal)

        # Quality score = 1.0 * 1.0 = 1.0
        # Position = 100k * 0.025 * 1.0 = 2500 / 100 = 25 shares
        assert shares == 25
        assert value == pytest.approx(2500.0, rel=0.01)

    def test_calculate_current_deployment(self, pipeline):
        """Test current deployment calculation"""
        deployment = pipeline._calculate_current_deployment()

        # Portfolio = 100k, Cash = 50k, Deployed = 50k
        # Deployment = 50k / 100k = 0.5
        assert deployment == pytest.approx(0.5, rel=0.01)

    def test_is_deployment_limit_reached(self, pipeline):
        """Test deployment limit check"""
        # Initial state: 50% deployed, limit is 80%
        assert pipeline._is_deployment_limit_reached() is False

        # Set to high deployment
        pipeline.portfolio_state._cash = 15000  # 85% deployed
        assert pipeline._is_deployment_limit_reached() is True

    def test_fill_callback(self, pipeline):
        """Test fill callback handling"""
        order_record = OrderRecord(
            order_id=12345,
            symbol="AAPL",
            action="BUY",
            total_quantity=100,
            order_type="MARKET",
            status=OrderStatus.FILLED,
            filled_quantity=100,
            avg_fill_price=150.0
        )

        # This should not raise an error
        pipeline._on_fill(order_record)

        # Verify notification was sent
        pipeline.notifier.notify.assert_called()
        call_args = pipeline.notifier.notify.call_args[0][0]
        assert "Filled" in call_args.title
        assert "AAPL" in call_args.message

    def test_get_stats(self, pipeline):
        """Test getting pipeline statistics"""
        stats = pipeline.get_stats()

        assert isinstance(stats, dict)
        assert 'total_processed' in stats
        assert 'approved' in stats
        assert 'rejected' in stats
        assert 'executed' in stats
        assert 'failed' in stats


class TestRiskCheckScenarios:
    """Test various risk check scenarios"""

    @pytest.mark.asyncio
    async def test_max_position_size_limit(
        self,
        mock_risk_manager,
        mock_order_handler,
        mock_notifier,
        mock_ib_connection
    ):
        """Test that position size respects max_position_pct"""
        portfolio_state = MockPortfolioState(
            portfolio_value=100000,
            cash=50000
        )

        pipeline = SignalExecutionPipeline(
            risk_manager=mock_risk_manager,
            order_handler=mock_order_handler,
            portfolio_state=portfolio_state,
            notifier=mock_notifier,
            ib_connection=mock_ib_connection,
            max_position_pct=0.025  # 2.5%
        )

        signal = TradingSignal(
            symbol="AAPL",
            side="buy",
            confidence=1.0,
            sharpe_estimate=2.0,
            entry_price=100.0,
            strategy_name="TestStrategy"
        )

        shares, value = pipeline._calculate_position_size(signal)

        # Max position = 100k * 0.025 = 2500
        assert value <= 2500.0

    @pytest.mark.asyncio
    async def test_drawdown_cap_rejection(
        self,
        mock_order_handler,
        mock_notifier,
        mock_ib_connection
    ):
        """Test signal rejection when drawdown cap exceeded"""
        # Create portfolio with high drawdown
        portfolio_state = MockPortfolioState(
            portfolio_value=85000,  # 15% drawdown
            peak_value=100000,
            cash=40000
        )

        settings = RiskSettings(max_portfolio_drawdown=0.12)  # 12% max
        risk_manager = RiskManager(settings)

        pipeline = SignalExecutionPipeline(
            risk_manager=risk_manager,
            order_handler=mock_order_handler,
            portfolio_state=portfolio_state,
            notifier=mock_notifier,
            ib_connection=mock_ib_connection
        )

        signal = TradingSignal(
            symbol="AAPL",
            side="buy",
            confidence=0.8,
            sharpe_estimate=1.5,
            entry_price=150.0,
            strategy_name="TestStrategy"
        )

        result = await pipeline.process_signal(signal)

        assert result.status == SignalStatus.REJECTED
        assert "drawdown" in result.rejection_reason.lower()

    @pytest.mark.asyncio
    async def test_circuit_breaker_notification(
        self,
        mock_order_handler,
        mock_notifier,
        mock_ib_connection
    ):
        """Test that circuit breaker triggers CRITICAL notification"""
        portfolio_state = MockPortfolioState(
            portfolio_value=88000,
            peak_value=100000,
            cash=40000
        )

        settings = RiskSettings(
            circuit_breaker_threshold=0.10,  # 10% triggers breaker
            max_portfolio_drawdown=0.12
        )
        risk_manager = RiskManager(settings)

        # Trigger circuit breaker (12% drawdown)
        risk_manager.trigger_circuit_breaker(
            portfolio_value=88000,
            peak_value=100000,
            current_drawdown=0.12
        )

        pipeline = SignalExecutionPipeline(
            risk_manager=risk_manager,
            order_handler=mock_order_handler,
            portfolio_state=portfolio_state,
            notifier=mock_notifier,
            ib_connection=mock_ib_connection
        )

        signal = TradingSignal(
            symbol="AAPL",
            side="buy",
            confidence=0.8,
            sharpe_estimate=1.5,
            entry_price=150.0,
            strategy_name="TestStrategy"
        )

        result = await pipeline.process_signal(signal)

        assert result.status == SignalStatus.REJECTED

        # Verify CRITICAL notification was sent
        mock_notifier.notify.assert_called()
        call_args = mock_notifier.notify.call_args[0][0]
        assert call_args.level == AlertLevel.CRITICAL
