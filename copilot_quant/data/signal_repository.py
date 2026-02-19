"""
Signal repository for database operations.

This module provides the SignalRepository class for persisting and querying
trading signals throughout their lifecycle.
"""

import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from copilot_quant.backtest.signals import TradingSignal
from copilot_quant.data.models import Base, SignalRecord


class SignalRepository:
    """Repository for signal persistence and querying."""

    def __init__(self, db_url: str = "sqlite:///data/signals.db"):
        """
        Initialize the signal repository.

        Args:
            db_url: Database URL (SQLite default, supports PostgreSQL)
        """
        # Ensure data directory exists for SQLite
        if db_url.startswith("sqlite:///"):
            db_path = db_url.replace("sqlite:///", "")
            Path(db_path).parent.mkdir(parents=True, exist_ok=True)

        self.engine = create_engine(db_url)
        self.SessionLocal = sessionmaker(bind=self.engine)

        # Create tables if they don't exist
        Base.metadata.create_all(self.engine)

    def save_signal(
        self,
        signal: TradingSignal,
        status: str = "generated",
        signal_id: Optional[str] = None,
        **kwargs,
    ) -> SignalRecord:
        """
        Persist a new signal to the database.

        Args:
            signal: TradingSignal instance to persist
            status: Initial status (default: "generated")
            signal_id: Optional signal ID (generated if not provided)
            **kwargs: Additional fields to set on the SignalRecord

        Returns:
            SignalRecord: The persisted signal record
        """
        session = self.SessionLocal()
        try:
            # Generate signal ID if not provided
            if signal_id is None:
                signal_id = str(uuid.uuid4())

            # Convert TradingSignal to SignalRecord
            record = SignalRecord(
                signal_id=signal_id,
                strategy_name=signal.strategy_name or "unknown",
                symbol=signal.symbol,
                direction=signal.side.upper(),
                strength=signal.confidence,
                quality_score=signal.quality_score,
                signal_price=signal.entry_price,
                target_price=kwargs.get("target_price", signal.take_profit),
                status=status,
                generated_at=kwargs.get("generated_at", datetime.utcnow()),
            )

            # Set additional fields from kwargs
            for key, value in kwargs.items():
                if hasattr(record, key) and key not in [
                    "signal_id",
                    "strategy_name",
                    "symbol",
                    "direction",
                    "strength",
                    "quality_score",
                    "signal_price",
                    "status",
                    "generated_at",
                ]:
                    setattr(record, key, value)

            # Store stop loss and take profit in metadata if present
            metadata = kwargs.get("signal_metadata", {})
            if signal.stop_loss is not None:
                metadata["stop_loss"] = signal.stop_loss
            if signal.take_profit is not None:
                metadata["take_profit"] = signal.take_profit
            record.signal_metadata = metadata if metadata else None

            session.add(record)
            session.commit()
            session.refresh(record)
            return record
        finally:
            session.close()

    def update_signal_status(
        self, signal_id: str, status: str, **kwargs
    ) -> bool:
        """
        Update signal status and related fields.

        Args:
            signal_id: Signal ID to update
            status: New status
            **kwargs: Additional fields to update

        Returns:
            bool: True if update successful, False if signal not found
        """
        session = self.SessionLocal()
        try:
            record = session.query(SignalRecord).filter(
                SignalRecord.signal_id == signal_id
            ).first()

            if not record:
                return False

            # Update status
            record.status = status
            record.updated_at = datetime.utcnow()

            # Update additional fields
            for key, value in kwargs.items():
                if hasattr(record, key):
                    setattr(record, key, value)

            # Calculate slippage if executed_price is set
            if (
                record.executed_price is not None
                and record.signal_price is not None
            ):
                record.slippage = record.executed_price - record.signal_price

            session.commit()
            return True
        finally:
            session.close()

    def get_signal_by_id(self, signal_id: str) -> Optional[SignalRecord]:
        """
        Get a specific signal by ID.

        Args:
            signal_id: Signal ID to retrieve

        Returns:
            SignalRecord or None if not found
        """
        session = self.SessionLocal()
        try:
            return session.query(SignalRecord).filter(
                SignalRecord.signal_id == signal_id
            ).first()
        finally:
            session.close()

    def get_signals(
        self, filters: Optional[Dict[str, Any]] = None, limit: int = 100
    ) -> List[SignalRecord]:
        """
        Query signals with optional filters.

        Args:
            filters: Dictionary of filter criteria
                - symbol: Filter by symbol
                - strategy: Filter by strategy name
                - status: Filter by status
                - start_date: Filter by generated_at >= start_date
                - end_date: Filter by generated_at <= end_date
            limit: Maximum number of results

        Returns:
            List of SignalRecord instances
        """
        session = self.SessionLocal()
        try:
            query = session.query(SignalRecord)

            if filters:
                if "symbol" in filters:
                    query = query.filter(SignalRecord.symbol == filters["symbol"])
                if "strategy" in filters:
                    query = query.filter(
                        SignalRecord.strategy_name == filters["strategy"]
                    )
                if "status" in filters:
                    query = query.filter(SignalRecord.status == filters["status"])
                if "start_date" in filters:
                    query = query.filter(
                        SignalRecord.generated_at >= filters["start_date"]
                    )
                if "end_date" in filters:
                    query = query.filter(
                        SignalRecord.generated_at <= filters["end_date"]
                    )

            # Order by generated_at descending (most recent first)
            query = query.order_by(SignalRecord.generated_at.desc())

            return query.limit(limit).all()
        finally:
            session.close()

    def get_signals_by_strategy(
        self,
        strategy_name: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> List[SignalRecord]:
        """
        Get all signals for a strategy in a date range.

        Args:
            strategy_name: Strategy name to filter by
            start_date: Optional start date filter
            end_date: Optional end date filter

        Returns:
            List of SignalRecord instances
        """
        filters = {"strategy": strategy_name}
        if start_date:
            filters["start_date"] = start_date
        if end_date:
            filters["end_date"] = end_date

        return self.get_signals(filters=filters, limit=10000)

    def get_execution_stats(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> Dict[str, Any]:
        """
        Get aggregated execution statistics.

        Args:
            start_date: Optional start date filter
            end_date: Optional end date filter

        Returns:
            Dictionary with execution statistics:
                - total_signals: Total number of signals
                - by_status: Count of signals by status
                - executed_count: Number of executed signals
                - rejected_count: Number of rejected signals
                - avg_slippage: Average slippage
                - avg_quality_score: Average quality score
        """
        session = self.SessionLocal()
        try:
            query = session.query(SignalRecord)

            if start_date:
                query = query.filter(SignalRecord.generated_at >= start_date)
            if end_date:
                query = query.filter(SignalRecord.generated_at <= end_date)

            all_signals = query.all()

            # Count by status
            status_counts = {}
            for signal in all_signals:
                status = signal.status
                status_counts[status] = status_counts.get(status, 0) + 1

            # Calculate averages
            executed_signals = [s for s in all_signals if s.slippage is not None]
            avg_slippage = (
                sum(s.slippage for s in executed_signals) / len(executed_signals)
                if executed_signals
                else 0.0
            )

            quality_signals = [s for s in all_signals if s.quality_score is not None]
            avg_quality = (
                sum(s.quality_score for s in quality_signals) / len(quality_signals)
                if quality_signals
                else 0.0
            )

            return {
                "total_signals": len(all_signals),
                "by_status": status_counts,
                "executed_count": status_counts.get("executed", 0),
                "rejected_count": status_counts.get("rejected", 0),
                "avg_slippage": avg_slippage,
                "avg_quality_score": avg_quality,
            }
        finally:
            session.close()

    def get_rejection_summary(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> Dict[str, int]:
        """
        Get summary of rejection reasons.

        Args:
            start_date: Optional start date filter
            end_date: Optional end date filter

        Returns:
            Dictionary mapping rejection reason to count
        """
        session = self.SessionLocal()
        try:
            query = session.query(SignalRecord).filter(
                SignalRecord.status == "rejected"
            )

            if start_date:
                query = query.filter(SignalRecord.generated_at >= start_date)
            if end_date:
                query = query.filter(SignalRecord.generated_at <= end_date)

            rejected_signals = query.all()

            # Count by rejection reason
            rejection_counts = {}
            for signal in rejected_signals:
                reason = signal.rejection_reason or "unknown"
                rejection_counts[reason] = rejection_counts.get(reason, 0) + 1

            return rejection_counts
        finally:
            session.close()
