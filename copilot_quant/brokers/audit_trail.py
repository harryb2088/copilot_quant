"""
Audit Trail Module for Trade Logging and Compliance

Provides a unified interface for trade audit trail management, combining
order logging, database storage, and reconciliation reporting.

Features:
- Automatic capture of all order and fill events
- Database persistence for audit trail
- Reconciliation with IBKR account history
- Compliance reporting and export
- Query interface for analysis

Example:
    >>> from copilot_quant.brokers.audit_trail import AuditTrail
    >>> audit = AuditTrail(broker, database_url="sqlite:///audit.db")
    >>> audit.enable()  # Start automatic logging
    >>>
    >>> # Later, generate compliance report
    >>> report = audit.generate_compliance_report(start_date, end_date)
"""

import json
import logging
from datetime import date
from pathlib import Path
from typing import Any, Dict, List, Optional

from .order_execution_handler import OrderRecord
from .trade_database import TradeDatabase
from .trade_reconciliation import ReconciliationReport, TradeReconciliation

logger = logging.getLogger(__name__)


class AuditTrail:
    """
    Unified audit trail manager for trade logging and compliance.

    This class integrates order logging, database storage, and reconciliation
    to provide a complete audit trail for regulatory compliance and analysis.

    Example:
        >>> broker = IBKRBroker(paper_trading=True)
        >>> broker.connect()
        >>> audit = AuditTrail(broker)
        >>> audit.enable()
        >>>
        >>> # Execute trades...
        >>>
        >>> # Generate daily reconciliation
        >>> report = audit.reconcile_today()
        >>> if report.has_discrepancies():
        ...     print("Discrepancies found!")
    """

    def __init__(self, broker, database_url: str = "sqlite:///trade_audit.db", auto_reconcile: bool = False):
        """
        Initialize audit trail.

        Args:
            broker: IBKRBroker instance
            database_url: Database URL for audit trail storage
            auto_reconcile: If True, automatically reconcile at end of day
        """
        self.broker = broker
        self.database = TradeDatabase(database_url)
        self.reconciler = TradeReconciliation(broker)
        self.auto_reconcile = auto_reconcile
        self._enabled = False

        logger.info(f"AuditTrail initialized with database: {database_url}")

    def enable(self):
        """
        Enable automatic audit trail capture.

        Registers callbacks with the broker to automatically capture
        all order submissions and fills to the database.
        """
        if self._enabled:
            logger.warning("AuditTrail already enabled")
            return

        if not self.broker.order_handler:
            raise RuntimeError("Broker must have order_handler enabled for audit trail")

        # Register fill callback
        def on_fill(order_record: OrderRecord):
            """Callback when order is filled"""
            try:
                # Store/update order
                self.database.store_order(order_record)

                # Store the most recent fill
                if order_record.fills:
                    latest_fill = order_record.fills[-1]
                    self.database.store_fill(latest_fill, order_record.order_id)

                logger.debug(f"Captured fill for order {order_record.order_id} in audit trail")
            except Exception as e:
                logger.error(f"Error capturing fill in audit trail: {e}", exc_info=True)

        # Register status callback to capture order updates
        def on_status(order_record: OrderRecord):
            """Callback when order status changes"""
            try:
                self.database.store_order(order_record)
                logger.debug(f"Captured status update for order {order_record.order_id} in audit trail")
            except Exception as e:
                logger.error(f"Error capturing status in audit trail: {e}", exc_info=True)

        # Register callbacks
        self.broker.order_handler.register_fill_callback(on_fill)
        self.broker.order_handler.register_status_callback(on_status)

        self._enabled = True
        logger.info("AuditTrail enabled - automatic capture started")

    def disable(self):
        """Disable automatic audit trail capture."""
        # Note: We don't unregister callbacks as that would require storing references
        # In practice, callbacks will just become no-ops if audit trail is disabled
        self._enabled = False
        logger.info("AuditTrail disabled")

    def is_enabled(self) -> bool:
        """Check if audit trail is enabled"""
        return self._enabled

    def reconcile_today(self) -> ReconciliationReport:
        """
        Reconcile today's trades with IBKR.

        Returns:
            ReconciliationReport for today
        """
        report = self.reconciler.reconcile_today()

        # Store report in database
        self.database.store_reconciliation_report(report)

        return report

    def reconcile_date(self, target_date: date) -> ReconciliationReport:
        """
        Reconcile trades for a specific date.

        Args:
            target_date: Date to reconcile

        Returns:
            ReconciliationReport for the date
        """
        report = self.reconciler.reconcile(target_date)

        # Store report in database
        self.database.store_reconciliation_report(report)

        return report

    def reconcile_range(self, start_date: date, end_date: date) -> List[ReconciliationReport]:
        """
        Reconcile trades for a date range.

        Args:
            start_date: Start date (inclusive)
            end_date: End date (inclusive)

        Returns:
            List of ReconciliationReport objects
        """
        reports = self.reconciler.reconcile_date_range(start_date, end_date)

        # Store all reports
        for report in reports:
            self.database.store_reconciliation_report(report)

        return reports

    def get_orders_by_date(self, target_date: date) -> List[Dict[str, Any]]:
        """
        Get all orders for a specific date.

        Args:
            target_date: Date to query

        Returns:
            List of order dictionaries
        """
        orders = self.database.get_orders_by_date(target_date)
        return [order.to_dict() for order in orders]

    def get_fills_by_date(self, target_date: date) -> List[Dict[str, Any]]:
        """
        Get all fills for a specific date.

        Args:
            target_date: Date to query

        Returns:
            List of fill dictionaries
        """
        fills = self.database.get_fills_by_date(target_date)
        return [fill.to_dict() for fill in fills]

    def get_order_history(self, order_id: int) -> Dict[str, Any]:
        """
        Get complete history for a specific order.

        Args:
            order_id: Order ID

        Returns:
            Dictionary with order details and all fills
        """
        order = self.database.get_order_by_id(order_id)
        if not order:
            return {"error": f"Order {order_id} not found"}

        fills = self.database.get_fills_by_order(order_id)

        return {"order": order.to_dict(), "fills": [fill.to_dict() for fill in fills], "fill_count": len(fills)}

    def generate_compliance_report(self, start_date: date, end_date: date, output_format: str = "json") -> str:
        """
        Generate compliance report for a date range.

        Args:
            start_date: Start date (inclusive)
            end_date: End date (inclusive)
            output_format: Output format ('json' or 'text')

        Returns:
            Formatted compliance report
        """
        audit_data = self.database.get_audit_trail(start_date, end_date)

        if output_format == "json":
            return json.dumps(audit_data, indent=2)
        elif output_format == "text":
            return self._format_text_report(audit_data)
        else:
            raise ValueError(f"Unsupported format: {output_format}")

    def _format_text_report(self, audit_data: Dict[str, Any]) -> str:
        """Format audit data as human-readable text"""
        lines = []
        lines.append("=" * 80)
        lines.append("TRADE AUDIT REPORT")
        lines.append("=" * 80)
        lines.append(f"Period: {audit_data['start_date']} to {audit_data['end_date']}")
        lines.append("")

        # Summary statistics
        lines.append("SUMMARY")
        lines.append("-" * 80)
        lines.append(f"Total Orders: {len(audit_data['orders'])}")
        lines.append(f"Total Fills: {len(audit_data['fills'])}")
        lines.append(f"Reconciliation Reports: {len(audit_data['reconciliation_reports'])}")
        lines.append(f"Total Discrepancies: {len(audit_data['discrepancies'])}")
        lines.append("")

        # Orders
        if audit_data["orders"]:
            lines.append("ORDERS")
            lines.append("-" * 80)
            for order in audit_data["orders"]:
                lines.append(
                    f"Order {order['order_id']}: {order['action']} {order['total_quantity']} "
                    f"{order['symbol']} @ {order['order_type']} - Status: {order['status']}"
                )
                if order.get("avg_fill_price"):
                    lines.append(f"  Filled: {order['filled_quantity']} @ ${order['avg_fill_price']:.2f}")
                lines.append(f"  Submitted: {order['submission_time']}")
            lines.append("")

        # Fills
        if audit_data["fills"]:
            lines.append("FILLS")
            lines.append("-" * 80)
            for fill in audit_data["fills"]:
                lines.append(
                    f"Fill {fill['fill_id']}: Order {fill['order_id']} - "
                    f"{fill['quantity']} {fill['symbol']} @ ${fill['price']:.2f}"
                )
                lines.append(f"  Commission: ${fill['commission']:.2f}, Time: {fill['timestamp']}")
            lines.append("")

        # Discrepancies
        if audit_data["discrepancies"]:
            lines.append("DISCREPANCIES")
            lines.append("-" * 80)
            for disc in audit_data["discrepancies"]:
                lines.append(f"Order {disc['order_id']} ({disc['symbol']}) - {disc['type']}")
                lines.append(f"  {disc['description']}")
            lines.append("")

        lines.append("=" * 80)
        lines.append("END OF REPORT")
        lines.append("=" * 80)

        return "\n".join(lines)

    def export_audit_trail(self, start_date: date, end_date: date, output_file: str):
        """
        Export audit trail to file.

        Args:
            start_date: Start date (inclusive)
            end_date: End date (inclusive)
            output_file: Path to output file (format determined by extension)
        """
        output_path = Path(output_file)

        # Determine format from extension
        if output_path.suffix.lower() == ".json":
            output_format = "json"
        elif output_path.suffix.lower() == ".txt":
            output_format = "text"
        else:
            raise ValueError(f"Unsupported file extension: {output_path.suffix}")

        # Generate report
        report = self.generate_compliance_report(start_date, end_date, output_format=output_format)

        # Write to file
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w") as f:
            f.write(report)

        logger.info(f"Exported audit trail to {output_file}")

    def get_reconciliation_summary(
        self, start_date: Optional[date] = None, end_date: Optional[date] = None
    ) -> Dict[str, Any]:
        """
        Get summary of reconciliation reports.

        Args:
            start_date: Start date (None for all)
            end_date: End date (None for all)

        Returns:
            Summary dictionary with statistics
        """
        reports = self.database.get_reconciliation_reports(start_date, end_date)

        total_discrepancies = sum(r.total_discrepancies for r in reports)
        total_matched = sum(r.matched_orders for r in reports)

        return {
            "total_reports": len(reports),
            "total_discrepancies": total_discrepancies,
            "total_matched_orders": total_matched,
            "reports": [r.to_dict() for r in reports],
        }

    def check_compliance(self, start_date: date, end_date: date, max_discrepancies: int = 0) -> Dict[str, Any]:
        """
        Check compliance status for a date range.

        Args:
            start_date: Start date (inclusive)
            end_date: End date (inclusive)
            max_discrepancies: Maximum allowed discrepancies (default: 0)

        Returns:
            Dictionary with compliance status and details
        """
        reports = self.database.get_reconciliation_reports(start_date, end_date)

        total_discrepancies = sum(r.total_discrepancies for r in reports)
        compliant = total_discrepancies <= max_discrepancies

        return {
            "compliant": compliant,
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "total_discrepancies": total_discrepancies,
            "max_allowed": max_discrepancies,
            "reports_checked": len(reports),
            "details": [r.to_dict() for r in reports if r.total_discrepancies > 0],
        }
