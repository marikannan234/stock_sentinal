"""
Email service module for Stock Sentinel.

Provides email notification functionality for alert triggering.
Uses FastMail with async/await for non-blocking email delivery.
"""

import logging
from typing import Optional

from fastapi_mail import FastMail, MessageSchema, ConnectionConfig, MessageType
from fastapi_mail.models import NameEmail
from jinja2 import Template
from pydantic import SecretStr

from app.config import settings

logger = logging.getLogger(__name__)

# ============================================================================
# Email Configuration
# ============================================================================

# Initialize FastMail connection config
mail_config = ConnectionConfig(
    MAIL_SERVER=settings.MAIL_SERVER,
    MAIL_PORT=settings.MAIL_PORT,
    MAIL_USERNAME=settings.MAIL_USERNAME,
    MAIL_PASSWORD=SecretStr(settings.MAIL_PASSWORD),
    MAIL_FROM=settings.MAIL_FROM,
    MAIL_FROM_NAME=settings.MAIL_FROM_NAME,
    MAIL_STARTTLS=settings.MAIL_STARTTLS,
    MAIL_SSL_TLS=settings.MAIL_SSL_TLS,
)

# Initialize FastMail instance
fm = FastMail(mail_config)


# ============================================================================
# Email Templates
# ============================================================================

ALERT_TRIGGERED_HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <style>
        body {{
            font-family: Arial, sans-serif;
            background-color: #f5f5f5;
            color: #333;
        }}
        .container {{
            max-width: 600px;
            margin: 0 auto;
            background-color: #ffffff;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
        }}
        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 20px;
            border-radius: 8px;
            text-align: center;
            margin-bottom: 20px;
        }}
        .header h1 {{
            margin: 0;
            font-size: 28px;
        }}
        .alert-details {{
            background-color: #f9f9f9;
            border-left: 4px solid #667eea;
            padding: 15px;
            margin: 20px 0;
            border-radius: 4px;
        }}
        .detail-row {{
            display: flex;
            justify-content: space-between;
            padding: 10px 0;
            border-bottom: 1px solid #eee;
        }}
        .detail-row:last-child {{
            border-bottom: none;
        }}
        .label {{
            font-weight: bold;
            color: #667eea;
        }}
        .value {{
            color: #333;
        }}
        .price-highlight {{
            background-color: #fff3cd;
            padding: 2px 6px;
            border-radius: 3px;
            font-weight: bold;
        }}
        .condition {{
            background-color: #e3f2fd;
            padding: 2px 6px;
            border-radius: 3px;
            font-weight: bold;
            color: #1976d2;
        }}
        .timestamp {{
            color: #999;
            font-size: 12px;
            margin-top: 20px;
            padding-top: 15px;
            border-top: 1px solid #eee;
            text-align: center;
        }}
        .footer {{
            margin-top: 20px;
            padding-top: 15px;
            border-top: 1px solid #eee;
            font-size: 12px;
            color: #999;
            text-align: center;
        }}
        .button {{
            display: inline-block;
            background-color: #667eea;
            color: white;
            padding: 10px 20px;
            text-decoration: none;
            border-radius: 4px;
            margin-top: 15px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🔔 Alert Triggered!</h1>
            <p>Your Stock Sentinel alert has been activated</p>
        </div>
        
        <div class="alert-details">
            <div class="detail-row">
                <span class="label">Stock Symbol:</span>
                <span class="value">{symbol}</span>
            </div>
            <div class="detail-row">
                <span class="label">Current Price:</span>
                <span class="value"><span class="price-highlight">${current_price:.2f}</span></span>
            </div>
            <div class="detail-row">
                <span class="label">Alert Condition:</span>
                <span class="value"><span class="condition">{symbol} {condition} ${target_value:.2f}</span></span>
            </div>
            <div class="detail-row">
                <span class="label">Triggered At:</span>
                <span class="value">{triggered_at}</span>
            </div>
        </div>
        
        <p>Your price alert for <strong>{symbol}</strong> has been triggered. The current price of <strong>${current_price:.2f}</strong> matches your alert condition of <span class="condition">{condition} ${target_value:.2f}</span>.</p>
        
        <p>This alert is now inactive. You can create new alerts anytime in the Stock Sentinel dashboard.</p>
        
        <div style="text-align: center;">
            <a href="http://localhost:3000/dashboard" class="button">View Dashboard</a>
        </div>
        
        <div class="footer">
            <p>Stock Sentinel - Real-time Stock Market Monitoring</p>
            <p>This is an automated email. Please do not reply to this message.</p>
        </div>
    </div>
</body>
</html>
"""


# ============================================================================
# Email Functions
# ============================================================================

async def send_alert_triggered_email(
    to_email: str,
    symbol: str,
    current_price: float,
    condition: str,
    target_value: float,
    triggered_at: str,
) -> bool:
    """
    Send email notification when an alert is triggered.
    
    Args:
        to_email: Recipient email address
        symbol: Stock ticker symbol (e.g., "AAPL")
        current_price: Current stock price that triggered the alert
        condition: Alert condition (e.g., ">", "<", ">=", "<=")
        target_value: Target price value in the alert
        triggered_at: Timestamp when alert was triggered
    
    Returns:
        True if email was sent successfully, False otherwise
    """
    try:
        # Validate email
        if not to_email or "@" not in to_email:
            logger.warning(
                f"Invalid email address for alert notification",
                extra={"email": to_email},
            )
            return False
        
        # Prepare subject
        subject = f"🔔 Stock Alert Triggered: {symbol}"
        
        # Prepare HTML body
        html_body = ALERT_TRIGGERED_HTML_TEMPLATE.format(
            symbol=symbol,
            current_price=current_price,
            condition=condition,
            target_value=target_value,
            triggered_at=triggered_at,
        )
        
        # Prepare plain text body as fallback
        text_body = f"""
Stock Sentinel Alert Triggered!

Stock Symbol: {symbol}
Current Price: ${current_price:.2f}
Alert Condition: {symbol} {condition} ${target_value:.2f}
Triggered At: {triggered_at}

Your price alert for {symbol} has been triggered. 
The current price of ${current_price:.2f} matches your alert condition.

This alert is now inactive.

View your dashboard: http://localhost:3000/dashboard
        """.strip()
        
        # Create message with type cast for recipients
        # FastMail accepts email strings but type system expects NameEmail objects
        message = MessageSchema(
            subject=subject,
            recipients=[NameEmail(name=to_email.split('@')[0], email=to_email)],  # type: ignore
            body=html_body,
            subtype=MessageType.html,
        )
        
        # Send email
        await fm.send_message(message)
        
        logger.info(
            f"Alert notification email sent successfully",
            extra={
                "to_email": to_email,
                "symbol": symbol,
                "current_price": current_price,
            },
        )
        
        return True
        
    except Exception as e:
        logger.error(
            f"Failed to send alert notification email",
            extra={
                "to_email": to_email,
                "symbol": symbol,
                "error": str(e),
                "error_type": type(e).__name__,
            },
            exc_info=True,
        )
        return False


async def send_email(
    to_email: str,
    subject: str,
    body: str,
    html_body: Optional[str] = None,
) -> bool:
    """
    Send a generic email.
    
    Args:
        to_email: Recipient email address
        subject: Email subject
        body: Plain text email body
        html_body: Optional HTML body (if not provided, text will be used)
    
    Returns:
        True if email was sent successfully, False otherwise
    """
    try:
        # Validate email
        if not to_email or "@" not in to_email:
            logger.warning(
                f"Invalid email address",
                extra={"email": to_email},
            )
            return False
        
        # Create message with type cast for recipients
        message = MessageSchema(
            subject=subject,
            recipients=[NameEmail(name=to_email.split('@')[0], email=to_email)],  # type: ignore
            body=html_body if html_body else body,
            subtype=MessageType.html if html_body else MessageType.plain,
        )
        
        # Send email
        await fm.send_message(message)
        
        logger.info(
            f"Email sent successfully",
            extra={
                "to_email": to_email,
                "subject": subject,
            },
        )
        
        return True
        
    except Exception as e:
        logger.error(
            f"Failed to send email",
            extra={
                "to_email": to_email,
                "subject": subject,
                "error": str(e),
                "error_type": type(e).__name__,
            },
            exc_info=True,
        )
        return False


async def send_email_with_retry(
    to_email: str,
    subject: str,
    body: str,
    html_body: Optional[str] = None,
    retry_count: int = 3,
) -> bool:
    """
    Send email with automatic retry on failure.
    
    Args:
        to_email: Recipient email address
        subject: Email subject
        body: Plain text email body
        html_body: Optional HTML body
        retry_count: Number of retries on failure
    
    Returns:
        True if email was sent successfully, False after all retries failed
    """
    for attempt in range(retry_count):
        try:
            success = await send_email(to_email, subject, body, html_body)
            if success:
                return True
        except Exception as e:
            logger.warning(
                f"Email send attempt {attempt + 1}/{retry_count} failed",
                extra={
                    "to_email": to_email,
                    "attempt": attempt + 1,
                    "error": str(e),
                },
            )
        
        # Wait before retry (exponential backoff)
        if attempt < retry_count - 1:
            import asyncio
            await asyncio.sleep(2 ** attempt)
    
    logger.error(
        f"Failed to send email after {retry_count} attempts",
        extra={"to_email": to_email, "subject": subject},
    )
    return False
