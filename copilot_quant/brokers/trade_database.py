"""
Trade Database Module for Audit Trail and Portfolio Snapshots

Provides SQLAlchemy-based database storage for trade logging, audit trail,
and historical portfolio snapshots.

Features:
- Store orders with full lifecycle tracking
- Store individual fills with execution details
- Store reconciliation reports and discrepancies
- Query portfolio snapshots with NAV, drawdown, equity curves
- Query position snapshots at specific points in time
- Export functionality for compliance reports

Example:
    >>> from copilot_quant.brokers.trade_database import TradeDatabase
    >>> db = TradeDatabase("sqlite:///trades.db")
    >>>
    >>> # Store trade data
    >>> db.store_order(order_record)
    >>> db.store_fill(fill_record)
    >>>
    >>> # Query portfolio snapshots
    >>> snapshots = db.get_portfolio_snapshots(start_date=date(2024, 1, 1))
    >>> equity_curve = db.get_equity_curve(start_date=date(2024, 1, 1))
    >>>
    >>> # Get audit trail
    >>> orders = db.get_orders_by_date(date.today())
"""

import logging
from contextlib import contextmanager
from datetime import date, datetime
from typing import Any, Dict, List, Optional

from sqlalchemy import JSON, Column, Date, DateTime, Float, ForeignKey, Integer, String, Text, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Session, relationship, sessionmaker
from sqlalchemy.pool import StaticPool

from .order_execution_handler import Fill, OrderRecord
from .trade_reconciliation import DiscrepancyType, ReconciliationReport

logger = logging.getLogger(__name__)

Base = declarative_base()


class OrderModel(Base):
    """SQLAlchemy model for orders"""

    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, autoincrement=True)
    order_id = Column(Integer, nullable=False, index=True)
    symbol = Column(String(20), nullable=False, index=True)
    action = Column(String(10), nullable=False)  # BUY or SELL
    total_quantity = Column(Integer, nullable=False)
    order_type = Column(String(20), nullable=False)  # MARKET, LIMIT, etc.
    limit_price = Column(Float, nullable=True)
    status = Column(String(30), nullable=False, index=True)
    filled_quantity = Column(Integer, default=0)
    remaining_quantity = Column(Integer, nullable=False)
    avg_fill_price = Column(Float, default=0.0)
    error_message = Column(Text, nullable=True)
    submission_time = Column(DateTime, nullable=False, index=True)
    last_update_time = Column(DateTime, nullable=False)
    retry_count = Column(Integer, default=0)

    # Relationships
    fills = relationship("FillModel", back_populates="order", cascade="all, delete-orphan")

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "id": self.id,
            "order_id": self.order_id,
            "symbol": self.symbol,
            "action": self.action,
            "total_quantity": self.total_quantity,
            "order_type": self.order_type,
            "limit_price": self.limit_price,
            "status": self.status,
            "filled_quantity": self.filled_quantity,
            "remaining_quantity": self.remaining_quantity,
            "avg_fill_price": self.avg_fill_price,
            "error_message": self.error_message,
            "submission_time": self.submission_time.isoformat(),
            "last_update_time": self.last_update_time.isoformat(),
            "retry_count": self.retry_count,
        }


class FillModel(Base):
    """SQLAlchemy model for fills"""

    __tablename__ = "fills"

    id = Column(Integer, primary_key=True, autoincrement=True)
    fill_id = Column(String(100), nullable=False, unique=True, index=True)
    order_id = Column(Integer, nullable=False, index=True)
    order_db_id = Column(Integer, ForeignKey("orders.id"), nullable=True)
    symbol = Column(String(20), nullable=False, index=True)
    quantity = Column(Integer, nullable=False)
    price = Column(Float, nullable=False)
    commission = Column(Float, default=0.0)
    timestamp = Column(DateTime, nullable=False, index=True)

    # Relationship
    order = relationship("OrderModel", back_populates="fills")

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "id": self.id,
            "fill_id": self.fill_id,
            "order_id": self.order_id,
            "symbol": self.symbol,
            "quantity": self.quantity,
            "price": self.price,
            "commission": self.commission,
            "timestamp": self.timestamp.isoformat(),
        }


class ReconciliationReportModel(Base):
    """SQLAlchemy model for reconciliation reports"""

    __tablename__ = "reconciliation_reports"

    id = Column(Integer, primary_key=True, autoincrement=True)
    reconciliation_date = Column(Date, nullable=False, index=True)
    timestamp = Column(DateTime, nullable=False)
    total_ibkr_fills = Column(Integer, default=0)
    total_local_fills = Column(Integer, default=0)
    matched_orders = Column(Integer, default=0)
    total_discrepancies = Column(Integer, default=0)
    summary_json = Column(JSON, nullable=True)

    # Relationships
    discrepancies = relationship("DiscrepancyModel", back_populates="report", cascade="all, delete-orphan")

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "id": self.id,
            "reconciliation_date": self.reconciliation_date.isoformat(),
            "timestamp": self.timestamp.isoformat(),
            "total_ibkr_fills": self.total_ibkr_fills,
            "total_local_fills": self.total_local_fills,
            "matched_orders": self.matched_orders,
            "total_discrepancies": self.total_discrepancies,
            "summary_json": self.summary_json,
        }


class DiscrepancyModel(Base):
    """SQLAlchemy model for discrepancies"""

    __tablename__ = "discrepancies"

    id = Column(Integer, primary_key=True, autoincrement=True)
    report_id = Column(Integer, ForeignKey("reconciliation_reports.id"), nullable=False)
    type = Column(String(50), nullable=False, index=True)
    order_id = Column(Integer, nullable=False, index=True)
    symbol = Column(String(20), nullable=False, index=True)
    description = Column(Text, nullable=True)
    ibkr_fill_json = Column(JSON, nullable=True)
    local_fill_json = Column(JSON, nullable=True)

    # Relationship
    report = relationship("ReconciliationReportModel", back_populates="discrepancies")

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "id": self.id,
            "report_id": self.report_id,
            "type": self.type,
            "order_id": self.order_id,
            "symbol": self.symbol,
            "description": self.description,
            "ibkr_fill": self.ibkr_fill_json,
            "local_fill": self.local_fill_json,
        }


class TradeDatabase:
    """
    Database interface for trade audit trail storage.

    Provides methods to store and query orders, fills, and reconciliation data.
    Uses SQLAlchemy for database abstraction.

    Example:
        >>> db = TradeDatabase("sqlite:///trades.db")
        >>> db.store_order(order_record)
        >>> orders = db.get_orders_by_symbol("AAPL")
    """

    def __init__(self, database_url: str = "sqlite:///trade_audit.db", echo: bool = False):
        """
        Initialize trade database.

        Args:
            database_url: SQLAlchemy database URL
                         (default: sqlite:///trade_audit.db)
            echo: If True, log all SQL statements (for debugging)
        """
        # Handle in-memory SQLite specially to avoid threading issues
        if database_url == "sqlite:///:memory:":
            self.engine = create_engine(
                database_url, connect_args={"check_same_thread": False}, poolclass=StaticPool, echo=echo
            )
        else:
            self.engine = create_engine(database_url, echo=echo)

        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)

        # Create tables
        Base.metadata.create_all(bind=self.engine)

        logger.info(f"TradeDatabase initialized with {database_url}")

    @contextmanager
    def get_session(self) -> Session:
        """
        Context manager for database sessions.

        Yields:
            SQLAlchemy Session
        """
        session = self.SessionLocal()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def store_order(self, order_record: OrderRecord) -> int:
        """
        Store an order in the database.

        Args:
            order_record: OrderRecord to store

        Returns:
            Database ID of the stored order
        """
        with self.get_session() as session:
            # Check if order already exists
            existing = session.query(OrderModel).filter_by(order_id=order_record.order_id).first()

            if existing:
                # Update existing order
                existing.status = order_record.status.value
                existing.filled_quantity = order_record.filled_quantity
                existing.remaining_quantity = order_record.remaining_quantity
                existing.avg_fill_price = order_record.avg_fill_price
                existing.error_message = order_record.error_message
                existing.last_update_time = order_record.last_update_time
                existing.retry_count = order_record.retry_count

                logger.debug(f"Updated order {order_record.order_id} in database")
                return existing.id
            else:
                # Create new order
                order_model = OrderModel(
                    order_id=order_record.order_id,
                    symbol=order_record.symbol,
                    action=order_record.action,
                    total_quantity=order_record.total_quantity,
                    order_type=order_record.order_type,
                    limit_price=order_record.limit_price,
                    status=order_record.status.value,
                    filled_quantity=order_record.filled_quantity,
                    remaining_quantity=order_record.remaining_quantity,
                    avg_fill_price=order_record.avg_fill_price,
                    error_message=order_record.error_message,
                    submission_time=order_record.submission_time,
                    last_update_time=order_record.last_update_time,
                    retry_count=order_record.retry_count,
                )

                session.add(order_model)
                session.flush()

                logger.info(f"Stored new order {order_record.order_id} in database")
                return order_model.id

    def store_fill(self, fill: Fill, order_id: int) -> int:
        """
        Store a fill in the database.

        Args:
            fill: Fill object to store
            order_id: Associated order ID

        Returns:
            Database ID of the stored fill
        """
        with self.get_session() as session:
            # Check if fill already exists
            existing = session.query(FillModel).filter_by(fill_id=fill.fill_id).first()

            if existing:
                logger.debug(f"Fill {fill.fill_id} already exists in database")
                return existing.id

            # Get order database ID if available
            order_db_id = None
            order = session.query(OrderModel).filter_by(order_id=order_id).first()
            if order:
                order_db_id = order.id

            # Create new fill
            fill_model = FillModel(
                fill_id=fill.fill_id,
                order_id=order_id,
                order_db_id=order_db_id,
                symbol=fill.symbol,
                quantity=fill.quantity,
                price=fill.price,
                commission=fill.commission,
                timestamp=fill.timestamp,
            )

            session.add(fill_model)
            session.flush()

            logger.info(f"Stored fill {fill.fill_id} for order {order_id} in database")
            return fill_model.id

    def store_reconciliation_report(self, report: ReconciliationReport) -> int:
        """
        Store a reconciliation report in the database.

        Args:
            report: ReconciliationReport to store

        Returns:
            Database ID of the stored report
        """
        with self.get_session() as session:
            summary = report.summary()

            # Create report model
            report_model = ReconciliationReportModel(
                reconciliation_date=report.reconciliation_date,
                timestamp=report.timestamp,
                total_ibkr_fills=summary["total_ibkr_fills"],
                total_local_fills=summary["total_local_fills"],
                matched_orders=summary["matched_orders"],
                total_discrepancies=summary["total_discrepancies"],
                summary_json=summary,
            )

            session.add(report_model)
            session.flush()

            # Store discrepancies
            for discrepancy in report.discrepancies:
                discrepancy_model = DiscrepancyModel(
                    report_id=report_model.id,
                    type=discrepancy.type.value,
                    order_id=discrepancy.order_id,
                    symbol=discrepancy.symbol,
                    description=discrepancy.description,
                    ibkr_fill_json=discrepancy.ibkr_fill.to_dict() if discrepancy.ibkr_fill else None,
                    local_fill_json=discrepancy.local_fill.to_dict() if discrepancy.local_fill else None,
                )
                session.add(discrepancy_model)

            logger.info(
                f"Stored reconciliation report for {report.reconciliation_date} "
                f"with {len(report.discrepancies)} discrepancies"
            )
            return report_model.id

    def get_orders_by_date(self, target_date: date) -> List[OrderModel]:
        """
        Get all orders submitted on a specific date.

        Args:
            target_date: Date to query

        Returns:
            List of OrderModel objects
        """
        from datetime import timedelta

        with self.get_session() as session:
            start_time = datetime.combine(target_date, datetime.min.time())
            end_time = datetime.combine(target_date + timedelta(days=1), datetime.min.time())

            orders = (
                session.query(OrderModel)
                .filter(OrderModel.submission_time >= start_time, OrderModel.submission_time < end_time)
                .all()
            )

            # Detach from session
            session.expunge_all()
            return orders

    def get_orders_by_symbol(self, symbol: str, limit: int = 100) -> List[OrderModel]:
        """
        Get orders for a specific symbol.

        Args:
            symbol: Stock symbol
            limit: Maximum number of orders to return

        Returns:
            List of OrderModel objects
        """
        with self.get_session() as session:
            orders = (
                session.query(OrderModel)
                .filter_by(symbol=symbol)
                .order_by(OrderModel.submission_time.desc())
                .limit(limit)
                .all()
            )

            session.expunge_all()
            return orders

    def get_fills_by_date(self, target_date: date) -> List[FillModel]:
        """
        Get all fills on a specific date.

        Args:
            target_date: Date to query

        Returns:
            List of FillModel objects
        """
        from datetime import timedelta

        with self.get_session() as session:
            start_time = datetime.combine(target_date, datetime.min.time())
            end_time = datetime.combine(target_date + timedelta(days=1), datetime.min.time())

            fills = (
                session.query(FillModel).filter(FillModel.timestamp >= start_time, FillModel.timestamp < end_time).all()
            )

            session.expunge_all()
            return fills

    def get_fills_by_order(self, order_id: int) -> List[FillModel]:
        """
        Get all fills for a specific order.

        Args:
            order_id: Order ID

        Returns:
            List of FillModel objects
        """
        with self.get_session() as session:
            fills = session.query(FillModel).filter_by(order_id=order_id).all()

            session.expunge_all()
            return fills

    def get_reconciliation_reports(
        self, start_date: Optional[date] = None, end_date: Optional[date] = None
    ) -> List[ReconciliationReportModel]:
        """
        Get reconciliation reports for a date range.

        Args:
            start_date: Start date (inclusive), None for no lower bound
            end_date: End date (inclusive), None for no upper bound

        Returns:
            List of ReconciliationReportModel objects
        """
        with self.get_session() as session:
            query = session.query(ReconciliationReportModel)

            if start_date:
                query = query.filter(ReconciliationReportModel.reconciliation_date >= start_date)
            if end_date:
                query = query.filter(ReconciliationReportModel.reconciliation_date <= end_date)

            reports = query.order_by(ReconciliationReportModel.reconciliation_date.desc()).all()

            session.expunge_all()
            return reports

    def get_discrepancies_by_type(self, discrepancy_type: DiscrepancyType, limit: int = 100) -> List[DiscrepancyModel]:
        """
        Get discrepancies of a specific type.

        Args:
            discrepancy_type: Type of discrepancy
            limit: Maximum number to return

        Returns:
            List of DiscrepancyModel objects
        """
        with self.get_session() as session:
            discrepancies = session.query(DiscrepancyModel).filter_by(type=discrepancy_type.value).limit(limit).all()

            session.expunge_all()
            return discrepancies

    def get_order_by_id(self, order_id: int) -> Optional[OrderModel]:
        """
        Get a specific order by its order ID.

        Args:
            order_id: Order ID

        Returns:
            OrderModel or None if not found
        """
        with self.get_session() as session:
            order = session.query(OrderModel).filter_by(order_id=order_id).first()

            if order:
                session.expunge(order)
            return order

    def get_audit_trail(self, start_date: date, end_date: date) -> Dict[str, Any]:
        """
        Get complete audit trail for a date range.

        Returns all orders, fills, and reconciliation reports for the period.

        Args:
            start_date: Start date (inclusive)
            end_date: End date (inclusive)

        Returns:
            Dictionary with audit trail data
        """
        with self.get_session() as session:
            # Get orders
            orders = (
                session.query(OrderModel)
                .filter(
                    OrderModel.submission_time >= datetime.combine(start_date, datetime.min.time()),
                    OrderModel.submission_time <= datetime.combine(end_date, datetime.max.time()),
                )
                .all()
            )

            # Get fills
            fills = (
                session.query(FillModel)
                .filter(
                    FillModel.timestamp >= datetime.combine(start_date, datetime.min.time()),
                    FillModel.timestamp <= datetime.combine(end_date, datetime.max.time()),
                )
                .all()
            )

            # Get reconciliation reports
            reports = (
                session.query(ReconciliationReportModel)
                .filter(
                    ReconciliationReportModel.reconciliation_date >= start_date,
                    ReconciliationReportModel.reconciliation_date <= end_date,
                )
                .all()
            )

            # Get all discrepancies for these reports
            report_ids = [r.id for r in reports]
            discrepancies = (
                session.query(DiscrepancyModel).filter(DiscrepancyModel.report_id.in_(report_ids)).all()
                if report_ids
                else []
            )

            return {
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
                "orders": [o.to_dict() for o in orders],
                "fills": [f.to_dict() for f in fills],
                "reconciliation_reports": [r.to_dict() for r in reports],
                "discrepancies": [d.to_dict() for d in discrepancies],
            }

    def get_portfolio_snapshots(
        self, start_date: Optional[date] = None, end_date: Optional[date] = None, limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Get portfolio snapshots for a date range.

        Retrieves historical portfolio snapshots including NAV, drawdown,
        equity value, and position counts.

        Args:
            start_date: Start date (inclusive), None for no lower bound
            end_date: End date (inclusive), None for no upper bound
            limit: Maximum number of snapshots to return (default: 100)

        Returns:
            List of portfolio snapshot dictionaries with keys:
            - id, timestamp, snapshot_date, nav, cash, equity_value,
              num_positions, drawdown, daily_pnl, peak_nav

        Raises:
            RuntimeError: If portfolio snapshot models are not available
        """
        try:
            from copilot_quant.live.portfolio_state_manager import PortfolioSnapshotModel
        except ImportError:
            raise RuntimeError(
                "Portfolio snapshot models not available. "
                "Ensure copilot_quant.live.portfolio_state_manager is installed."
            )

        with self.get_session() as session:
            query = session.query(PortfolioSnapshotModel)

            if start_date:
                query = query.filter(PortfolioSnapshotModel.snapshot_date >= start_date)
            if end_date:
                query = query.filter(PortfolioSnapshotModel.snapshot_date <= end_date)

            snapshots = query.order_by(PortfolioSnapshotModel.timestamp.desc()).limit(limit).all()

            session.expunge_all()
            return [s.to_dict() for s in snapshots]

    def get_portfolio_snapshot_by_id(self, snapshot_id: int) -> Optional[Dict[str, Any]]:
        """
        Get a specific portfolio snapshot by its ID.

        Args:
            snapshot_id: Database ID of the snapshot

        Returns:
            Portfolio snapshot dictionary or None if not found

        Raises:
            RuntimeError: If portfolio snapshot models are not available
        """
        try:
            from copilot_quant.live.portfolio_state_manager import PortfolioSnapshotModel
        except ImportError:
            raise RuntimeError(
                "Portfolio snapshot models not available. "
                "Ensure copilot_quant.live.portfolio_state_manager is installed."
            )

        with self.get_session() as session:
            snapshot = session.query(PortfolioSnapshotModel).filter_by(id=snapshot_id).first()

            if snapshot:
                session.expunge(snapshot)
                return snapshot.to_dict()
            return None

    def get_equity_curve(
        self, start_date: Optional[date] = None, end_date: Optional[date] = None
    ) -> List[Dict[str, Any]]:
        """
        Get equity curve data for a date range.

        Retrieves time-series portfolio values for charting and analysis.

        Args:
            start_date: Start date (inclusive), None for no lower bound
            end_date: End date (inclusive), None for no upper bound

        Returns:
            List of dictionaries with timestamp, nav, drawdown, daily_pnl

        Raises:
            RuntimeError: If portfolio snapshot models are not available
        """
        try:
            from copilot_quant.live.portfolio_state_manager import PortfolioSnapshotModel
        except ImportError:
            raise RuntimeError(
                "Portfolio snapshot models not available. "
                "Ensure copilot_quant.live.portfolio_state_manager is installed."
            )

        with self.get_session() as session:
            query = session.query(PortfolioSnapshotModel)

            if start_date:
                query = query.filter(PortfolioSnapshotModel.snapshot_date >= start_date)
            if end_date:
                query = query.filter(PortfolioSnapshotModel.snapshot_date <= end_date)

            snapshots = query.order_by(PortfolioSnapshotModel.timestamp).all()

            session.expunge_all()
            return [
                {
                    "timestamp": s.timestamp.isoformat(),
                    "nav": s.nav,
                    "drawdown": s.drawdown,
                    "daily_pnl": s.daily_pnl,
                    "cash": s.cash,
                    "equity_value": s.equity_value,
                }
                for s in snapshots
            ]

    def get_position_snapshots(
        self, snapshot_id: Optional[int] = None, symbol: Optional[str] = None, limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Get position snapshots with optional filtering.

        Args:
            snapshot_id: Filter to a specific portfolio snapshot ID
            symbol: Filter to a specific symbol
            limit: Maximum number of position snapshots to return

        Returns:
            List of position snapshot dictionaries

        Raises:
            RuntimeError: If portfolio snapshot models are not available
        """
        try:
            from copilot_quant.live.portfolio_state_manager import PositionSnapshotModel
        except ImportError:
            raise RuntimeError(
                "Portfolio snapshot models not available. "
                "Ensure copilot_quant.live.portfolio_state_manager is installed."
            )

        with self.get_session() as session:
            query = session.query(PositionSnapshotModel)

            if snapshot_id:
                query = query.filter(PositionSnapshotModel.portfolio_snapshot_id == snapshot_id)
            if symbol:
                query = query.filter(PositionSnapshotModel.symbol == symbol)

            positions = query.limit(limit).all()

            session.expunge_all()
            return [p.to_dict() for p in positions]

    def get_latest_portfolio_snapshot(self) -> Optional[Dict[str, Any]]:
        """
        Get the most recent portfolio snapshot.

        Returns:
            Latest portfolio snapshot dictionary or None if no snapshots exist

        Raises:
            RuntimeError: If portfolio snapshot models are not available
        """
        try:
            from copilot_quant.live.portfolio_state_manager import PortfolioSnapshotModel
        except ImportError:
            raise RuntimeError(
                "Portfolio snapshot models not available. "
                "Ensure copilot_quant.live.portfolio_state_manager is installed."
            )

        with self.get_session() as session:
            snapshot = session.query(PortfolioSnapshotModel).order_by(PortfolioSnapshotModel.timestamp.desc()).first()

            if snapshot:
                session.expunge(snapshot)
                return snapshot.to_dict()
            return None
