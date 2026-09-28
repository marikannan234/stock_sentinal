"""
The alert job: `run_alert_checks()` is the single entry point (called by the
scheduler through app.services.alert_service.check_all_alerts).

One run:
  1. load active alerts, grouped by symbol
  2. fetch one market-data snapshot per symbol (a failed symbol is skipped;
     no substitute price is ever used)
  3. evaluate each alert with the checker for its type
  4. persist the checker's state (reference/previous values)
  5. if it fired: claim it atomically (active -> inactive, one-shot), write
     an AlertHistory row, commit, then notify

Lifecycle (one-shot): an alert that fires is deactivated (is_active=False,
is_triggered=True) and never fires again until the user re-enables it, which
re-arms it (see AlertService.update_alert_status). The claim is a
conditional UPDATE, so even overlapping runs cannot notify twice.

Isolation: every alert runs in its own transaction. An exception in one
alert (or one symbol's data fetch) is logged with its context and the run
continues with the next.
"""

from __future__ import annotations

import logging
import time
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime
from typing import Callable

from sqlalchemy.orm import Session, joinedload

from app.models.alert import Alert, AlertHistory, AlertType
from app.services.alerts.base import Checker, CheckResult
from app.services.alerts.crash_checker import check_crash
from app.services.alerts.custom_checker import check_custom
from app.services.alerts.indicator_checker import (
    check_combined_signal,
    check_moving_average_crossover,
    check_moving_average_level,
    check_rsi_crossover,
    check_rsi_level,
)
from app.services.alerts.market_data import (
    MarketDataError,
    SnapshotFetcher,
    SymbolSnapshot,
    bars_needed,
    fetch_snapshot,
)
from app.services.alerts.notifier import AlertNotifier
from app.services.alerts.percentage_checker import check_percentage_change
from app.services.alerts.price_checker import check_price
from app.services.alerts.volume_checker import check_volume_spike

logger = logging.getLogger(__name__)

CHECKERS: dict[AlertType, Checker] = {
    AlertType.PRICE: check_price,
    AlertType.CUSTOM: check_custom,
    AlertType.PERCENTAGE_CHANGE: check_percentage_change,
    AlertType.CRASH: check_crash,
    AlertType.VOLUME_SPIKE: check_volume_spike,
    AlertType.SMA_ABOVE: check_moving_average_level,
    AlertType.SMA_BELOW: check_moving_average_level,
    AlertType.SMA_CROSSOVER: check_moving_average_crossover,
    AlertType.EMA_ABOVE: check_moving_average_level,
    AlertType.EMA_BELOW: check_moving_average_level,
    AlertType.EMA_CROSSOVER: check_moving_average_crossover,
    AlertType.RSI_OVERBOUGHT: check_rsi_level,
    AlertType.RSI_OVERSOLD: check_rsi_level,
    AlertType.RSI_CROSSOVER: check_rsi_crossover,
    AlertType.STRONG_BUY_SIGNAL: check_combined_signal,
    AlertType.STRONG_SELL_SIGNAL: check_combined_signal,
}
assert set(CHECKERS) == set(AlertType), "every alert type needs a checker"


@dataclass
class RunSummary:
    alerts_checked: int = 0
    alerts_triggered: int = 0
    alerts_skipped: int = 0
    alert_errors: int = 0
    symbols_fetched: int = 0
    symbol_errors: dict[str, str] = field(default_factory=dict)
    triggered_ids: list[int] = field(default_factory=list)


def run_alert_checks(
    session_factory: Callable[[], Session] | None = None,
    fetch: SnapshotFetcher | None = None,
    notifier: AlertNotifier | None = None,
) -> RunSummary:
    if session_factory is None:
        from app.db.session import SessionLocal as session_factory  # noqa: N813
    fetch = fetch or fetch_snapshot
    notifier = notifier or AlertNotifier()
    summary = RunSummary()
    started = time.monotonic()

    db = session_factory()
    try:
        alerts = (
            db.query(Alert)
            .options(joinedload(Alert.user))
            .filter(Alert.is_active.is_(True))
            .order_by(Alert.id)
            .all()
        )
        by_symbol: dict[str, list[Alert]] = defaultdict(list)
        for alert in alerts:
            by_symbol[alert.stock_symbol.upper()].append(alert)

        for symbol, symbol_alerts in by_symbol.items():
            snapshot = _fetch(symbol, symbol_alerts, fetch, summary)
            if snapshot is None:
                continue
            for alert in symbol_alerts:
                _run_one(db, alert, snapshot, notifier, summary)
    except Exception:
        logger.exception("Alert run aborted")
        db.rollback()
    finally:
        db.close()

    logger.info(
        "Alert run finished",
        extra={
            "alerts_checked": summary.alerts_checked,
            "alerts_triggered": summary.alerts_triggered,
            "alerts_skipped": summary.alerts_skipped,
            "alert_errors": summary.alert_errors,
            "symbols_fetched": summary.symbols_fetched,
            "symbol_errors": len(summary.symbol_errors),
            "duration_ms": int((time.monotonic() - started) * 1000),
        },
    )
    return summary


def _fetch(symbol: str, alerts: list[Alert], fetch: SnapshotFetcher, summary: RunSummary) -> SymbolSnapshot | None:
    bars = max(bars_needed(alert) for alert in alerts)
    try:
        snapshot = fetch(symbol, bars)
    except MarketDataError as exc:
        summary.symbol_errors[symbol] = str(exc)
        logger.warning(
            "No market data; skipping symbol this run",
            extra={"symbol": symbol, "alerts": len(alerts), "error_category": "market_data", "reason": str(exc)},
        )
        return None
    except Exception as exc:
        summary.symbol_errors[symbol] = type(exc).__name__
        logger.error(
            "Market data fetch crashed; skipping symbol this run",
            extra={"symbol": symbol, "alerts": len(alerts), "error_category": type(exc).__name__},
            exc_info=True,
        )
        return None
    summary.symbols_fetched += 1
    return snapshot


def _run_one(db: Session, alert: Alert, snapshot: SymbolSnapshot, notifier: AlertNotifier, summary: RunSummary) -> None:
    alert_id, alert_type = alert.id, alert.alert_type
    try:
        summary.alerts_checked += 1
        result = CHECKERS[AlertType(alert_type)](alert, snapshot)
        for attribute, value in result.state.items():
            setattr(alert, attribute, value)

        if result.skipped:
            summary.alerts_skipped += 1
            logger.info(
                "Alert not evaluated",
                extra={"alert_id": alert_id, "symbol": snapshot.symbol, "alert_type": alert_type.value, "reason": result.skipped},
            )
        if not result.triggered:
            db.commit()
            return

        now = datetime.utcnow()
        history = _claim_and_record(db, alert, result, snapshot.price, now)
        if history is None:
            return  # disabled or already fired concurrently
        summary.alerts_triggered += 1
        summary.triggered_ids.append(alert_id)
        logger.info(
            "Alert triggered",
            extra={"alert_id": alert_id, "symbol": snapshot.symbol, "alert_type": alert_type.value, "history_id": history.id},
        )
        _notify(db, notifier, alert, history, result, snapshot.price, now)
    except Exception as exc:
        db.rollback()
        summary.alert_errors += 1
        logger.error(
            "Alert check failed",
            extra={
                "alert_id": alert_id,
                "symbol": snapshot.symbol,
                "alert_type": getattr(alert_type, "value", str(alert_type)),
                "error_category": type(exc).__name__,
            },
            exc_info=True,
        )


def _claim_and_record(db: Session, alert: Alert, result: CheckResult, price: float, now: datetime) -> AlertHistory | None:
    """Deactivate the alert only if it is still active; record the trigger."""
    db.flush()  # persist state updates from the checker first
    claimed = (
        db.query(Alert)
        .filter(Alert.id == alert.id, Alert.is_active.is_(True))
        .update(
            {
                Alert.is_active: False,
                Alert.is_triggered: True,
                Alert.triggered_at: now,
                Alert.last_triggered_at: now,
            },
            synchronize_session="fetch",
        )
    )
    if claimed != 1:
        db.rollback()
        return None

    history = AlertHistory(
        alert_id=alert.id,
        user_id=alert.user_id,
        triggered_at=now,
        stock_symbol=alert.stock_symbol,
        alert_type=alert.alert_type,
        price_at_trigger=price,
        target_value=alert.target_value,
        condition=alert.condition,
        message=f"Alert triggered: {result.description}"[:500],
        email_sent=False,
    )
    db.add(history)
    db.commit()
    return history


def _notify(db: Session, notifier: AlertNotifier, alert: Alert, history: AlertHistory,
            result: CheckResult, price: float, now: datetime) -> None:
    # The trigger is already committed; a notification problem must not undo it.
    try:
        outcome = notifier.notify(alert, result, price, now)
    except Exception as exc:
        logger.warning(
            "Alert notification failed",
            extra={"alert_id": alert.id, "error_category": type(exc).__name__},
        )
        return
    if outcome.email_sent:
        history.email_sent = True
        history.email_sent_at = datetime.utcnow()
        db.commit()
