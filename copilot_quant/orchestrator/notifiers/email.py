"""
Email Notifier Module

Sends notifications via SMTP email.
"""

import logging
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import List

from copilot_quant.orchestrator.notifiers.base import AlertLevel, NotificationMessage, Notifier

logger = logging.getLogger(__name__)


class EmailNotifier(Notifier):
    """
    Send notifications via SMTP email.

    Example:
        >>> notifier = EmailNotifier(
        ...     smtp_host="smtp.gmail.com",
        ...     smtp_port=587,
        ...     username="your-email@gmail.com",
        ...     password="your-app-password",
        ...     from_email="trading-bot@example.com",
        ...     to_emails=["trader@example.com"]
        ... )
        >>> message = NotificationMessage(
        ...     title="Daily Trading Summary",
        ...     message="Completed 5 trades today with 60% win rate",
        ...     level=AlertLevel.INFO
        ... )
        >>> notifier.notify(message)
    """

    def __init__(
        self,
        smtp_host: str,
        smtp_port: int,
        username: str,
        password: str,
        from_email: str,
        to_emails: List[str],
        use_tls: bool = True,
        enabled: bool = True,
        min_level: AlertLevel = AlertLevel.INFO,
    ):
        """
        Initialize email notifier.

        Args:
            smtp_host: SMTP server hostname
            smtp_port: SMTP server port
            username: SMTP username
            password: SMTP password
            from_email: From email address
            to_emails: List of recipient email addresses
            use_tls: Use TLS encryption
            enabled: Whether this notifier is enabled
            min_level: Minimum alert level to send
        """
        super().__init__(enabled=enabled, min_level=min_level)
        self.smtp_host = smtp_host
        self.smtp_port = smtp_port
        self.username = username
        self.password = password
        self.from_email = from_email
        self.to_emails = to_emails
        self.use_tls = use_tls

    def send(self, message: NotificationMessage) -> bool:
        """
        Send notification via email.

        Args:
            message: NotificationMessage to send

        Returns:
            True if sent successfully
        """
        # Create email message
        msg = MIMEMultipart("alternative")
        msg["Subject"] = f"[{message.level.value.upper()}] {message.title}"
        msg["From"] = self.from_email
        msg["To"] = ", ".join(self.to_emails)

        # Create HTML body
        html_body = self._create_html_body(message)

        # Create plain text alternative
        text_body = self._create_text_body(message)

        # Attach both versions
        msg.attach(MIMEText(text_body, "plain"))
        msg.attach(MIMEText(html_body, "html"))

        try:
            # Connect to SMTP server
            with smtplib.SMTP(self.smtp_host, self.smtp_port, timeout=30) as server:
                if self.use_tls:
                    server.starttls()

                # Login
                server.login(self.username, self.password)

                # Send email
                server.send_message(msg)

            logger.info(f"Email notification sent to {len(self.to_emails)} recipients: {message.title}")
            return True

        except Exception as e:
            logger.error(f"Failed to send email notification: {e}")
            return False

    def _create_text_body(self, message: NotificationMessage) -> str:
        """Create plain text email body"""
        body = f"{message.title}\n"
        body += "=" * len(message.title) + "\n\n"
        body += f"{message.message}\n\n"
        body += f"Alert Level: {message.level.value.upper()}\n"
        body += f"Time: {message.timestamp.strftime('%Y-%m-%d %H:%M:%S')}\n"

        if message.metadata:
            body += "\nDetails:\n"
            for key, value in message.metadata.items():
                body += f"  {key}: {value}\n"

        return body

    def _create_html_body(self, message: NotificationMessage) -> str:
        """Create HTML email body"""
        # Map alert levels to colors
        color_map = {
            AlertLevel.INFO: "#36a64f",
            AlertLevel.WARNING: "#ff9900",
            AlertLevel.CRITICAL: "#ff0000",
        }

        color = color_map.get(message.level, "#808080")

        html = f"""
        <html>
          <head>
            <style>
              body {{ font-family: Arial, sans-serif; }}
              .header {{
                background-color: {color};
                color: white;
                padding: 10px;
                border-radius: 5px;
              }}
              .content {{ padding: 20px; }}
              .metadata {{
                background-color: #f5f5f5;
                padding: 10px;
                border-radius: 5px;
                margin-top: 20px;
              }}
              .metadata-item {{ margin: 5px 0; }}
              .footer {{
                color: #666;
                font-size: 12px;
                margin-top: 20px;
                border-top: 1px solid #ddd;
                padding-top: 10px;
              }}
            </style>
          </head>
          <body>
            <div class="header">
              <h2>{message.title}</h2>
            </div>
            <div class="content">
              <p>{message.message}</p>

              <div class="footer">
                <p>
                  <strong>Alert Level:</strong> {message.level.value.upper()}<br>
                  <strong>Time:</strong> {message.timestamp.strftime("%Y-%m-%d %H:%M:%S")}
                </p>
              </div>
        """

        if message.metadata:
            html += '<div class="metadata"><h3>Details</h3>'
            for key, value in message.metadata.items():
                html += f'<div class="metadata-item"><strong>{key}:</strong> {value}</div>'
            html += "</div>"

        html += """
            </div>
          </body>
        </html>
        """

        return html
