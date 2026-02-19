"""
Tests for Notification System

Tests notifier base class and implementations.
"""

import unittest
from datetime import datetime
from unittest.mock import MagicMock, Mock, patch

from copilot_quant.orchestrator.notifiers.base import (
    AlertLevel,
    NotificationMessage,
    Notifier,
)
from copilot_quant.orchestrator.notifiers.discord import DiscordNotifier
from copilot_quant.orchestrator.notifiers.email import EmailNotifier
from copilot_quant.orchestrator.notifiers.slack import SlackNotifier
from copilot_quant.orchestrator.notifiers.webhook import WebhookNotifier


class TestNotificationMessage(unittest.TestCase):
    """Test NotificationMessage dataclass"""

    def test_message_creation(self):
        """Test creating a notification message"""
        msg = NotificationMessage(title="Test Alert", message="This is a test message", level=AlertLevel.WARNING)

        self.assertEqual(msg.title, "Test Alert")
        self.assertEqual(msg.message, "This is a test message")
        self.assertEqual(msg.level, AlertLevel.WARNING)
        self.assertIsInstance(msg.timestamp, datetime)
        self.assertEqual(msg.metadata, {})

    def test_message_with_metadata(self):
        """Test message with metadata"""
        metadata = {"symbol": "AAPL", "price": 150.00}
        msg = NotificationMessage(
            title="Trade Executed", message="Bought AAPL", level=AlertLevel.INFO, metadata=metadata
        )

        self.assertEqual(msg.metadata, metadata)

    def test_to_dict(self):
        """Test converting message to dictionary"""
        msg = NotificationMessage(title="Test", message="Message", level=AlertLevel.CRITICAL)

        data = msg.to_dict()
        self.assertEqual(data["title"], "Test")
        self.assertEqual(data["message"], "Message")
        self.assertEqual(data["level"], "critical")
        self.assertIn("timestamp", data)


class TestBaseNotifier(unittest.TestCase):
    """Test base Notifier class"""

    def test_level_filtering(self):
        """Test that notifier filters messages by level"""

        class TestNotifier(Notifier):
            def __init__(self):
                super().__init__(enabled=True, min_level=AlertLevel.WARNING)
                self.sent_messages = []

            def send(self, message):
                self.sent_messages.append(message)
                return True

        notifier = TestNotifier()

        # INFO message should be filtered out
        info_msg = NotificationMessage(title="Info", message="Info message", level=AlertLevel.INFO)
        notifier.notify(info_msg)
        self.assertEqual(len(notifier.sent_messages), 0)

        # WARNING message should pass
        warning_msg = NotificationMessage(title="Warning", message="Warning message", level=AlertLevel.WARNING)
        notifier.notify(warning_msg)
        self.assertEqual(len(notifier.sent_messages), 1)

        # CRITICAL message should pass
        critical_msg = NotificationMessage(title="Critical", message="Critical message", level=AlertLevel.CRITICAL)
        notifier.notify(critical_msg)
        self.assertEqual(len(notifier.sent_messages), 2)

    def test_disabled_notifier(self):
        """Test that disabled notifier doesn't send"""

        class TestNotifier(Notifier):
            def __init__(self):
                super().__init__(enabled=False)
                self.sent_count = 0

            def send(self, message):
                self.sent_count += 1
                return True

        notifier = TestNotifier()
        msg = NotificationMessage(title="Test", message="Test", level=AlertLevel.CRITICAL)

        result = notifier.notify(msg)
        self.assertFalse(result)
        self.assertEqual(notifier.sent_count, 0)


class TestSlackNotifier(unittest.TestCase):
    """Test Slack notifier"""

    @patch("copilot_quant.orchestrator.notifiers.slack.requests.post")
    def test_send_notification(self, mock_post):
        """Test sending Slack notification"""
        mock_response = Mock()
        mock_response.raise_for_status = Mock()
        mock_post.return_value = mock_response

        notifier = SlackNotifier(webhook_url="https://hooks.slack.com/test", channel="#test")

        msg = NotificationMessage(title="Test Alert", message="This is a test", level=AlertLevel.INFO)

        result = notifier.send(msg)

        self.assertTrue(result)
        mock_post.assert_called_once()

        # Check payload
        call_args = mock_post.call_args
        payload = call_args[1]["json"]
        self.assertIn("attachments", payload)
        self.assertEqual(payload["channel"], "#test")


class TestDiscordNotifier(unittest.TestCase):
    """Test Discord notifier"""

    @patch("copilot_quant.orchestrator.notifiers.discord.requests.post")
    def test_send_notification(self, mock_post):
        """Test sending Discord notification"""
        mock_response = Mock()
        mock_response.raise_for_status = Mock()
        mock_post.return_value = mock_response

        notifier = DiscordNotifier(webhook_url="https://discord.com/api/webhooks/test")

        msg = NotificationMessage(title="Test Alert", message="This is a test", level=AlertLevel.WARNING)

        result = notifier.send(msg)

        self.assertTrue(result)
        mock_post.assert_called_once()

        # Check payload
        call_args = mock_post.call_args
        payload = call_args[1]["json"]
        self.assertIn("embeds", payload)


class TestWebhookNotifier(unittest.TestCase):
    """Test Webhook notifier"""

    @patch("copilot_quant.orchestrator.notifiers.webhook.requests.post")
    def test_send_notification(self, mock_post):
        """Test sending webhook notification"""
        mock_response = Mock()
        mock_response.raise_for_status = Mock()
        mock_post.return_value = mock_response

        headers = {"Authorization": "Bearer test-token"}
        notifier = WebhookNotifier(webhook_url="https://example.com/webhook", headers=headers)

        msg = NotificationMessage(
            title="Test Alert", message="This is a test", level=AlertLevel.CRITICAL, metadata={"key": "value"}
        )

        result = notifier.send(msg)

        self.assertTrue(result)
        mock_post.assert_called_once()

        # Check that message was converted to dict
        call_args = mock_post.call_args
        payload = call_args[1]["json"]
        self.assertEqual(payload["title"], "Test Alert")
        self.assertEqual(payload["metadata"]["key"], "value")


class TestEmailNotifier(unittest.TestCase):
    """Test Email notifier"""

    @patch("copilot_quant.orchestrator.notifiers.email.smtplib.SMTP")
    def test_send_notification(self, mock_smtp_class):
        """Test sending email notification"""
        # Mock SMTP server
        mock_server = MagicMock()
        mock_smtp_class.return_value.__enter__.return_value = mock_server

        notifier = EmailNotifier(
            smtp_host="smtp.example.com",
            smtp_port=587,
            username="test@example.com",
            password="password",
            from_email="bot@example.com",
            to_emails=["user@example.com"],
        )

        msg = NotificationMessage(title="Test Alert", message="This is a test", level=AlertLevel.INFO)

        result = notifier.send(msg)

        self.assertTrue(result)
        mock_server.login.assert_called_once_with("test@example.com", "password")
        mock_server.send_message.assert_called_once()


if __name__ == "__main__":
    unittest.main()
