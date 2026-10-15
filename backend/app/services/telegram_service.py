"""Telegram Bot API notification delivery for stock alerts."""

import logging
import requests

from app.config import settings

logger = logging.getLogger(__name__)


def send_telegram_notification(*, chat_id: str, message: str) -> bool:
    """Send a Telegram message; return False when disabled, unconfigured, or failed."""
    token = settings.TELEGRAM_BOT_TOKEN
    if not settings.ENABLE_TELEGRAM_NOTIFICATIONS or not token or not chat_id:
        return False
    try:
        response = requests.post(
            f"https://api.telegram.org/bot{token}/sendMessage",
            json={"chat_id": chat_id, "text": message, "disable_web_page_preview": True},
            timeout=5,
        )
        response.raise_for_status()
        payload = response.json()
        if not payload.get("ok"):
            logger.warning("Telegram API rejected alert notification")
            return False
        return True
    except Exception as exc:
        # Never log the bot token, chat ID, or full request URL (token is in URL).
        logger.warning("Telegram alert notification failed", extra={"error_type": type(exc).__name__})
        return False
