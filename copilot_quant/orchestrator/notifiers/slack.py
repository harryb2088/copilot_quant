"""
Slack Notifier Module

Sends notifications to Slack via webhook.
"""

import logging
import requests
from typing import Optional

from copilot_quant.orchestrator.notifiers.base import Notifier, NotificationMessage, AlertLevel

logger = logging.getLogger(__name__)


class SlackNotifier(Notifier):
    """
    Send notifications to Slack via webhook.
    
    Example:
        >>> notifier = SlackNotifier(
        ...     webhook_url="https://hooks.slack.com/services/YOUR/WEBHOOK/URL",
        ...     channel="#trading-alerts"
        ... )
        >>> message = NotificationMessage(
        ...     title="Order Filled",
        ...     message="Bought 100 shares of AAPL at $150.00",
        ...     level=AlertLevel.INFO
        ... )
        >>> notifier.notify(message)
    """
    
    def __init__(
        self,
        webhook_url: str,
        channel: Optional[str] = None,
        username: str = "Trading Bot",
        enabled: bool = True,
        min_level: AlertLevel = AlertLevel.INFO
    ):
        """
        Initialize Slack notifier.
        
        Args:
            webhook_url: Slack webhook URL
            channel: Target channel (optional, can be set in webhook config)
            username: Bot username to display
            enabled: Whether this notifier is enabled
            min_level: Minimum alert level to send
        """
        super().__init__(enabled=enabled, min_level=min_level)
        self.webhook_url = webhook_url
        self.channel = channel
        self.username = username
    
    def send(self, message: NotificationMessage) -> bool:
        """
        Send notification to Slack.
        
        Args:
            message: NotificationMessage to send
            
        Returns:
            True if sent successfully
        """
        # Map alert levels to Slack colors
        color_map = {
            AlertLevel.INFO: "#36a64f",  # Green
            AlertLevel.WARNING: "#ff9900",  # Orange
            AlertLevel.CRITICAL: "#ff0000",  # Red
        }
        
        # Build Slack message payload
        payload = {
            "username": self.username,
            "attachments": [
                {
                    "color": color_map.get(message.level, "#808080"),
                    "title": message.title,
                    "text": message.message,
                    "footer": f"Alert Level: {message.level.value.upper()}",
                    "ts": int(message.timestamp.timestamp()),
                    "fields": [
                        {
                            "title": key,
                            "value": str(value),
                            "short": True
                        }
                        for key, value in (message.metadata or {}).items()
                    ]
                }
            ]
        }
        
        if self.channel:
            payload["channel"] = self.channel
        
        try:
            response = requests.post(
                self.webhook_url,
                json=payload,
                timeout=10
            )
            response.raise_for_status()
            
            logger.info(f"Slack notification sent: {message.title}")
            return True
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to send Slack notification: {e}")
            return False
