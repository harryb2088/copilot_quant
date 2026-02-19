"""
Webhook Notifier Module

Sends notifications to a custom webhook endpoint.
"""

import logging
from typing import Dict, Optional

import requests

from copilot_quant.orchestrator.notifiers.base import AlertLevel, NotificationMessage, Notifier

logger = logging.getLogger(__name__)


class WebhookNotifier(Notifier):
    """
    Send notifications to a custom webhook endpoint.

    Sends JSON payload to the specified webhook URL.

    Example:
        >>> notifier = WebhookNotifier(
        ...     webhook_url="https://example.com/webhook/trading-alerts",
        ...     headers={"Authorization": "Bearer YOUR_TOKEN"}
        ... )
        >>> message = NotificationMessage(
        ...     title="Position Opened",
        ...     message="Opened long position in TSLA",
        ...     level=AlertLevel.INFO
        ... )
        >>> notifier.notify(message)
    """

    def __init__(
        self,
        webhook_url: str,
        headers: Optional[Dict[str, str]] = None,
        timeout: int = 10,
        enabled: bool = True,
        min_level: AlertLevel = AlertLevel.INFO,
    ):
        """
        Initialize webhook notifier.

        Args:
            webhook_url: Webhook endpoint URL
            headers: Optional HTTP headers (e.g., authentication)
            timeout: Request timeout in seconds
            enabled: Whether this notifier is enabled
            min_level: Minimum alert level to send
        """
        super().__init__(enabled=enabled, min_level=min_level)
        self.webhook_url = webhook_url
        self.headers = headers or {}
        self.timeout = timeout

        # Set default content type if not provided
        if "Content-Type" not in self.headers:
            self.headers["Content-Type"] = "application/json"

    def send(self, message: NotificationMessage) -> bool:
        """
        Send notification to webhook.

        Args:
            message: NotificationMessage to send

        Returns:
            True if sent successfully
        """
        # Build payload
        payload = message.to_dict()

        try:
            response = requests.post(self.webhook_url, json=payload, headers=self.headers, timeout=self.timeout)
            response.raise_for_status()

            logger.info(f"Webhook notification sent: {message.title}")
            return True

        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to send webhook notification: {e}")
            return False
