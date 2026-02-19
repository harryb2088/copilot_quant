"""
Database models for signal persistence.

This module provides SQLAlchemy models for persisting trading signals
throughout their lifecycle from generation to execution.
"""

import enum
from datetime import datetime

from sqlalchemy import JSON, Boolean, Column, DateTime, Float, Integer, String
from sqlalchemy.orm import declarative_base

Base = declarative_base()


class SignalStatus(enum.Enum):
    """Signal lifecycle status."""

    GENERATED = "generated"  # Signal created by strategy
    PASSED_RISK = "passed_risk"  # Passed risk checks
    REJECTED = "rejected"  # Failed risk checks
    SUBMITTED = "submitted"  # Order submitted to broker
    EXECUTED = "executed"  # Order filled
    PARTIALLY_FILLED = "partially_filled"
    CANCELLED = "cancelled"  # Order cancelled
    EXPIRED = "expired"  # Signal expired before execution
    MISSED = "missed"  # Signal missed (market closed, etc.)
    ERROR = "error"  # Error during processing


class SignalRecord(Base):
    """SQLAlchemy model for persisting trading signals."""

    __tablename__ = "signals"

    id = Column(Integer, primary_key=True, autoincrement=True)

    # Signal identification
    signal_id = Column(String, unique=True, nullable=False)  # UUID
    strategy_name = Column(String, nullable=False)
    symbol = Column(String, nullable=False)

    # Signal details
    signal_type = Column(String)  # e.g., 'entry', 'exit', 'rebalance'
    direction = Column(String)  # 'BUY' or 'SELL'
    strength = Column(Float)  # Signal strength/confidence
    quality_score = Column(Float)  # Quality score from signal architecture

    # Timing
    generated_at = Column(DateTime, nullable=False)
    processed_at = Column(DateTime)
    executed_at = Column(DateTime)

    # Execution details
    status = Column(String, nullable=False, default="generated")
    rejection_reason = Column(String)

    # Price information
    signal_price = Column(Float)  # Price when signal was generated
    target_price = Column(Float)  # Target/limit price
    executed_price = Column(Float)  # Actual fill price
    slippage = Column(Float)  # Difference between signal and fill

    # Position sizing
    requested_quantity = Column(Integer)
    executed_quantity = Column(Integer)
    position_value = Column(Float)

    # Risk check results
    risk_check_passed = Column(Boolean)
    risk_check_details = Column(JSON)  # Detailed risk check results

    # Metadata
    signal_metadata = Column(JSON)  # Strategy-specific metadata
    order_id = Column(String)  # Broker order ID if submitted

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return (
            f"<SignalRecord(id={self.id}, signal_id={self.signal_id}, "
            f"symbol={self.symbol}, status={self.status}, "
            f"strategy={self.strategy_name})>"
        )
