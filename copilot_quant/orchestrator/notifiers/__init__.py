"""
Notification & Alerting System

Provides multi-channel notifications for trading events with different severity levels.
"""

from copilot_quant.orchestrator.notifiers.base import (
    Notifier,
    AlertLevel,
    NotificationMessage,
)
from copilot_quant.orchestrator.notifiers.slack import SlackNotifier
from copilot_quant.orchestrator.notifiers.discord import DiscordNotifier
from copilot_quant.orchestrator.notifiers.email import EmailNotifier
from copilot_quant.orchestrator.notifiers.webhook import WebhookNotifier

__all__ = [
    'Notifier',
    'AlertLevel',
    'NotificationMessage',
    'SlackNotifier',
    'DiscordNotifier',
    'EmailNotifier',
    'WebhookNotifier',
]
