"""
Portfolio State Manager for Persistent Portfolio Tracking

This module provides the PortfolioStateManager class that maintains persistent
local portfolio state with synchronization to IBKR. It stores NAV, drawdown,
position PnL snapshots, and ensures state survives restarts.

Features:
- Persistent local portfolio state (SQLite or PostgreSQL)
- Sync local positions with IBKR on startup and periodically
- Store NAV, drawdown, and position PnL snapshots
- Survive restarts without losing positions or state
- Historical, queryable portfolio NAV/equity curves
- Reconciliation with broker state

Example Usage:
    >>> from copilot_quant.live import PortfolioStateManager
    >>>
    >>> manager = PortfolioStateManager(
    ...     database_url="sqlite:///portfolio_state.db",
    ...     broker=live_broker_adapter
    ... )
    >>>
    >>> # Initialize and sync with broker
    >>> manager.initialize()
    >>>
    >>> # Take snapshot
    >>> manager.take_snapshot()
    >>>
    >>> # Get current state
    >>> state = manager.get_current_state()
    >>>
    >>> # Get historical equity curve
    >>> equity_curve = manager.get_equity_curve(days=30)
"""

import logging
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from typing import Any, Dict, List, Optional

import pandas as pd
from sqlalchemy import Boolean, Column, Date, DateTime, Float, ForeignKey, Integer, String, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
from sqlalchemy.pool import StaticPool

from copilot_quant.brokers.live_broker_adapter import LiveBrokerAdapter

logger = logging.getLogger(__name__)

Base = declarative_base()


@dataclass
class PortfolioSnapshot:
    """
    Snapshot of portfolio state at a point in time.

    Attributes:
        timestamp: Snapshot timestamp
        nav: Net asset value
        cash: Cash balance
        equity_value: Total equity value
        num_positions: Number of open positions
        drawdown: Current drawdown from peak
        daily_pnl: Daily profit/loss
    """

    timestamp: datetime
    nav: float
    cash: float
    equity_value: float
    num_positions: int
    drawdown: float
    daily_pnl: float


class PortfolioSnapshotModel(Base):
    """SQLAlchemy model for portfolio snapshots"""

    __tablename__ = "portfolio_snapshots"

    id = Column(Integer, primary_key=True, autoincrement=True)
    timestamp = Column(DateTime, nullable=False, index=True)
    snapshot_date = Column(Date, nullable=False, index=True)
    nav = Column(Float, nullable=False)
    cash = Column(Float, nullable=False)
    equity_value = Column(Float, nullable=False)
    num_positions = Column(Integer, nullable=False)
    drawdown = Column(Float, nullable=False)
    daily_pnl = Column(Float, nullable=False)
    peak_nav = Column(Float, nullable=False)

    # Relationships
    positions = relationship("PositionSnapshotModel", back_populates="portfolio_snapshot")

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "id": self.id,
            "timestamp": self.timestamp.isoformat(),
            "snapshot_date": self.snapshot_date.isoformat(),
            "nav": self.nav,
            "cash": self.cash,
            "equity_value": self.equity_value,
            "num_positions": self.num_positions,
            "drawdown": self.drawdown,
            "daily_pnl": self.daily_pnl,
            "peak_nav": self.peak_nav,
        }


class PositionSnapshotModel(Base):
    """SQLAlchemy model for position snapshots"""

    __tablename__ = "position_snapshots"

    id = Column(Integer, primary_key=True, autoincrement=True)
    portfolio_snapshot_id = Column(Integer, ForeignKey("portfolio_snapshots.id"), nullable=False)
    symbol = Column(String(20), nullable=False, index=True)
    quantity = Column(Integer, nullable=False)
    avg_cost = Column(Float, nullable=False)
    current_price = Column(Float, nullable=False)
    market_value = Column(Float, nullable=False)
    unrealized_pnl = Column(Float, nullable=False)
    realized_pnl = Column(Float, nullable=False)

    # Relationship
    portfolio_snapshot = relationship("PortfolioSnapshotModel", back_populates="positions")

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "id": self.id,
            "symbol": self.symbol,
            "quantity": self.quantity,
            "avg_cost": self.avg_cost,
            "current_price": self.current_price,
            "market_value": self.market_value,
            "unrealized_pnl": self.unrealized_pnl,
            "realized_pnl": self.realized_pnl,
        }


class ReconciliationLogModel(Base):
    """SQLAlchemy model for reconciliation logs"""

    __tablename__ = "reconciliation_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    timestamp = Column(DateTime, nullable=False, index=True)
    reconciliation_date = Column(Date, nullable=False, index=True)
    ibkr_nav = Column(Float, nullable=False)
    local_nav = Column(Float, nullable=False)
    nav_difference = Column(Float, nullable=False)
    positions_matched = Column(Boolean, nullable=False)
    discrepancies_found = Column(Integer, default=0)
    notes = Column(String(500), nullable=True)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "id": self.id,
            "timestamp": self.timestamp.isoformat(),
            "reconciliation_date": self.reconciliation_date.isoformat(),
            "ibkr_nav": self.ibkr_nav,
            "local_nav": self.local_nav,
            "nav_difference": self.nav_difference,
            "positions_matched": self.positions_matched,
            "discrepancies_found": self.discrepancies_found,
            "notes": self.notes,
        }


class PortfolioStateManager:
    """
    Manages persistent portfolio state with IBKR synchronization.

    This class maintains a local database of portfolio state including NAV,
    positions, drawdown, and equity curve. It synchronizes with IBKR on
    startup and periodically to ensure consistency. State survives restarts
    and provides historical queryable data.

    Features:
    - Persistent portfolio state storage
    - Automatic IBKR reconciliation
    - NAV and equity curve tracking
    - Drawdown calculation
    - Position snapshot history
    - Query interface for analytics

    Example:
        >>> manager = PortfolioStateManager(
        ...     database_url="sqlite:///portfolio.db",
        ...     broker=broker_adapter
        ... )
        >>> manager.initialize()
        >>> manager.take_snapshot()
        >>> equity = manager.get_equity_curve(days=30)
    """

    def __init__(
        self,
        broker: LiveBrokerAdapter,
        database_url: str = "sqlite:///portfolio_state.db",
        sync_interval_minutes: int = 5,
        snapshot_interval_minutes: int = 15,
    ):
        """
        Initialize portfolio state manager.

        Args:
            broker: LiveBrokerAdapter instance for IBKR integration
            database_url: SQLAlchemy database URL for persistence
            sync_interval_minutes: How often to sync with IBKR (in minutes)
            snapshot_interval_minutes: How often to take snapshots (in minutes)
        """
        self.broker = broker
        self.sync_interval_minutes = sync_interval_minutes
        self.snapshot_interval_minutes = snapshot_interval_minutes

        # Initialize database
        if database_url == "sqlite:///:memory:":
            self.engine = create_engine(database_url, connect_args={"check_same_thread": False}, poolclass=StaticPool)
        else:
            self.engine = create_engine(database_url)

        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)

        # Create tables
        Base.metadata.create_all(bind=self.engine)

        # State tracking
        self._peak_nav = 0.0
        self._last_sync_time: Optional[datetime] = None
        self._last_snapshot_time: Optional[datetime] = None
        self._initialized = False

        logger.info(f"PortfolioStateManager initialized with {database_url}")

    def initialize(self) -> bool:
        """
        Initialize state manager and sync with IBKR.

        This should be called once at startup. It loads the most recent
        state from the database and reconciles with current IBKR state.

        Returns:
            True if initialization successful, False otherwise
        """
        try:
            logger.info("Initializing portfolio state manager...")

            # Load last known state
            last_snapshot = self._get_latest_snapshot()

            if last_snapshot:
                self._peak_nav = last_snapshot.peak_nav
                logger.info(f"Loaded last snapshot: NAV=${last_snapshot.nav:,.2f} from {last_snapshot.timestamp}")
            else:
                logger.info("No previous snapshots found - starting fresh")

            # Sync with IBKR
            if not self.sync_with_broker():
                logger.error("Failed to sync with broker during initialization")
                return False

            # Take initial snapshot
            self.take_snapshot()

            self._initialized = True
            logger.info("✓ Portfolio state manager initialized")
            return True

        except Exception as e:
            logger.error(f"Error initializing state manager: {e}", exc_info=True)
            return False

    def sync_with_broker(self) -> bool:
        """
        Synchronize local state with IBKR broker.

        Fetches current positions and account value from IBKR and
        logs any discrepancies.

        Returns:
            True if sync successful, False otherwise
        """
        try:
            if not self.broker.is_connected():
                logger.warning("Cannot sync - broker not connected")
                return False

            # Get broker state
            ibkr_nav = self.broker.get_account_value()
            ibkr_positions = self.broker.get_positions()

            # Get local state
            last_snapshot = self._get_latest_snapshot()
            local_nav = last_snapshot.nav if last_snapshot else 0.0

            # Calculate difference (signed - positive means IBKR > local)
            nav_diff = (ibkr_nav - local_nav) if last_snapshot else 0.0
            nav_diff_pct = (nav_diff / local_nav * 100) if local_nav > 0 else 0.0

            # Log reconciliation
            positions_matched = True  # TODO: Compare positions in detail

            self._log_reconciliation(
                ibkr_nav=ibkr_nav,
                local_nav=local_nav,
                nav_difference=nav_diff,
                positions_matched=positions_matched,
                discrepancies_found=0,
                notes=f"NAV diff: ${nav_diff:.2f} ({nav_diff_pct:.2f}%)",
            )

            if nav_diff_pct > 1.0:
                logger.warning(
                    f"NAV discrepancy: IBKR=${ibkr_nav:,.2f} vs Local=${local_nav:,.2f} (diff={nav_diff_pct:.2f}%)"
                )
            else:
                logger.info(f"✓ Synced with broker: NAV=${ibkr_nav:,.2f}, Positions={len(ibkr_positions)}")

            self._last_sync_time = datetime.now()
            return True

        except Exception as e:
            logger.error(f"Error syncing with broker: {e}", exc_info=True)
            return False

    def take_snapshot(self) -> bool:
        """
        Take a snapshot of current portfolio state.

        Captures current NAV, positions, cash, drawdown, and PnL.

        Returns:
            True if snapshot successful, False otherwise
        """
        try:
            if not self.broker.is_connected():
                logger.warning("Cannot take snapshot - broker not connected")
                return False

            # Get current state from broker
            nav = self.broker.get_account_value()
            cash = self.broker.get_cash_balance()
            positions = self.broker.get_positions()

            # Calculate equity value
            equity_value = 0.0
            for pos in positions.values():
                price = getattr(pos, "current_price", None) or getattr(pos, "avg_entry_price", 0)
                equity_value += abs(pos.quantity * price)

            # Update peak NAV
            if nav > self._peak_nav:
                self._peak_nav = nav

            # Calculate drawdown
            drawdown = ((self._peak_nav - nav) / self._peak_nav) if self._peak_nav > 0 else 0.0

            # Calculate daily PnL
            last_snapshot = self._get_latest_snapshot()
            if last_snapshot and last_snapshot.snapshot_date == date.today():
                # Already have snapshot today - calculate from that
                daily_pnl = nav - last_snapshot.nav
            elif last_snapshot:
                # New day - PnL from yesterday's close
                daily_pnl = nav - last_snapshot.nav
            else:
                daily_pnl = 0.0

            # Store snapshot
            self._store_snapshot(
                nav=nav,
                cash=cash,
                equity_value=equity_value,
                num_positions=len(positions),
                drawdown=drawdown,
                daily_pnl=daily_pnl,
                peak_nav=self._peak_nav,
                positions=positions,
            )

            self._last_snapshot_time = datetime.now()

            logger.info(f"✓ Snapshot taken: NAV=${nav:,.2f}, Drawdown={drawdown:.2%}, Positions={len(positions)}")

            return True

        except Exception as e:
            logger.error(f"Error taking snapshot: {e}", exc_info=True)
            return False

    def should_sync(self) -> bool:
        """
        Check if it's time to sync with broker.

        Returns:
            True if sync is due, False otherwise
        """
        if self._last_sync_time is None:
            return True

        elapsed = (datetime.now() - self._last_sync_time).total_seconds() / 60
        return elapsed >= self.sync_interval_minutes

    def should_snapshot(self) -> bool:
        """
        Check if it's time to take a snapshot.

        Returns:
            True if snapshot is due, False otherwise
        """
        if self._last_snapshot_time is None:
            return True

        elapsed = (datetime.now() - self._last_snapshot_time).total_seconds() / 60
        return elapsed >= self.snapshot_interval_minutes

    def get_current_state(self) -> Optional[PortfolioSnapshot]:
        """
        Get current portfolio state.

        Returns:
            PortfolioSnapshot with current state, or None if not available
        """
        snapshot_model = self._get_latest_snapshot()

        if snapshot_model is None:
            return None

        return PortfolioSnapshot(
            timestamp=snapshot_model.timestamp,
            nav=snapshot_model.nav,
            cash=snapshot_model.cash,
            equity_value=snapshot_model.equity_value,
            num_positions=snapshot_model.num_positions,
            drawdown=snapshot_model.drawdown,
            daily_pnl=snapshot_model.daily_pnl,
        )

    def get_equity_curve(self, days: int = 30) -> pd.DataFrame:
        """
        Get historical equity curve.

        Args:
            days: Number of days of history to retrieve

        Returns:
            DataFrame with timestamp, nav, drawdown, daily_pnl columns
        """
        start_date = date.today() - timedelta(days=days)

        with self._get_session() as session:
            snapshots = (
                session.query(PortfolioSnapshotModel)
                .filter(PortfolioSnapshotModel.snapshot_date >= start_date)
                .order_by(PortfolioSnapshotModel.timestamp)
                .all()
            )

            if not snapshots:
                return pd.DataFrame()

            data = {
                "timestamp": [s.timestamp for s in snapshots],
                "nav": [s.nav for s in snapshots],
                "cash": [s.cash for s in snapshots],
                "equity_value": [s.equity_value for s in snapshots],
                "drawdown": [s.drawdown for s in snapshots],
                "daily_pnl": [s.daily_pnl for s in snapshots],
                "num_positions": [s.num_positions for s in snapshots],
            }

            df = pd.DataFrame(data)
            df.set_index("timestamp", inplace=True)

            return df

    def get_reconciliation_history(self, days: int = 7) -> List[ReconciliationLogModel]:
        """
        Get reconciliation history.

        Args:
            days: Number of days of history to retrieve

        Returns:
            List of ReconciliationLogModel objects
        """
        start_date = date.today() - timedelta(days=days)

        with self._get_session() as session:
            logs = (
                session.query(ReconciliationLogModel)
                .filter(ReconciliationLogModel.reconciliation_date >= start_date)
                .order_by(ReconciliationLogModel.timestamp.desc())
                .all()
            )

            session.expunge_all()
            return logs

    def _get_session(self):
        """Get database session context manager"""
        return self.SessionLocal()

    def _get_latest_snapshot(self) -> Optional[PortfolioSnapshotModel]:
        """Get the most recent portfolio snapshot"""
        session = self._get_session()
        try:
            snapshot = session.query(PortfolioSnapshotModel).order_by(PortfolioSnapshotModel.timestamp.desc()).first()

            if snapshot:
                session.expunge(snapshot)
            return snapshot
        finally:
            session.close()

    def _store_snapshot(
        self,
        nav: float,
        cash: float,
        equity_value: float,
        num_positions: int,
        drawdown: float,
        daily_pnl: float,
        peak_nav: float,
        positions: Dict,
    ) -> None:
        """Store a portfolio snapshot"""
        session = self._get_session()
        try:
            snapshot = PortfolioSnapshotModel(
                timestamp=datetime.now(),
                snapshot_date=date.today(),
                nav=nav,
                cash=cash,
                equity_value=equity_value,
                num_positions=num_positions,
                drawdown=drawdown,
                daily_pnl=daily_pnl,
                peak_nav=peak_nav,
            )

            session.add(snapshot)
            session.flush()

            # Store position snapshots
            for symbol, position in positions.items():
                # Handle different position attribute names
                avg_cost = getattr(position, "avg_cost", getattr(position, "avg_entry_price", 0))
                current_price = getattr(position, "current_price", getattr(position, "avg_entry_price", 0))

                pos_snapshot = PositionSnapshotModel(
                    portfolio_snapshot_id=snapshot.id,
                    symbol=symbol,
                    quantity=position.quantity,
                    avg_cost=avg_cost,
                    current_price=current_price,
                    market_value=position.quantity * current_price,
                    unrealized_pnl=position.unrealized_pnl,
                    realized_pnl=position.realized_pnl,
                )
                session.add(pos_snapshot)

            session.commit()

        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def _log_reconciliation(
        self,
        ibkr_nav: float,
        local_nav: float,
        nav_difference: float,
        positions_matched: bool,
        discrepancies_found: int,
        notes: Optional[str] = None,
    ) -> None:
        """Log a reconciliation event"""
        session = self._get_session()
        try:
            log = ReconciliationLogModel(
                timestamp=datetime.now(),
                reconciliation_date=date.today(),
                ibkr_nav=ibkr_nav,
                local_nav=local_nav,
                nav_difference=nav_difference,
                positions_matched=positions_matched,
                discrepancies_found=discrepancies_found,
                notes=notes,
            )

            session.add(log)
            session.commit()

        except Exception:
            session.rollback()
            raise
        finally:
            session.close()
