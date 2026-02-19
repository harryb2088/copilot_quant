"""
Base Notifier Module

Provides abstract base class for notification channels.
"""

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any, Dict

logger = logging.getLogger(__name__)


class AlertLevel(Enum):
    """Alert severity levels"""

    INFO = "info"  # Informational (signals, trades)
    WARNING = "warning"  # Warning (position limit breach, etc.)
    CRITICAL = "critical"  # Critical (risk breach, circuit breaker)


@dataclass
class NotificationMessage:
    """
    Notification message structure.

    Attributes:
        title: Message title/subject
        message: Main message content
        level: Alert severity level
        timestamp: When the alert was created
        metadata: Additional context (order details, position info, etc.)
    """

    title: str
    message: str
    level: AlertLevel = AlertLevel.INFO
    timestamp: datetime = None
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        """Initialize defaults"""
        if self.timestamp is None:
            self.timestamp = datetime.now()
        if self.metadata is None:
            self.metadata = {}

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "title": self.title,
            "message": self.message,
            "level": self.level.value,
            "timestamp": self.timestamp.isoformat(),
            "metadata": self.metadata,
        }


class Notifier(ABC):
    """
    Abstract base class for notification channels.

    All notifier implementations must inherit from this class and
    implement the send() method.

    Example:
        >>> class MyNotifier(Notifier):
        ...     def send(self, message: NotificationMessage) -> bool:
        ...         print(f"Sending: {message.title}")
        ...         return True
    """

    def __init__(self, enabled: bool = True, min_level: AlertLevel = AlertLevel.INFO):
        """
        Initialize notifier.

        Args:
            enabled: Whether this notifier is enabled
            min_level: Minimum alert level to send (filters out lower levels)
        """
        self.enabled = enabled
        self.min_level = min_level
        logger.info(f"{self.__class__.__name__} initialized (enabled={enabled}, min_level={min_level.value})")

    @abstractmethod
    def send(self, message: NotificationMessage) -> bool:
        """
        Send a notification message.

        Args:
            message: NotificationMessage to send

        Returns:
            True if sent successfully, False otherwise
        """
        pass

    def notify(self, message: NotificationMessage) -> bool:
        """
        Send notification with filtering.

        This method handles enabled/disabled state and level filtering.

        Args:
            message: NotificationMessage to send

        Returns:
            True if sent successfully, False if filtered or failed
        """
        if not self.enabled:
            logger.debug(f"{self.__class__.__name__} disabled, skipping notification")
            return False

        # Check level filtering
        level_order = {
            AlertLevel.INFO: 0,
            AlertLevel.WARNING: 1,
            AlertLevel.CRITICAL: 2,
        }

        if level_order[message.level] < level_order[self.min_level]:
            logger.debug(
                f"{self.__class__.__name__} filtered out {message.level.value} (min_level={self.min_level.value})"
            )
            return False

        try:
            return self.send(message)
        except Exception as e:
            logger.error(f"{self.__class__.__name__} failed to send notification: {e}")
            return False

    def _format_message(self, message: NotificationMessage) -> str:
        """
        Format message for display.

        Args:
            message: NotificationMessage to format

        Returns:
            Formatted message string
        """
        level_emoji = {
            AlertLevel.INFO: "ℹ️",
            AlertLevel.WARNING: "⚠️",
            AlertLevel.CRITICAL: "🚨",
        }

        emoji = level_emoji.get(message.level, "")
        timestamp_str = message.timestamp.strftime("%Y-%m-%d %H:%M:%S")

        formatted = f"{emoji} **{message.title}**\n\n"
        formatted += f"{message.message}\n\n"
        formatted += f"_Level: {message.level.value.upper()}_\n"
        formatted += f"_Time: {timestamp_str}_"

        if message.metadata:
            formatted += "\n\n**Details:**\n"
            for key, value in message.metadata.items():
                formatted += f"• {key}: {value}\n"

        return formatted
