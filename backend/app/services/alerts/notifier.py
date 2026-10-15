"""
Notifications for a fired alert: email (SMTP), Telegram, and optionally
a WebSocket push.

Each channel is independent and failures are logged and swallowed, so a
provider outage never stops the alert job. Logs never contain recipient
identifiers or credentials.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime

from app.config import settings
from app.core.event_loop import run_coroutine_from_thread
from app.models.alert import Alert
from app.services.alerts.base import CheckResult
from app.services.telegram_service import send_telegram_notification
from app.services.email_smtp import send_alert_notification

logger = logging.getLogger(__name__)

# WebSocket alert push is OFF: /ws/alerts has no authentication and would send
# every user's alerts to every connected client. Turn this on only once alerts
# are delivered per authenticated user. The thread -> event loop path it uses
# (app.core.event_loop) is implemented and tested.
BROADCAST_ALERTS_OVER_WEBSOCKET = False
WEBSOCKET_TIMEOUT_SECONDS = 5.0


@dataclass
class NotificationOutcome:
    email_sent: bool = False
    telegram_sent: bool = False
    websocket_sent: bool = False


class AlertNotifier:
    def notify(self, alert: Alert, result: CheckResult, price: float, triggered_at: datetime) -> NotificationOutcome:
        outcome = NotificationOutcome()
        context = {"alert_id": alert.id, "symbol": alert.stock_symbol, "alert_type": alert.alert_type.value}
        user = alert.user

        if settings.ENABLE_EMAIL_NOTIFICATIONS and user is not None and user.email:
            try:
                outcome.email_sent = bool(send_alert_notification(
                    user_email=user.email,
                    symbol=alert.stock_symbol,
                    current_price=price,
                    condition=alert.condition.value if alert.condition else "",
                    target_value=alert.target_value,
                    triggered_at=triggered_at.isoformat(),
                    alert_type=alert.alert_type.value,
                    sma_value=result.indicators.get("sma_value"),
                    sma_period=result.indicators.get("sma_period"),
                    ema_value=result.indicators.get("ema_value"),
                    ema_period=result.indicators.get("ema_period"),
                    rsi_value=result.indicators.get("rsi_value"),
                    rsi_period=result.indicators.get("rsi_period"),
                    description=result.description,
                ))
            except Exception as exc:
                logger.warning("Alert email failed", extra={**context, "error_type": type(exc).__name__})

        if settings.ENABLE_TELEGRAM_NOTIFICATIONS and user is not None and getattr(user, "telegram_chat_id", None):
            try:
                outcome.telegram_sent = bool(send_telegram_notification(
                    chat_id=user.telegram_chat_id,
                    message=telegram_message(alert, result, price, triggered_at),
                ))
            except Exception as exc:
                logger.warning("Alert Telegram message failed", extra={**context, "error_type": type(exc).__name__})

        if BROADCAST_ALERTS_OVER_WEBSOCKET:
            outcome.websocket_sent = self._broadcast(alert, result, price, triggered_at)

        return outcome

    def _broadcast(self, alert: Alert, result: CheckResult, price: float, triggered_at: datetime) -> bool:
        from app.ws.connection_manager import alert_manager

        payload = {
            "type": "alert",
            "alert_id": alert.id,
            "symbol": alert.stock_symbol,
            "alert_type": alert.alert_type.value,
            "message": f"Alert triggered: {result.description}",
            "current_price": price,
            "target_value": alert.target_value,
            "condition": alert.condition.value if alert.condition else None,
            "timestamp": triggered_at.isoformat(),
        }
        try:
            return run_coroutine_from_thread(alert_manager.broadcast_alert(payload), timeout=WEBSOCKET_TIMEOUT_SECONDS)
        except Exception as exc:
            logger.warning(
                "Alert WebSocket push failed",
                extra={"alert_id": alert.id, "error_type": type(exc).__name__},
            )
            return False


def telegram_message(alert: Alert, result: CheckResult, price: float, triggered_at: datetime) -> str:
    rule = result.description or f"{alert.stock_symbol} {alert.alert_type.value} alert"
    return (
        "🚨 STOCKSENTINEL ALERT\n\n"
        f"Symbol: {alert.stock_symbol}\n"
        f"Rule: {rule}\n"
        f"Current price: {price:.2f}\n"
        f"Triggered at: {triggered_at.strftime('%d-%m-%Y %H:%M')} UTC\n\n"
        "This one-shot alert is now paused. Re-enable it in StockSentinel to keep watching."
    )
