"""
Simple SMTP email service for Stock Sentinel alerts.

Provides synchronous email sending via SMTP (Gmail).
This is more reliable than async approaches when called from sync contexts like the scheduler.
"""

import logging
import html
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional

from app.config import settings

logger = logging.getLogger(__name__)


def mask_email(address: Optional[str]) -> str:
    """'jane.doe@example.com' -> 'ja***@example.com' (for logs)."""
    if not address or "@" not in address:
        return "<invalid>"
    local, _, domain = address.partition("@")
    return f"{local[:2]}***@{domain}"


def send_alert_email_smtp(
    to_email: str,
    subject: str,
    html_body: str,
    text_body: Optional[str] = None,
) -> bool:
    """
    Send email via SMTP (Gmail).
    
    This is a simple, synchronous implementation that works reliably
    when called from sync contexts like the scheduler.
    
    Args:
        to_email: Recipient email address
        subject: Email subject line
        html_body: HTML email body
        text_body: Plain text fallback body
    
    Returns:
        True if email sent successfully, False otherwise
    """
    try:
        # Validate email
        if not to_email or "@" not in to_email:
            logger.warning("Invalid recipient email address")
            return False
        
        # Check if email is disabled
        if not settings.ENABLE_EMAIL_NOTIFICATIONS:
            logger.debug("Email notifications disabled, skipping email")
            return False
        
        # Create message
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = settings.MAIL_FROM
        msg["To"] = to_email
        
        # Attach plain text and HTML parts
        if text_body:
            msg.attach(MIMEText(text_body, "plain"))
        msg.attach(MIMEText(html_body, "html"))
        
        # Send via SMTP
        smtp_client = smtplib.SMTP_SSL if settings.MAIL_SSL_TLS else smtplib.SMTP
        with smtp_client(settings.MAIL_SERVER, settings.MAIL_PORT, timeout=10) as server:
            # STARTTLS and implicit SSL are mutually exclusive SMTP modes.
            if settings.MAIL_STARTTLS and not settings.MAIL_SSL_TLS:
                server.starttls()

            server.login(settings.MAIL_USERNAME, settings.MAIL_PASSWORD)
            server.send_message(msg)
        
        logger.info(
            f"✅ Alert email sent successfully",
            extra={
                "to_email": mask_email(to_email),
                "subject": subject,
            },
        )
        return True
    
    except smtplib.SMTPException as e:
        logger.error(
            f"❌ SMTP error sending alert email: {e}",
            extra={
                "to_email": mask_email(to_email),
                "subject": subject,
                "smtp_error": str(e),
            },
            exc_info=True,
        )
        return False
    
    except Exception as e:
        logger.error(
            f"❌ Failed to send alert email: {e}",
            extra={
                "to_email": mask_email(to_email),
                "subject": subject,
                "error": str(e),
                "error_type": type(e).__name__,
            },
            exc_info=True,
        )
        return False


def _dashboard_url() -> str:
    """Resolve a real frontend URL for email links, preferring explicit config."""
    configured = getattr(settings, "FRONTEND_URL", None)
    if configured:
        return f"{configured.rstrip('/')}/dashboard"

    # Reuse a configured non-local CORS origin when FRONTEND_URL is not set.
    for origin in settings.BACKEND_CORS_ORIGINS:
        url = str(origin).rstrip("/")
        if "localhost" not in url and "127.0.0.1" not in url:
            return f"{url}/dashboard"

    return "http://localhost:3000/dashboard"


def send_alert_notification(
    user_email: str,
    symbol: str,
    current_price: float,
    condition: str,
    target_value: float,
    triggered_at: str,
    alert_type: str = "price",
    sma_value: Optional[float] = None,
    sma_period: Optional[int] = None,
    ema_value: Optional[float] = None,
    ema_period: Optional[int] = None,
    rsi_value: Optional[float] = None,
    rsi_period: Optional[int] = None,
    description: Optional[str] = None,
) -> bool:
    """
    Send alert notification email when a price alert triggers.
    
    Args:
        user_email: User's email address
        symbol: Stock symbol (e.g., "AAPL")
        current_price: Current stock price
        condition: Alert condition (">", "<", ">=", "<=")
        target_value: Target price in the alert
        triggered_at: ISO timestamp when alert triggered
        alert_type: Type of alert (price, sma_above, sma_below, etc.)
        sma_value: SMA value (optional)
        sma_period: SMA period (optional)
        ema_value: EMA value (optional)
        ema_period: EMA period (optional)
        rsi_value: RSI value (optional)
        rsi_period: RSI period (optional)
        description: Human-readable rule/outcome; used for alerts without a
            target price (indicator alerts)
    
    Returns:
        True if email sent successfully, False otherwise
    """
    if target_value is not None:
        rule = f"{symbol} {condition} ${target_value:.2f}"
    else:
        rule = description or f"{symbol} {alert_type} alert"
    rule_html = html.escape(rule)

    # Build subject and safely escaped values for HTML output.
    subject = f"🔔 Stock Alert Triggered: {symbol}"
    symbol_html = html.escape(symbol)
    triggered_at_html = html.escape(triggered_at)
    dashboard_url = html.escape(_dashboard_url(), quote=True)
    
    # Build HTML email body
    html_body = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <style>
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background-color: #f5f5f5;
            color: #333;
            margin: 0;
            padding: 0;
        }}
        .container {{
            max-width: 600px;
            margin: 20px auto;
            background-color: #ffffff;
            border-radius: 8px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
            overflow: hidden;
        }}
        .header {{
            background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%);
            color: white;
            padding: 30px 20px;
            text-align: center;
        }}
        .header h1 {{
            margin: 0;
            font-size: 28px;
            font-weight: 600;
        }}
        .content {{
            padding: 30px 20px;
        }}
        .alert-box {{
            background: linear-gradient(to right, #e3f2fd, #f3e5f5);
            border-left: 4px solid #2a5298;
            padding: 20px;
            margin: 20px 0;
            border-radius: 4px;
        }}
        .detail {{
            display: flex;
            justify-content: space-between;
            padding: 12px 0;
            border-bottom: 1px solid #eee;
            font-size: 14px;
        }}
        .detail:last-child {{
            border-bottom: none;
        }}
        .label {{
            font-weight: 600;
            color: #1e3c72;
        }}
        .value {{
            color: #666;
            font-weight: 500;
        }}
        .highlight {{
            background-color: #fff3cd;
            padding: 2px 6px;
            border-radius: 3px;
            font-weight: 600;
            color: #856404;
        }}
        .footer {{
            background-color: #f9f9f9;
            padding: 20px;
            text-align: center;
            font-size: 12px;
            color: #999;
            border-top: 1px solid #eee;
        }}
        .button {{
            display: inline-block;
            background-color: #2a5298;
            color: white;
            padding: 12px 24px;
            text-decoration: none;
            border-radius: 4px;
            margin-top: 15px;
            font-weight: 600;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🔔 Price Alert Triggered!</h1>
            <p style="margin: 10px 0 0 0; opacity: 0.9;">Your Stock Sentinel alert has been activated</p>
        </div>
        
        <div class="content">
            <p>Hello,</p>
            <p>Your price alert for <strong>{symbol_html}</strong> has been triggered!</p>
            
            <div class="alert-box">
                <div class="detail">
                    <span class="label">Stock Symbol:</span>
                    <span class="value"><strong>{symbol_html}</strong></span>
                </div>
                <div class="detail">
                    <span class="label">Current Price:</span>
                    <span class="value"><span class="highlight">${current_price:.2f}</span></span>
                </div>
                <div class="detail">
                    <span class="label">Alert Condition:</span>
                    <span class="value"><strong>{rule_html}</strong></span>
                </div>
                <div class="detail">
                    <span class="label">Triggered At:</span>
                    <span class="value">{triggered_at_html}</span>
                </div>
            </div>
            
            <p>The current price of <strong>${current_price:.2f}</strong> matches your alert condition: <strong>{rule_html}</strong>.</p>
            
            <p>This alert has been deactivated. You can view your portfolio and create new alerts anytime.</p>
            
            <div style="text-align: center;">
                <a href="{dashboard_url}" class="button">View Dashboard</a>
            </div>
        </div>
        
        <div class="footer">
            <p>Stock Sentinel - Real-Time Stock Market Monitoring</p>
            <p>This is an automated alert. Please do not reply to this email.</p>
        </div>
    </div>
</body>
</html>
"""
    
    # Build plain text version
    text_body = f"""
STOCK ALERT TRIGGERED

Symbol: {symbol}
Current Price: ${current_price:.2f}
Alert Condition: {rule}
Triggered At: {triggered_at}

Your price alert has been triggered.
View your dashboard: {_dashboard_url()}

Stock Sentinel - Real-Time Stock Market Monitoring
"""
    
    # Send email
    return send_alert_email_smtp(
        to_email=user_email,
        subject=subject,
        html_body=html_body,
        text_body=text_body,
    )
