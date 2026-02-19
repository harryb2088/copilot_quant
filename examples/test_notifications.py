"""
Example: Setting up Notifications

This script demonstrates how to configure and test different notification channels.
"""

import logging
import os
from datetime import datetime

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


def test_slack_notifications():
    """Test Slack notifications"""
    from copilot_quant.orchestrator.notifiers import SlackNotifier, NotificationMessage, AlertLevel
    
    # Get webhook URL from environment variable (for security)
    webhook_url = os.getenv('SLACK_WEBHOOK_URL')
    
    if not webhook_url:
        logger.warning("SLACK_WEBHOOK_URL not set, skipping Slack test")
        return
    
    # Create notifier
    notifier = SlackNotifier(
        webhook_url=webhook_url,
        channel="#trading-alerts",  # Optional
        min_level=AlertLevel.INFO
    )
    
    # Send test message
    message = NotificationMessage(
        title="Test: Trading Alert",
        message="This is a test notification from the trading orchestrator",
        level=AlertLevel.INFO,
        metadata={
            'test': 'true',
            'timestamp': datetime.now().isoformat(),
            'environment': 'development'
        }
    )
    
    success = notifier.notify(message)
    if success:
        logger.info("✓ Slack notification sent successfully")
    else:
        logger.error("✗ Slack notification failed")


def test_discord_notifications():
    """Test Discord notifications"""
    from copilot_quant.orchestrator.notifiers import DiscordNotifier, NotificationMessage, AlertLevel
    
    webhook_url = os.getenv('DISCORD_WEBHOOK_URL')
    
    if not webhook_url:
        logger.warning("DISCORD_WEBHOOK_URL not set, skipping Discord test")
        return
    
    notifier = DiscordNotifier(
        webhook_url=webhook_url,
        min_level=AlertLevel.INFO
    )
    
    message = NotificationMessage(
        title="Test: Order Filled",
        message="Bought 100 shares of AAPL at $150.00",
        level=AlertLevel.INFO,
        metadata={
            'symbol': 'AAPL',
            'quantity': 100,
            'price': '$150.00',
            'action': 'BUY'
        }
    )
    
    success = notifier.notify(message)
    if success:
        logger.info("✓ Discord notification sent successfully")
    else:
        logger.error("✗ Discord notification failed")


def test_email_notifications():
    """Test email notifications"""
    from copilot_quant.orchestrator.notifiers import EmailNotifier, NotificationMessage, AlertLevel
    
    # Get credentials from environment
    smtp_host = os.getenv('SMTP_HOST', 'smtp.gmail.com')
    smtp_port = int(os.getenv('SMTP_PORT', '587'))
    smtp_user = os.getenv('SMTP_USERNAME')
    smtp_pass = os.getenv('SMTP_PASSWORD')
    email_to = os.getenv('EMAIL_TO')
    
    if not all([smtp_user, smtp_pass, email_to]):
        logger.warning("Email credentials not set, skipping email test")
        logger.info("Set SMTP_USERNAME, SMTP_PASSWORD, and EMAIL_TO environment variables")
        return
    
    notifier = EmailNotifier(
        smtp_host=smtp_host,
        smtp_port=smtp_port,
        username=smtp_user,
        password=smtp_pass,
        from_email=smtp_user,
        to_emails=[email_to],
        min_level=AlertLevel.WARNING
    )
    
    message = NotificationMessage(
        title="Test: Circuit Breaker Alert",
        message="Portfolio drawdown exceeded threshold - circuit breaker triggered",
        level=AlertLevel.CRITICAL,
        metadata={
            'drawdown': '12.5%',
            'threshold': '10.0%',
            'action': 'All positions liquidated'
        }
    )
    
    success = notifier.notify(message)
    if success:
        logger.info("✓ Email notification sent successfully")
    else:
        logger.error("✗ Email notification failed")


def test_webhook_notifications():
    """Test webhook notifications"""
    from copilot_quant.orchestrator.notifiers import WebhookNotifier, NotificationMessage, AlertLevel
    
    webhook_url = os.getenv('WEBHOOK_URL')
    
    if not webhook_url:
        logger.warning("WEBHOOK_URL not set, skipping webhook test")
        return
    
    # Optional: Add authorization header
    headers = {}
    auth_token = os.getenv('WEBHOOK_AUTH_TOKEN')
    if auth_token:
        headers['Authorization'] = f'Bearer {auth_token}'
    
    notifier = WebhookNotifier(
        webhook_url=webhook_url,
        headers=headers,
        min_level=AlertLevel.INFO
    )
    
    message = NotificationMessage(
        title="Test: Risk Limit Breach",
        message="Position size for TSLA exceeded maximum limit",
        level=AlertLevel.WARNING,
        metadata={
            'symbol': 'TSLA',
            'position_size': '12%',
            'max_limit': '10%'
        }
    )
    
    success = notifier.notify(message)
    if success:
        logger.info("✓ Webhook notification sent successfully")
    else:
        logger.error("✗ Webhook notification failed")


def test_order_notifications():
    """Test order notification adapter"""
    from copilot_quant.orchestrator.notifiers import SlackNotifier, AlertLevel
    from copilot_quant.orchestrator.notification_integration import OrderNotificationAdapter
    from copilot_quant.brokers.order_execution_handler import OrderRecord, OrderStatus, Fill
    from datetime import datetime
    
    webhook_url = os.getenv('SLACK_WEBHOOK_URL')
    if not webhook_url:
        logger.warning("SLACK_WEBHOOK_URL not set, skipping order notification test")
        return
    
    # Setup notifier
    notifier = SlackNotifier(webhook_url=webhook_url, min_level=AlertLevel.INFO)
    
    # Create adapter
    adapter = OrderNotificationAdapter(
        notifiers=[notifier],
        notify_on_fills=True,
        notify_on_errors=True
    )
    
    # Simulate a filled order
    order = OrderRecord(
        order_id=12345,
        symbol="AAPL",
        action="BUY",
        total_quantity=100,
        order_type="MARKET"
    )
    
    # Add a fill
    fill = Fill(
        fill_id="test-fill-1",
        order_id=12345,
        symbol="AAPL",
        quantity=100,
        price=150.50,
        timestamp=datetime.now(),
        commission=1.0
    )
    
    order.add_fill(fill)
    
    # Send notification
    adapter.on_order_filled(order)
    logger.info("✓ Order fill notification sent")


def main():
    """Run all notification tests"""
    logger.info("=" * 60)
    logger.info("Testing Notification Channels")
    logger.info("=" * 60)
    logger.info("Set environment variables for credentials:")
    logger.info("  SLACK_WEBHOOK_URL")
    logger.info("  DISCORD_WEBHOOK_URL")
    logger.info("  SMTP_USERNAME, SMTP_PASSWORD, EMAIL_TO")
    logger.info("  WEBHOOK_URL, WEBHOOK_AUTH_TOKEN (optional)")
    logger.info("=" * 60)
    
    # Run tests
    test_slack_notifications()
    test_discord_notifications()
    test_email_notifications()
    test_webhook_notifications()
    test_order_notifications()
    
    logger.info("=" * 60)
    logger.info("Notification tests complete")
    logger.info("=" * 60)


if __name__ == "__main__":
    main()
