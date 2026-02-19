"""Tests for signal persistence layer."""

import uuid
from datetime import datetime, timedelta

import pytest

from copilot_quant.backtest.signals import TradingSignal
from copilot_quant.data.models import SignalRecord, SignalStatus
from copilot_quant.data.signal_repository import SignalRepository


class TestSignalRecord:
    """Tests for SignalRecord model."""

    def test_signal_record_creation(self):
        """Test creating a SignalRecord instance."""
        record = SignalRecord(
            signal_id=str(uuid.uuid4()),
            strategy_name="TestStrategy",
            symbol="AAPL",
            direction="BUY",
            strength=0.8,
            quality_score=0.6,
            signal_price=150.0,
            status="generated",
            generated_at=datetime.utcnow(),
        )

        assert record.signal_id is not None
        assert record.strategy_name == "TestStrategy"
        assert record.symbol == "AAPL"
        assert record.direction == "BUY"
        assert record.strength == 0.8
        assert record.quality_score == 0.6
        assert record.signal_price == 150.0
        assert record.status == "generated"

    def test_signal_record_repr(self):
        """Test SignalRecord string representation."""
        record = SignalRecord(
            id=1,
            signal_id="test-123",
            strategy_name="TestStrategy",
            symbol="AAPL",
            status="generated",
            generated_at=datetime.utcnow(),
        )

        repr_str = repr(record)
        assert "SignalRecord" in repr_str
        assert "test-123" in repr_str
        assert "AAPL" in repr_str
        assert "generated" in repr_str


class TestSignalStatus:
    """Tests for SignalStatus enum."""

    def test_signal_status_values(self):
        """Test all SignalStatus enum values."""
        assert SignalStatus.GENERATED.value == "generated"
        assert SignalStatus.PASSED_RISK.value == "passed_risk"
        assert SignalStatus.REJECTED.value == "rejected"
        assert SignalStatus.SUBMITTED.value == "submitted"
        assert SignalStatus.EXECUTED.value == "executed"
        assert SignalStatus.PARTIALLY_FILLED.value == "partially_filled"
        assert SignalStatus.CANCELLED.value == "cancelled"
        assert SignalStatus.EXPIRED.value == "expired"
        assert SignalStatus.MISSED.value == "missed"
        assert SignalStatus.ERROR.value == "error"

    def test_signal_status_enum_access(self):
        """Test accessing SignalStatus by name."""
        status = SignalStatus["GENERATED"]
        assert status == SignalStatus.GENERATED
        assert status.value == "generated"


class TestSignalRepository:
    """Tests for SignalRepository class."""

    @pytest.fixture
    def repo(self):
        """Create an in-memory repository for testing."""
        return SignalRepository(db_url="sqlite:///:memory:")

    @pytest.fixture
    def sample_signal(self):
        """Create a sample TradingSignal for testing."""
        return TradingSignal(
            symbol="AAPL",
            side="buy",
            confidence=0.8,
            sharpe_estimate=1.5,
            entry_price=150.0,
            stop_loss=145.0,
            take_profit=155.0,
            strategy_name="TestStrategy",
        )

    def test_repository_initialization(self, repo):
        """Test repository initialization creates tables."""
        assert repo.engine is not None
        assert repo.SessionLocal is not None

    def test_save_signal(self, repo, sample_signal):
        """Test saving a signal to the database."""
        record = repo.save_signal(sample_signal)

        assert record.signal_id is not None
        assert record.strategy_name == "TestStrategy"
        assert record.symbol == "AAPL"
        assert record.direction == "BUY"
        assert record.strength == 0.8
        assert record.quality_score == sample_signal.quality_score
        assert record.signal_price == 150.0
        assert record.status == "generated"
        assert record.generated_at is not None

    def test_save_signal_with_custom_status(self, repo, sample_signal):
        """Test saving a signal with custom status."""
        record = repo.save_signal(sample_signal, status="passed_risk")

        assert record.status == "passed_risk"

    def test_save_signal_with_custom_id(self, repo, sample_signal):
        """Test saving a signal with custom ID."""
        custom_id = str(uuid.uuid4())
        record = repo.save_signal(sample_signal, signal_id=custom_id)

        assert record.signal_id == custom_id

    def test_save_signal_stores_metadata(self, repo, sample_signal):
        """Test that stop loss and take profit are stored in metadata."""
        record = repo.save_signal(sample_signal)

        assert record.signal_metadata is not None
        assert record.signal_metadata["stop_loss"] == 145.0
        assert record.signal_metadata["take_profit"] == 155.0

    def test_save_signal_with_additional_fields(self, repo, sample_signal):
        """Test saving signal with additional fields."""
        record = repo.save_signal(
            sample_signal,
            signal_type="entry",
            requested_quantity=100,
            position_value=15000.0,
        )

        assert record.signal_type == "entry"
        assert record.requested_quantity == 100
        assert record.position_value == 15000.0

    def test_get_signal_by_id(self, repo, sample_signal):
        """Test retrieving a signal by ID."""
        saved = repo.save_signal(sample_signal)
        retrieved = repo.get_signal_by_id(saved.signal_id)

        assert retrieved is not None
        assert retrieved.signal_id == saved.signal_id
        assert retrieved.symbol == "AAPL"

    def test_get_signal_by_id_not_found(self, repo):
        """Test retrieving non-existent signal returns None."""
        result = repo.get_signal_by_id("non-existent-id")
        assert result is None

    def test_update_signal_status(self, repo, sample_signal):
        """Test updating signal status."""
        saved = repo.save_signal(sample_signal)
        success = repo.update_signal_status(saved.signal_id, "passed_risk")

        assert success is True

        retrieved = repo.get_signal_by_id(saved.signal_id)
        assert retrieved.status == "passed_risk"

    def test_update_signal_status_not_found(self, repo):
        """Test updating non-existent signal returns False."""
        success = repo.update_signal_status("non-existent-id", "executed")
        assert success is False

    def test_update_signal_with_additional_fields(self, repo, sample_signal):
        """Test updating signal with additional fields."""
        saved = repo.save_signal(sample_signal)
        repo.update_signal_status(
            saved.signal_id,
            "executed",
            executed_price=151.0,
            executed_quantity=100,
            executed_at=datetime.utcnow(),
        )

        retrieved = repo.get_signal_by_id(saved.signal_id)
        assert retrieved.status == "executed"
        assert retrieved.executed_price == 151.0
        assert retrieved.executed_quantity == 100
        assert retrieved.executed_at is not None

    def test_update_calculates_slippage(self, repo, sample_signal):
        """Test that slippage is calculated when executed_price is set."""
        saved = repo.save_signal(sample_signal)
        repo.update_signal_status(
            saved.signal_id,
            "executed",
            executed_price=151.0,
        )

        retrieved = repo.get_signal_by_id(saved.signal_id)
        assert retrieved.slippage == 1.0  # 151.0 - 150.0

    def test_signal_status_transition(self, repo, sample_signal):
        """Test complete signal lifecycle status transitions."""
        # Save signal
        saved = repo.save_signal(sample_signal)
        assert saved.status == "generated"

        # Pass risk check
        repo.update_signal_status(
            saved.signal_id,
            "passed_risk",
            risk_check_passed=True,
            risk_check_details={"max_position_size": True, "portfolio_risk": True},
        )
        retrieved = repo.get_signal_by_id(saved.signal_id)
        assert retrieved.status == "passed_risk"
        assert retrieved.risk_check_passed is True

        # Submit order
        repo.update_signal_status(
            saved.signal_id,
            "submitted",
            order_id="ORDER-123",
            processed_at=datetime.utcnow(),
        )
        retrieved = repo.get_signal_by_id(saved.signal_id)
        assert retrieved.status == "submitted"
        assert retrieved.order_id == "ORDER-123"

        # Execute order
        repo.update_signal_status(
            saved.signal_id,
            "executed",
            executed_price=151.5,
            executed_quantity=100,
            executed_at=datetime.utcnow(),
        )
        retrieved = repo.get_signal_by_id(saved.signal_id)
        assert retrieved.status == "executed"
        assert retrieved.executed_price == 151.5
        assert retrieved.executed_quantity == 100

    def test_get_signals_no_filters(self, repo, sample_signal):
        """Test getting all signals without filters."""
        # Save multiple signals
        repo.save_signal(sample_signal)
        repo.save_signal(
            TradingSignal(
                symbol="MSFT",
                side="sell",
                confidence=0.6,
                sharpe_estimate=1.2,
                entry_price=300.0,
                strategy_name="TestStrategy",
            )
        )

        signals = repo.get_signals()
        assert len(signals) == 2

    def test_get_signals_filter_by_symbol(self, repo, sample_signal):
        """Test filtering signals by symbol."""
        repo.save_signal(sample_signal)
        repo.save_signal(
            TradingSignal(
                symbol="MSFT",
                side="sell",
                confidence=0.6,
                sharpe_estimate=1.2,
                entry_price=300.0,
                strategy_name="TestStrategy",
            )
        )

        signals = repo.get_signals(filters={"symbol": "AAPL"})
        assert len(signals) == 1
        assert signals[0].symbol == "AAPL"

    def test_get_signals_filter_by_strategy(self, repo, sample_signal):
        """Test filtering signals by strategy."""
        repo.save_signal(sample_signal)
        repo.save_signal(
            TradingSignal(
                symbol="MSFT",
                side="sell",
                confidence=0.6,
                sharpe_estimate=1.2,
                entry_price=300.0,
                strategy_name="OtherStrategy",
            )
        )

        signals = repo.get_signals(filters={"strategy": "TestStrategy"})
        assert len(signals) == 1
        assert signals[0].strategy_name == "TestStrategy"

    def test_get_signals_filter_by_status(self, repo, sample_signal):
        """Test filtering signals by status."""
        saved1 = repo.save_signal(sample_signal)
        saved2 = repo.save_signal(
            TradingSignal(
                symbol="MSFT",
                side="sell",
                confidence=0.6,
                sharpe_estimate=1.2,
                entry_price=300.0,
                strategy_name="TestStrategy",
            )
        )

        # Update one signal to executed
        repo.update_signal_status(saved2.signal_id, "executed")

        signals = repo.get_signals(filters={"status": "executed"})
        assert len(signals) == 1
        assert signals[0].status == "executed"

    def test_get_signals_filter_by_date_range(self, repo, sample_signal):
        """Test filtering signals by date range."""
        now = datetime.utcnow()
        yesterday = now - timedelta(days=1)
        tomorrow = now + timedelta(days=1)

        # Save signal with specific timestamp
        repo.save_signal(sample_signal, generated_at=now)

        signals = repo.get_signals(filters={"start_date": yesterday, "end_date": tomorrow})
        assert len(signals) == 1

        # Filter outside range
        signals = repo.get_signals(
            filters={"start_date": tomorrow, "end_date": tomorrow + timedelta(days=1)}
        )
        assert len(signals) == 0

    def test_get_signals_limit(self, repo, sample_signal):
        """Test limiting number of returned signals."""
        # Save multiple signals
        for i in range(5):
            repo.save_signal(sample_signal)

        signals = repo.get_signals(limit=3)
        assert len(signals) == 3

    def test_get_signals_ordered_by_date(self, repo, sample_signal):
        """Test signals are ordered by generated_at descending."""
        now = datetime.utcnow()

        # Save signals with different timestamps
        repo.save_signal(sample_signal, generated_at=now - timedelta(hours=2))
        repo.save_signal(sample_signal, generated_at=now - timedelta(hours=1))
        repo.save_signal(sample_signal, generated_at=now)

        signals = repo.get_signals()
        # Most recent should be first
        assert signals[0].generated_at > signals[1].generated_at
        assert signals[1].generated_at > signals[2].generated_at

    def test_get_signals_by_strategy(self, repo, sample_signal):
        """Test getting signals for a specific strategy."""
        repo.save_signal(sample_signal)
        repo.save_signal(
            TradingSignal(
                symbol="MSFT",
                side="sell",
                confidence=0.6,
                sharpe_estimate=1.2,
                entry_price=300.0,
                strategy_name="OtherStrategy",
            )
        )

        signals = repo.get_signals_by_strategy("TestStrategy")
        assert len(signals) == 1
        assert signals[0].strategy_name == "TestStrategy"

    def test_get_signals_by_strategy_with_date_range(self, repo, sample_signal):
        """Test getting signals by strategy with date range."""
        now = datetime.utcnow()
        yesterday = now - timedelta(days=1)
        tomorrow = now + timedelta(days=1)

        repo.save_signal(sample_signal, generated_at=now)
        repo.save_signal(sample_signal, generated_at=yesterday - timedelta(days=1))

        signals = repo.get_signals_by_strategy(
            "TestStrategy", start_date=yesterday, end_date=tomorrow
        )
        assert len(signals) == 1

    def test_get_execution_stats_basic(self, repo, sample_signal):
        """Test basic execution statistics."""
        # Save signals with different statuses
        saved1 = repo.save_signal(sample_signal)
        saved2 = repo.save_signal(sample_signal)
        saved3 = repo.save_signal(sample_signal)

        repo.update_signal_status(saved1.signal_id, "executed", executed_price=151.0)
        repo.update_signal_status(saved2.signal_id, "rejected", rejection_reason="risk")

        stats = repo.get_execution_stats()

        assert stats["total_signals"] == 3
        assert stats["executed_count"] == 1
        assert stats["rejected_count"] == 1
        assert stats["by_status"]["generated"] == 1
        assert stats["by_status"]["executed"] == 1
        assert stats["by_status"]["rejected"] == 1

    def test_get_execution_stats_slippage(self, repo, sample_signal):
        """Test execution statistics with slippage calculation."""
        saved1 = repo.save_signal(sample_signal)  # signal_price = 150.0
        saved2 = repo.save_signal(sample_signal)

        repo.update_signal_status(saved1.signal_id, "executed", executed_price=151.0)
        repo.update_signal_status(saved2.signal_id, "executed", executed_price=149.0)

        stats = repo.get_execution_stats()

        # Average slippage: (1.0 + -1.0) / 2 = 0.0
        assert stats["avg_slippage"] == 0.0

    def test_get_execution_stats_quality_score(self, repo, sample_signal):
        """Test execution statistics with quality score."""
        repo.save_signal(sample_signal)  # quality_score calculated from signal
        repo.save_signal(sample_signal)

        stats = repo.get_execution_stats()

        assert stats["avg_quality_score"] > 0
        assert stats["avg_quality_score"] == sample_signal.quality_score

    def test_get_execution_stats_with_date_range(self, repo, sample_signal):
        """Test execution statistics with date filter."""
        now = datetime.utcnow()
        yesterday = now - timedelta(days=1)

        repo.save_signal(sample_signal, generated_at=now)
        repo.save_signal(sample_signal, generated_at=yesterday - timedelta(days=1))

        stats = repo.get_execution_stats(start_date=yesterday)
        assert stats["total_signals"] == 1

    def test_get_rejection_summary(self, repo, sample_signal):
        """Test rejection summary aggregation."""
        saved1 = repo.save_signal(sample_signal)
        saved2 = repo.save_signal(sample_signal)
        saved3 = repo.save_signal(sample_signal)

        repo.update_signal_status(
            saved1.signal_id, "rejected", rejection_reason="max_position_exceeded"
        )
        repo.update_signal_status(
            saved2.signal_id, "rejected", rejection_reason="portfolio_risk_exceeded"
        )
        repo.update_signal_status(
            saved3.signal_id, "rejected", rejection_reason="max_position_exceeded"
        )

        summary = repo.get_rejection_summary()

        assert summary["max_position_exceeded"] == 2
        assert summary["portfolio_risk_exceeded"] == 1

    def test_get_rejection_summary_unknown_reason(self, repo, sample_signal):
        """Test rejection summary with unknown reason."""
        saved = repo.save_signal(sample_signal)
        repo.update_signal_status(saved.signal_id, "rejected")

        summary = repo.get_rejection_summary()
        assert summary["unknown"] == 1

    def test_get_rejection_summary_with_date_range(self, repo, sample_signal):
        """Test rejection summary with date filter."""
        now = datetime.utcnow()
        yesterday = now - timedelta(days=1)

        saved1 = repo.save_signal(sample_signal, generated_at=now)
        saved2 = repo.save_signal(sample_signal, generated_at=yesterday - timedelta(days=1))

        repo.update_signal_status(saved1.signal_id, "rejected", rejection_reason="risk1")
        repo.update_signal_status(saved2.signal_id, "rejected", rejection_reason="risk2")

        summary = repo.get_rejection_summary(start_date=yesterday)
        assert len(summary) == 1
        assert "risk1" in summary

    def test_trading_signal_conversion(self, repo):
        """Test complete conversion from TradingSignal to SignalRecord."""
        signal = TradingSignal(
            symbol="GOOGL",
            side="sell",
            confidence=0.75,
            sharpe_estimate=1.8,
            entry_price=2800.0,
            stop_loss=2850.0,
            take_profit=2750.0,
            strategy_name="MomentumStrategy",
        )

        record = repo.save_signal(signal)

        # Verify all fields converted correctly
        assert record.symbol == "GOOGL"
        assert record.direction == "SELL"
        assert record.strength == 0.75
        assert record.signal_price == 2800.0
        assert record.strategy_name == "MomentumStrategy"
        assert record.quality_score == signal.quality_score
        assert record.signal_metadata["stop_loss"] == 2850.0
        assert record.signal_metadata["take_profit"] == 2750.0

    def test_concurrent_writes_basic(self, repo, sample_signal):
        """Test basic thread safety with sequential writes."""
        # This is a basic test - full concurrent testing would require threading
        for i in range(10):
            repo.save_signal(sample_signal)

        signals = repo.get_signals()
        assert len(signals) == 10
