"""
Discord Notifier Module

Sends notifications to Discord via webhook.
"""

import logging

import requests

from copilot_quant.orchestrator.notifiers.base import AlertLevel, NotificationMessage, Notifier

logger = logging.getLogger(__name__)


class DiscordNotifier(Notifier):
    """
    Send notifications to Discord via webhook.

    Example:
        >>> notifier = DiscordNotifier(
        ...     webhook_url="https://discord.com/api/webhooks/YOUR/WEBHOOK"
        ... )
        >>> message = NotificationMessage(
        ...     title="Circuit Breaker Triggered",
        ...     message="Portfolio drawdown exceeded threshold",
        ...     level=AlertLevel.CRITICAL
        ... )
        >>> notifier.notify(message)
    """

    def __init__(
        self,
        webhook_url: str,
        username: str = "Trading Bot",
        enabled: bool = True,
        min_level: AlertLevel = AlertLevel.INFO,
    ):
        """
        Initialize Discord notifier.

        Args:
            webhook_url: Discord webhook URL
            username: Bot username to display
            enabled: Whether this notifier is enabled
            min_level: Minimum alert level to send
        """
        super().__init__(enabled=enabled, min_level=min_level)
        self.webhook_url = webhook_url
        self.username = username

    def send(self, message: NotificationMessage) -> bool:
        """
        Send notification to Discord.

        Args:
            message: NotificationMessage to send

        Returns:
            True if sent successfully
        """
        # Map alert levels to Discord colors (decimal RGB)
        color_map = {
            AlertLevel.INFO: 3581519,  # Green (#36a64f)
            AlertLevel.WARNING: 16750080,  # Orange (#ff9900)
            AlertLevel.CRITICAL: 16711680,  # Red (#ff0000)
        }

        # Build embed fields from metadata
        fields = []
        if message.metadata:
            for key, value in message.metadata.items():
                fields.append({"name": key, "value": str(value), "inline": True})

        # Build Discord webhook payload
        payload = {
            "username": self.username,
            "embeds": [
                {
                    "title": message.title,
                    "description": message.message,
                    "color": color_map.get(message.level, 8421504),  # Gray default
                    "timestamp": message.timestamp.isoformat(),
                    "footer": {"text": f"Alert Level: {message.level.value.upper()}"},
                    "fields": fields,
                }
            ],
        }

        try:
            response = requests.post(self.webhook_url, json=payload, timeout=10)
            response.raise_for_status()

            logger.info(f"Discord notification sent: {message.title}")
            return True

        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to send Discord notification: {e}")
            return False
