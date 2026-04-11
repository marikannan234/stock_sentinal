"""
WhatsApp notification service using Twilio.

Sends real-time WhatsApp notifications when alerts trigger.
"""

import logging
from typing import Optional

from app.config import settings

try:
    from twilio.rest import Client
except ImportError:  # pragma: no cover - handled gracefully at runtime
    Client = None

logger = logging.getLogger(__name__)


def send_whatsapp_alert(
    phone_number: str,
    symbol: str,
    current_price: float,
    condition: str,
    target_value: float,
    triggered_at: str,
) -> bool:
    """
    Send WhatsApp alert notification via Twilio.
    
    Args:
        phone_number: User's WhatsApp phone number (with country code, e.g., "+919876543210")
        symbol: Stock symbol (e.g., "AAPL")
        current_price: Current stock price
        condition: Alert condition (">", "<", ">=", "<=")
        target_value: Target price value
        triggered_at: ISO timestamp when alert triggered
    
    Returns:
        True if SMS sent successfully, False otherwise
    """
    try:
        if Client is None:
            logger.error("Twilio SDK is not installed in the active Python environment")
            return False

        # Check if WhatsApp notifications are enabled
        if not settings.ENABLE_WHATSAPP_NOTIFICATIONS:
            logger.debug("WhatsApp notifications disabled")
            return False
        
        # Validate phone number
        if not phone_number or not phone_number.startswith("+"):
            logger.warning(f"Invalid WhatsApp phone: {phone_number}")
            return False
        
        # Initialize Twilio client
        client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
        
        # Format WhatsApp message
        message_body = (
            f"🔔 *Stock Alert Triggered*\n\n"
            f"Symbol: *{symbol}*\n"
            f"Current Price: ${current_price:.2f}\n"
            f"Condition: {symbol} {condition} ${target_value:.2f}\n"
            f"Triggered: {triggered_at}\n\n"
            f"View alert details in Stock Sentinel app."
        )
        
        # Send WhatsApp message
        message = client.messages.create(
            body=message_body,
            from_=f"whatsapp:{settings.TWILIO_WHATSAPP_NUMBER}",
            to=f"whatsapp:{phone_number}",
        )
        
        logger.info(
            f"✅ WhatsApp alert sent successfully",
            extra={
                "to_phone": phone_number,
                "symbol": symbol,
                "message_sid": message.sid,
            },
        )
        
        return True
    
    except Exception as e:
        logger.error(
            f"❌ Failed to send WhatsApp alert",
            extra={
                "to_phone": phone_number,
                "symbol": symbol,
                "error": str(e),
                "error_type": type(e).__name__,
            },
            exc_info=True,
        )
        return False


def send_whatsapp_notification(
    phone_number: str,
    message: str,
) -> bool:
    """
    Send a custom WhatsApp message via Twilio.
    
    Args:
        phone_number: Recipient's WhatsApp number (with country code)
        message: Message content
    
    Returns:
        True if sent successfully, False otherwise
    """
    try:
        if Client is None:
            logger.error("Twilio SDK is not installed in the active Python environment")
            return False

        # Check if WhatsApp notifications are enabled
        if not settings.ENABLE_WHATSAPP_NOTIFICATIONS:
            logger.debug("WhatsApp notifications disabled")
            return False
        
        # Validate inputs
        if not phone_number or not phone_number.startswith("+"):
            logger.warning(f"Invalid WhatsApp phone: {phone_number}")
            return False
        
        if not message or len(message) == 0:
            logger.warning("Empty message")
            return False
        
        # Initialize Twilio client
        client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
        
        # Send message
        msg = client.messages.create(
            body=message,
            from_=f"whatsapp:{settings.TWILIO_WHATSAPP_NUMBER}",
            to=f"whatsapp:{phone_number}",
        )
        
        logger.info(
            f"✅ WhatsApp message sent",
            extra={
                "to_phone": phone_number,
                "message_length": len(message),
                "message_sid": msg.sid,
            },
        )
        
        return True
    
    except Exception as e:
        logger.error(
            f"❌ Failed to send WhatsApp message",
            extra={
                "to_phone": phone_number,
                "error": str(e),
            },
            exc_info=True,
        )
        return False
