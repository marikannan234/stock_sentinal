"""
Email service module for Stock Sentinel.

Provides email notification functionality for alert triggering.
Uses FastMail with async/await for non-blocking email delivery.
"""

import logging
from typing import Optional, cast, List

from fastapi_mail import FastMail, MessageSchema, ConnectionConfig, MessageType
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
    alert_type: str = "price",
    sma_value: Optional[float] = None,
    sma_period: Optional[int] = None,
    ema_value: Optional[float] = None,
    ema_period: Optional[int] = None,
    rsi_value: Optional[float] = None,
    rsi_period: Optional[int] = None,
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
        alert_type: Type of alert (price, sma_above, sma_below, sma_crossover, ema_above, ema_below, ema_crossover, rsi_overbought, rsi_oversold, rsi_crossover, strong_buy_signal, strong_sell_signal, etc.)
        sma_value: SMA value (for SMA-based alerts and combined signals)
        sma_period: SMA period (for SMA-based alerts and combined signals)
        ema_value: EMA value (for EMA-based alerts and combined signals)
        ema_period: EMA period (for EMA-based alerts and combined signals)
        rsi_value: RSI value (for RSI-based alerts and combined signals)
        rsi_period: RSI period (for RSI-based alerts and combined signals)
    
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
        
        # Prepare HTML body based on alert type
        if alert_type in ["sma_above", "sma_below", "sma_crossover"] and sma_value is not None and sma_period is not None:
            # SMA alert
            if alert_type == "sma_above":
                condition_text = f"Price ({current_price:.2f}) is ABOVE {sma_period}-day SMA ({sma_value:.2f})"
            elif alert_type == "sma_below":
                condition_text = f"Price ({current_price:.2f}) is BELOW {sma_period}-day SMA ({sma_value:.2f})"
            else:  # sma_crossover
                direction = "above" if current_price > sma_value else "below"
                condition_text = f"Price CROSSED {direction} {sma_period}-day SMA. Current: {current_price:.2f}, SMA: {sma_value:.2f}"
            
            html_body = f"""
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
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>📈 SMA Alert Triggered!</h1>
        </div>
        <div class="alert-details">
            <div class="detail-row">
                <span class="label">Stock Symbol:</span>
                <span class="value">{symbol}</span>
            </div>
            <div class="detail-row">
                <span class="label">Alert Type:</span>
                <span class="value">{alert_type.replace('_', ' ').title()}</span>
            </div>
            <div class="detail-row">
                <span class="label">Condition:</span>
                <span class="value">{condition_text}</span>
            </div>
            <div class="detail-row">
                <span class="label">Current Price:</span>
                <span class="value">${current_price:.2f}</span>
            </div>
            <div class="detail-row">
                <span class="label">SMA ({sma_period}-day):</span>
                <span class="value">${sma_value:.2f}</span>
            </div>
            <div class="detail-row">
                <span class="label">Triggered At:</span>
                <span class="value">{triggered_at}</span>
            </div>
        </div>
        <p>Your SMA alert for {symbol} has been triggered.</p>
        <p><a href="http://localhost:3000/dashboard">View your dashboard</a></p>
    </div>
</body>
</html>
            """
            
            text_body = f"""
Stock Sentinel SMA Alert Triggered!

Stock Symbol: {symbol}
Alert Type: {alert_type.replace('_', ' ').title()}
Condition: {condition_text}
Current Price: ${current_price:.2f}
SMA ({sma_period}-day): ${sma_value:.2f}
Triggered At: {triggered_at}

Your SMA alert for {symbol} has been triggered.

View your dashboard: http://localhost:3000/dashboard
            """.strip()
        
        elif alert_type in ["rsi_overbought", "rsi_oversold", "rsi_crossover"] and rsi_value is not None and rsi_period is not None:
            # RSI alert
            if alert_type == "rsi_overbought":
                condition_text = f"RSI ({rsi_value:.1f}) is OVERBOUGHT (>70) - Potential sell signal"
            elif alert_type == "rsi_oversold":
                condition_text = f"RSI ({rsi_value:.1f}) is OVERSOLD (<30) - Potential buy signal"
            else:  # rsi_crossover
                if rsi_value > 50:
                    direction = "exited oversold zone"
                else:
                    direction = "exited overbought zone"
                condition_text = f"RSI CROSSOVER - {direction}. Current RSI: {rsi_value:.1f}"
            
            html_body = f"""
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
            background: linear-gradient(135deg, #ff6b6b 0%, #ee5a6f 100%);
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
            border-left: 4px solid #ff6b6b;
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
            color: #ff6b6b;
        }}
        .value {{
            color: #333;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>📊 RSI Alert Triggered!</h1>
        </div>
        <div class="alert-details">
            <div class="detail-row">
                <span class="label">Stock Symbol:</span>
                <span class="value">{symbol}</span>
            </div>
            <div class="detail-row">
                <span class="label">Alert Type:</span>
                <span class="value">{alert_type.replace('_', ' ').title()}</span>
            </div>
            <div class="detail-row">
                <span class="label">Condition:</span>
                <span class="value">{condition_text}</span>
            </div>
            <div class="detail-row">
                <span class="label">Current Price:</span>
                <span class="value">${current_price:.2f}</span>
            </div>
            <div class="detail-row">
                <span class="label">RSI ({rsi_period}):</span>
                <span class="value">{rsi_value:.1f}</span>
            </div>
            <div class="detail-row">
                <span class="label">Triggered At:</span>
                <span class="value">{triggered_at}</span>
            </div>
        </div>
        <p>Your RSI alert for {symbol} has been triggered.</p>
        <p><a href="http://localhost:3000/dashboard">View your dashboard</a></p>
    </div>
</body>
</html>
            """
            
            text_body = f"""
Stock Sentinel RSI Alert Triggered!

Stock Symbol: {symbol}
Alert Type: {alert_type.replace('_', ' ').title()}
Condition: {condition_text}
Current Price: ${current_price:.2f}
RSI ({rsi_period}): {rsi_value:.1f}
Triggered At: {triggered_at}

Your RSI alert for {symbol} has been triggered.

View your dashboard: http://localhost:3000/dashboard
            """.strip()
        
        elif alert_type in ["strong_buy_signal", "strong_sell_signal"] and sma_value is not None and ema_value is not None and rsi_value is not None:
            # Combined signal alert
            signal_name = "🚀 STRONG BUY" if alert_type == "strong_buy_signal" else "📉 STRONG SELL"
            signal_emoji = "🚀" if alert_type == "strong_buy_signal" else "📉"
            gradient_start = "#27ae60" if alert_type == "strong_buy_signal" else "#e74c3c"
            gradient_end = "#2ecc71" if alert_type == "strong_buy_signal" else "#c0392b"
            
            condition_analysis = f"""
            <div class="analysis-box">
                <h3>📊 Signal Analysis</h3>
                <div class="analysis-item">
                    <span class="analysis-label">Price vs SMA:</span>
                    <span class="analysis-value">
                        ${current_price:.2f} {'>' if alert_type == "strong_buy_signal" else '<'} ${sma_value:.2f}
                    </span>
                </div>
                <div class="analysis-item">
                    <span class="analysis-label">Price vs EMA:</span>
                    <span class="analysis-value">
                        ${current_price:.2f} {'>' if alert_type == "strong_buy_signal" else '<'} ${ema_value:.2f}
                    </span>
                </div>
                <div class="analysis-item">
                    <span class="analysis-label">RSI({rsi_period}):</span>
                    <span class="analysis-value">{rsi_value:.1f} {'< 30 (Oversold)' if alert_type == 'strong_buy_signal' else '> 70 (Overbought)'}</span>
                </div>
                <div class="analysis-note">
                    ✓ All three conditions met for strongest signal
                </div>
            </div>
            """
            
            html_body = f"""
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
            background: linear-gradient(135deg, {gradient_start} 0%, {gradient_end} 100%);
            color: white;
            padding: 30px;
            border-radius: 8px;
            text-align: center;
            margin-bottom: 20px;
        }}
        .header h1 {{
            margin: 0;
            font-size: 32px;
            letter-spacing: 1px;
        }}
        .header p {{
            margin: 10px 0 0 0;
            font-size: 18px;
            opacity: 0.9;
        }}
        .alert-details {{
            background-color: #f9f9f9;
            border-left: 5px solid {gradient_start};
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
            color: {gradient_start};
        }}
        .value {{
            color: #333;
        }}
        .analysis-box {{
            background-color: #f0f8ff;
            border: 2px solid {gradient_start};
            padding: 15px;
            margin: 20px 0;
            border-radius: 6px;
        }}
        .analysis-box h3 {{
            margin: 0 0 15px 0;
            color: {gradient_start};
        }}
        .analysis-item {{
            display: flex;
            justify-content: space-between;
            padding: 8px 0;
            border-bottom: 1px solid {gradient_start}33;
        }}
        .analysis-item:last-child {{
            border-bottom: none;
        }}
        .analysis-label {{
            font-weight: bold;
            color: #333;
        }}
        .analysis-value {{
            color: {gradient_start};
            font-weight: bold;
        }}
        .analysis-note {{
            background-color: {gradient_start}11;
            padding: 10px;
            margin-top: 10px;
            border-radius: 4px;
            color: {gradient_start};
            font-weight: bold;
        }}
        .cta-button {{
            display: inline-block;
            background-color: {gradient_start};
            color: white;
            padding: 12px 24px;
            text-decoration: none;
            border-radius: 4px;
            margin-top: 15px;
        }}
        .footer {{
            margin-top: 20px;
            padding-top: 15px;
            border-top: 1px solid #eee;
            font-size: 12px;
            color: #999;
            text-align: center;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>{signal_emoji} {signal_name} SIGNAL</h1>
            <p>Multiple bullish/bearish conditions detected</p>
        </div>
        
        <div class="alert-details">
            <div class="detail-row">
                <span class="label">Stock Symbol:</span>
                <span class="value">{symbol}</span>
            </div>
            <div class="detail-row">
                <span class="label">Current Price:</span>
                <span class="value">${current_price:.2f}</span>
            </div>
            <div class="detail-row">
                <span class="label">Signal Triggered At:</span>
                <span class="value">{triggered_at}</span>
            </div>
        </div>
        
        {condition_analysis}
        
        <p style="text-align: center; font-size: 16px; margin: 20px 0;">
            {'🟢 All conditions aligned for a strong buying opportunity' if alert_type == 'strong_buy_signal' else '🔴 All conditions aligned for a strong selling opportunity'}
        </p>
        
        <div style="text-align: center;">
            <a href="http://localhost:3000/dashboard" class="cta-button">Take Action Now</a>
        </div>
        
        <div class="footer">
            <p>Stock Sentinel - Professional Trading Signal Detection</p>
            <p>This is an automated alert. Your portfolio performance is your responsibility.</p>
        </div>
    </div>
</body>
</html>
            """
            
            text_body = f"""
🚀 STOCK SENTINEL - {signal_name} SIGNAL FOR {symbol}

═══════════════════════════════════════════════════

SIGNAL ANALYSIS:
• Current Price: ${current_price:.2f}
• SMA({sma_period}-day): ${sma_value:.2f} - Price {'above' if alert_type == 'strong_buy_signal' else 'below'} SMA ✓
• EMA({ema_period}-day): ${ema_value:.2f} - Price {'above' if alert_type == 'strong_buy_signal' else 'below'} EMA ✓
• RSI({rsi_period}): {rsi_value:.1f} - {'Oversold (<30)' if alert_type == 'strong_buy_signal' else 'Overbought (>70)'} ✓

═══════════════════════════════════════════════════

{'✅ STRONG BUY SIGNAL - All bullish conditions met!' if alert_type == 'strong_buy_signal' else '❌ STRONG SELL SIGNAL - All bearish conditions met!'}

This is a high-confidence signal combining:
1. Trend Analysis (SMA)
2. Momentum Analysis (EMA)
3. Strength Analysis (RSI)

Triggered At: {triggered_at}

Take Action: http://localhost:3000/dashboard

═══════════════════════════════════════════════════
Stock Sentinel - Professional Trading Signal Detection
            """.strip()
        else:
            # Regular price alert
            html_body = ALERT_TRIGGERED_HTML_TEMPLATE.format(
                symbol=symbol,
                current_price=current_price,
                condition=condition,
                target_value=target_value,
                triggered_at=triggered_at,
            )
            
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
        
        # Create message with email recipients
        message = MessageSchema(
            subject=subject,
            recipients=cast(List, [to_email]),
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
        
        # Create message with email recipients
        message = MessageSchema(
            subject=subject,
            recipients=cast(List, [to_email]),
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
