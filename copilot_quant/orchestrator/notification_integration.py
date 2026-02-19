"""
Notification Integration Module

Provides integration between the orchestrator notification system and existing
trading components like OrderExecutionHandler.

This module provides callbacks that can be registered with existing components
to send notifications for trading events.
"""

import logging
from typing import List, Optional

from copilot_quant.brokers.order_execution_handler import OrderRecord, OrderStatus
from copilot_quant.orchestrator.notifiers.base import AlertLevel, NotificationMessage, Notifier

logger = logging.getLogger(__name__)


class OrderNotificationAdapter:
    """
    Adapter for sending notifications about order events.

    This class provides callbacks that can be registered with
    OrderExecutionHandler to automatically send notifications.

    Example:
        >>> from copilot_quant.orchestrator.notifiers import SlackNotifier
        >>>
        >>> # Setup notifiers
        >>> notifiers = [
        ...     SlackNotifier(webhook_url="https://hooks.slack.com/...")
        ... ]
        >>>
        >>> # Create adapter
        >>> adapter = OrderNotificationAdapter(notifiers)
        >>>
        >>> # Register with order handler
        >>> order_handler.register_fill_callback(adapter.on_order_filled)
        >>> order_handler.register_error_callback(adapter.on_order_error)
    """

    def __init__(
        self,
        notifiers: List[Notifier],
        notify_on_fills: bool = True,
        notify_on_partial_fills: bool = False,
        notify_on_errors: bool = True,
        notify_on_cancellations: bool = False,
    ):
        """
        Initialize order notification adapter.

        Args:
            notifiers: List of Notifier instances to send notifications to
            notify_on_fills: Send notifications on complete fills
            notify_on_partial_fills: Send notifications on partial fills
            notify_on_errors: Send notifications on errors
            notify_on_cancellations: Send notifications on cancellations
        """
        self.notifiers = notifiers
        self.notify_on_fills = notify_on_fills
        self.notify_on_partial_fills = notify_on_partial_fills
        self.notify_on_errors = notify_on_errors
        self.notify_on_cancellations = notify_on_cancellations

        logger.info(f"OrderNotificationAdapter initialized with {len(notifiers)} notifier(s)")

    def on_order_filled(self, order_record: OrderRecord) -> None:
        """
        Callback for order fill events.

        Args:
            order_record: OrderRecord with fill information
        """
        # Check if we should notify for this fill
        if order_record.status == OrderStatus.FILLED and not self.notify_on_fills:
            return

        if order_record.status == OrderStatus.PARTIALLY_FILLED and not self.notify_on_partial_fills:
            return

        # Determine alert level and title
        if order_record.status == OrderStatus.FILLED:
            level = AlertLevel.INFO
            title = "Order Filled"
        else:
            level = AlertLevel.INFO
            title = "Order Partially Filled"

        # Build message
        message = (
            f"{order_record.action} {order_record.filled_quantity} shares of "
            f"{order_record.symbol} at ${order_record.avg_fill_price:.2f}"
        )

        if order_record.status == OrderStatus.PARTIALLY_FILLED:
            message += f" ({order_record.remaining_quantity} remaining)"

        # Build metadata
        metadata = {
            "order_id": order_record.order_id,
            "symbol": order_record.symbol,
            "action": order_record.action,
            "filled_quantity": order_record.filled_quantity,
            "avg_price": f"${order_record.avg_fill_price:.2f}",
            "status": order_record.status.value,
        }

        if len(order_record.fills) > 0:
            total_commission = sum(f.commission for f in order_record.fills)
            if total_commission > 0:
                metadata["total_commission"] = f"${total_commission:.2f}"

        # Send notification
        notification = NotificationMessage(title=title, message=message, level=level, metadata=metadata)

        self._send_notification(notification)

    def on_order_error(self, order_record: OrderRecord, error_message: str) -> None:
        """
        Callback for order error events.

        Args:
            order_record: OrderRecord with error
            error_message: Error description
        """
        if not self.notify_on_errors:
            return

        # Build message
        message = (
            f"Error placing {order_record.action} order for {order_record.total_quantity} "
            f"shares of {order_record.symbol}: {error_message}"
        )

        # Build metadata
        metadata = {
            "order_id": order_record.order_id,
            "symbol": order_record.symbol,
            "action": order_record.action,
            "quantity": order_record.total_quantity,
            "error": error_message,
            "retry_count": order_record.retry_count,
        }

        # Send notification
        notification = NotificationMessage(
            title="Order Error", message=message, level=AlertLevel.WARNING, metadata=metadata
        )

        self._send_notification(notification)

    def on_order_status_changed(self, order_record: OrderRecord) -> None:
        """
        Callback for order status change events.

        Args:
            order_record: OrderRecord with updated status
        """
        # Only notify on cancellations if configured
        if order_record.status == OrderStatus.CANCELLED:
            if not self.notify_on_cancellations:
                return

            message = (
                f"{order_record.action} order for {order_record.total_quantity} "
                f"shares of {order_record.symbol} was cancelled"
            )

            if order_record.filled_quantity > 0:
                message += f" ({order_record.filled_quantity} shares were filled before cancellation)"

            metadata = {
                "order_id": order_record.order_id,
                "symbol": order_record.symbol,
                "action": order_record.action,
                "total_quantity": order_record.total_quantity,
                "filled_quantity": order_record.filled_quantity,
            }

            notification = NotificationMessage(
                title="Order Cancelled", message=message, level=AlertLevel.INFO, metadata=metadata
            )

            self._send_notification(notification)

    def _send_notification(self, notification: NotificationMessage) -> None:
        """
        Send notification to all configured notifiers.

        Args:
            notification: NotificationMessage to send
        """
        for notifier in self.notifiers:
            try:
                notifier.notify(notification)
            except Exception as e:
                logger.error(f"Failed to send notification via {notifier.__class__.__name__}: {e}", exc_info=True)


class RiskNotificationAdapter:
    """
    Adapter for sending notifications about risk events.

    Can be integrated with risk management systems to send
    alerts on risk breaches, circuit breaker activations, etc.

    Example:
        >>> adapter = RiskNotificationAdapter(notifiers)
        >>>
        >>> # Send circuit breaker alert
        >>> adapter.on_circuit_breaker_triggered(
        ...     reason="Portfolio drawdown exceeded 10%",
        ...     drawdown=0.12,
        ...     threshold=0.10
        ... )
    """

    def __init__(self, notifiers: List[Notifier]):
        """
        Initialize risk notification adapter.

        Args:
            notifiers: List of Notifier instances to send notifications to
        """
        self.notifiers = notifiers
        logger.info(f"RiskNotificationAdapter initialized with {len(notifiers)} notifier(s)")

    def on_circuit_breaker_triggered(
        self, reason: str, drawdown: Optional[float] = None, threshold: Optional[float] = None
    ) -> None:
        """
        Send notification when circuit breaker is triggered.

        Args:
            reason: Reason for circuit breaker activation
            drawdown: Current drawdown level (optional)
            threshold: Threshold that was exceeded (optional)
        """
        message = f"🚨 CIRCUIT BREAKER TRIGGERED: {reason}"

        metadata = {"reason": reason}
        if drawdown is not None:
            metadata["drawdown"] = f"{drawdown * 100:.2f}%"
        if threshold is not None:
            metadata["threshold"] = f"{threshold * 100:.2f}%"

        notification = NotificationMessage(
            title="Circuit Breaker Activated", message=message, level=AlertLevel.CRITICAL, metadata=metadata
        )

        self._send_notification(notification)

    def on_risk_limit_breach(
        self, limit_type: str, current_value: float, limit_value: float, symbol: Optional[str] = None
    ) -> None:
        """
        Send notification when a risk limit is breached.

        Args:
            limit_type: Type of limit breached (e.g., "position_size", "correlation")
            current_value: Current value that breached the limit
            limit_value: The limit that was breached
            symbol: Symbol related to the breach (optional)
        """
        if symbol:
            message = f"Risk limit breach for {symbol}: {limit_type}"
        else:
            message = f"Risk limit breach: {limit_type}"

        metadata = {
            "limit_type": limit_type,
            "current_value": current_value,
            "limit_value": limit_value,
        }

        if symbol:
            metadata["symbol"] = symbol

        notification = NotificationMessage(
            title="Risk Limit Breach", message=message, level=AlertLevel.WARNING, metadata=metadata
        )

        self._send_notification(notification)

    def on_portfolio_drawdown_warning(self, current_drawdown: float, threshold: float) -> None:
        """
        Send notification for portfolio drawdown warning.

        Args:
            current_drawdown: Current drawdown level
            threshold: Warning threshold
        """
        message = (
            f"Portfolio drawdown at {current_drawdown * 100:.2f}%, approaching threshold of {threshold * 100:.2f}%"
        )

        metadata = {
            "current_drawdown": f"{current_drawdown * 100:.2f}%",
            "threshold": f"{threshold * 100:.2f}%",
        }

        notification = NotificationMessage(
            title="Drawdown Warning", message=message, level=AlertLevel.WARNING, metadata=metadata
        )

        self._send_notification(notification)

    def _send_notification(self, notification: NotificationMessage) -> None:
        """
        Send notification to all configured notifiers.

        Args:
            notification: NotificationMessage to send
        """
        for notifier in self.notifiers:
            try:
                notifier.notify(notification)
            except Exception as e:
                logger.error(f"Failed to send notification via {notifier.__class__.__name__}: {e}", exc_info=True)
