"""
Alert job tests: real runner, checkers, indicator math, database and scheduler;
only the network is replaced (a fake market serving known price series).
"""

import asyncio
import logging
import math
import threading
import time
from collections import Counter
from datetime import date, datetime, timedelta

import pandas as pd
import pytest

from app.config import settings
from app.core import event_loop
from app.models.alert import Alert, AlertCondition, AlertHistory, AlertType
from app.services.alerts import alert_runner, indicators, market_data, notifier
from app.services.alerts.alert_runner import CHECKERS, run_alert_checks
from app.services.alerts.market_data import (
    MarketDataError,
    SymbolSnapshot,
    bars_needed,
    snapshot_from_history,
)

USER_EMAIL = "alerts-owner@example.com"


# ---------------------------------------------------------------------------
# fixtures / helpers
# ---------------------------------------------------------------------------

class FakeMarket:
    """Serves daily series per symbol and counts requests."""

    def __init__(self):
        self.series: dict[str, tuple[list[float], list[float]]] = {}
        self.calls: Counter = Counter()
        self.bars_requested: dict[str, int] = {}
        self.errors: dict[str, Exception] = {}

    def set(self, symbol, closes, volumes=None):
        self.series[symbol] = (list(closes), list(volumes or [1_000_000.0] * len(closes)))

    def fetch(self, symbol, bars):
        self.calls[symbol] += 1
        self.bars_requested[symbol] = bars
        if symbol in self.errors:
            raise self.errors[symbol]
        if symbol not in self.series:
            raise MarketDataError("no price history returned")
        closes, volumes = self.series[symbol]
        return SymbolSnapshot(symbol=symbol, closes=tuple(closes), volumes=tuple(volumes))


@pytest.fixture()
def fake_market():
    return FakeMarket()


@pytest.fixture()
def owner(db_session):
    from app.core.security import get_password_hash
    from app.models.user import User

    user = User(email=USER_EMAIL, password_hash=get_password_hash("x" * 12), full_name="Owner")
    db_session.add(user)
    db_session.commit()
    return user


@pytest.fixture()
def emails(monkeypatch):
    """Record alert emails instead of sending them."""
    sent = []

    def fake_send(**kwargs):
        sent.append(kwargs)
        return True

    monkeypatch.setattr(settings, "ENABLE_EMAIL_NOTIFICATIONS", True)
    monkeypatch.setattr(notifier, "send_alert_notification", fake_send)
    return sent


def make_alert(db, user, symbol="AAPL", alert_type=AlertType.PRICE, **fields):
    alert = Alert(user_id=user.id, stock_symbol=symbol, alert_type=alert_type, is_active=True, is_triggered=False, **fields)
    db.add(alert)
    db.commit()
    return alert


def run(session_factory, market, **kwargs):
    return run_alert_checks(session_factory=session_factory, fetch=market.fetch, **kwargs)


def reload(db, alert):
    db.expire_all()
    return db.get(Alert, alert.id)


def history_for(db, alert):
    db.expire_all()
    return db.query(AlertHistory).filter(AlertHistory.alert_id == alert.id).all()


# ---------------------------------------------------------------------------
# indicator math (same formulas as app.services.indicator_service)
# ---------------------------------------------------------------------------

def test_sma_ema_rsi_values():
    closes = [float(x) for x in range(1, 11)]  # 1..10
    assert indicators.sma(closes, 5) == 8.0
    assert indicators.ema([10.0] * 30, 10) == 10.0
    assert indicators.rsi(closes, 5) == 100.0                  # only gains
    assert indicators.rsi(list(reversed(closes)), 5) == 0.0     # only losses


@pytest.mark.parametrize(
    "func, period, available",
    [(indicators.sma, 200, 150), (indicators.ema, 50, 49), (indicators.rsi, 14, 14)],
)
def test_indicators_refuse_short_history(func, period, available):
    with pytest.raises(indicators.InsufficientHistoryError) as exc:
        func([100.0] * available, period)
    assert exc.value.available == available


# ---------------------------------------------------------------------------
# market data
# ---------------------------------------------------------------------------

def _frame(closes, volumes=None):
    return pd.DataFrame({"Close": closes, "Volume": volumes or [1000] * len(closes)})


def test_snapshot_parses_history_and_drops_bad_bars():
    snapshot = snapshot_from_history("AAPL", _frame([100.0, math.nan, 0.0, 101.0, 102.5]))

    assert snapshot.closes == (100.0, 101.0, 102.5)
    assert snapshot.price == 102.5


@pytest.mark.parametrize(
    "frame",
    [pd.DataFrame(), _frame([100.0, 101.0, math.nan]), _frame([100.0, 0.0]), _frame([100.0, -5.0])],
    ids=["empty", "latest-nan", "latest-zero", "latest-negative"],
)
def test_snapshot_never_substitutes_a_price(frame):
    with pytest.raises(MarketDataError):
        snapshot_from_history("AAPL", frame)


def test_fetch_snapshot_requests_enough_calendar_days(monkeypatch):
    requested = {}

    class FakeTicker:
        def __init__(self, symbol):
            requested["symbol"] = symbol

        def history(self, **kwargs):
            requested.update(kwargs)
            return _frame([100.0] * 250)

    monkeypatch.setattr(market_data.yf, "Ticker", FakeTicker)

    snapshot = market_data.fetch_snapshot("AAPL", 201)

    start = date.fromisoformat(requested["start"])
    # 201 trading days need roughly 290 calendar days; weekends/holidays covered.
    assert (date.today() - start).days >= 201 * 1.4
    assert requested["interval"] == "1d"
    assert len(snapshot.closes) == 250


def test_fetch_snapshot_maps_request_errors(monkeypatch):
    class BrokenTicker:
        def __init__(self, symbol):
            pass

        def history(self, **kwargs):
            raise ConnectionError("boom")

    monkeypatch.setattr(market_data.yf, "Ticker", BrokenTicker)

    with pytest.raises(MarketDataError):
        market_data.fetch_snapshot("AAPL", 21)


def test_lookback_covers_the_longest_indicator(db_session, owner):
    sma200 = make_alert(db_session, owner, alert_type=AlertType.SMA_ABOVE, sma_period=200)
    rsi14 = make_alert(db_session, owner, alert_type=AlertType.RSI_OVERSOLD, rsi_period=14)
    price = make_alert(db_session, owner, alert_type=AlertType.PRICE, condition=AlertCondition.GREATER_THAN, target_value=1)

    assert bars_needed(sma200) >= 201
    assert bars_needed(rsi14) >= 3 * 14
    assert bars_needed(price) == market_data.MIN_BARS


# ---------------------------------------------------------------------------
# evaluation per type
# ---------------------------------------------------------------------------

def test_price_alert_triggers_and_records_history(session_factory, db_session, owner, fake_market, emails):
    fake_market.set("AAPL", [140.0, 151.0])
    alert = make_alert(db_session, owner, condition=AlertCondition.GREATER_THAN, target_value=150)

    summary = run(session_factory, fake_market)

    assert summary.triggered_ids == [alert.id]
    alert = reload(db_session, alert)
    assert (alert.is_active, alert.is_triggered) == (False, True)
    assert alert.triggered_at is not None
    [history] = history_for(db_session, alert)
    assert history.price_at_trigger == 151.0
    assert history.email_sent is True
    assert "151.00 > 150.00" in history.message
    assert len(emails) == 1 and emails[0]["user_email"] == USER_EMAIL


def test_price_alert_not_met_stays_active(session_factory, db_session, owner, fake_market, emails):
    fake_market.set("AAPL", [140.0, 149.99])
    alert = make_alert(db_session, owner, condition=AlertCondition.GREATER_THAN, target_value=150)

    summary = run(session_factory, fake_market)

    assert summary.alerts_triggered == 0
    assert reload(db_session, alert).is_active is True
    assert emails == []


def test_percentage_change_uses_reference_price(session_factory, db_session, owner, fake_market):
    alert = make_alert(db_session, owner, alert_type=AlertType.PERCENTAGE_CHANGE, target_value=5)

    fake_market.set("AAPL", [100.0])
    first = run(session_factory, fake_market)
    assert first.alerts_skipped == 1 and first.alerts_triggered == 0
    assert reload(db_session, alert).last_price == 100.0

    fake_market.set("AAPL", [100.0, 103.0])  # +3%: not enough, reference must not move
    run(session_factory, fake_market)
    assert reload(db_session, alert).last_price == 100.0

    fake_market.set("AAPL", [100.0, 103.0, 106.0])  # +6% from the reference
    assert run(session_factory, fake_market).triggered_ids == [alert.id]


def test_percentage_change_triggers_on_drops_too(session_factory, db_session, owner, fake_market):
    alert = make_alert(db_session, owner, alert_type=AlertType.PERCENTAGE_CHANGE, target_value=5, last_price=100.0)
    fake_market.set("AAPL", [94.0])

    assert run(session_factory, fake_market).triggered_ids == [alert.id]


def test_crash_triggers_only_on_drop(session_factory, db_session, owner, fake_market):
    crash = make_alert(db_session, owner, alert_type=AlertType.CRASH, target_value=8, last_price=100.0)
    rally = make_alert(db_session, owner, symbol="MSFT", alert_type=AlertType.CRASH, target_value=8, last_price=100.0)
    fake_market.set("AAPL", [91.0])   # -9%
    fake_market.set("MSFT", [110.0])  # +10%

    assert run(session_factory, fake_market).triggered_ids == [crash.id]
    assert reload(db_session, rally).is_active is True


def test_volume_spike(session_factory, db_session, owner, fake_market):
    spike = make_alert(db_session, owner, alert_type=AlertType.VOLUME_SPIKE, target_value=2)
    fake_market.set("AAPL", [100.0] * 21, volumes=[1_000_000.0] * 20 + [2_500_000.0])

    assert run(session_factory, fake_market).triggered_ids == [spike.id]


def test_volume_below_threshold_does_not_trigger(session_factory, db_session, owner, fake_market):
    make_alert(db_session, owner, alert_type=AlertType.VOLUME_SPIKE, target_value=3)
    fake_market.set("AAPL", [100.0] * 21, volumes=[1_000_000.0] * 20 + [2_500_000.0])

    assert run(session_factory, fake_market).alerts_triggered == 0


RISING = [100.0 + i for i in range(60)]           # price well above its averages
FALLING = [160.0 - i for i in range(60)]


def test_sma_above_and_below(session_factory, db_session, owner, fake_market, emails):
    above = make_alert(db_session, owner, alert_type=AlertType.SMA_ABOVE, sma_period=50)
    below = make_alert(db_session, owner, symbol="MSFT", alert_type=AlertType.SMA_BELOW, sma_period=50)
    fake_market.set("AAPL", RISING)
    fake_market.set("MSFT", RISING)

    assert run(session_factory, fake_market).triggered_ids == [above.id]
    assert reload(db_session, below).is_active is True
    assert emails[0]["sma_period"] == 50 and emails[0]["sma_value"] == indicators.sma(RISING, 50)
    assert "SMA(50)" in emails[0]["description"]


def test_ema_and_rsi_levels(session_factory, db_session, owner, fake_market):
    ema_below = make_alert(db_session, owner, alert_type=AlertType.EMA_BELOW, ema_period=10)
    oversold = make_alert(db_session, owner, alert_type=AlertType.RSI_OVERSOLD, rsi_period=14)
    overbought = make_alert(db_session, owner, alert_type=AlertType.RSI_OVERBOUGHT, rsi_period=14)
    fake_market.set("AAPL", FALLING)

    triggered = run(session_factory, fake_market).triggered_ids

    assert sorted(triggered) == sorted([ema_below.id, oversold.id])
    assert reload(db_session, overbought).is_active is True


def test_sma_crossover_needs_a_baseline_then_fires(session_factory, db_session, owner, fake_market):
    alert = make_alert(db_session, owner, alert_type=AlertType.SMA_CROSSOVER, sma_period=5)
    fake_market.set("AAPL", [100.0] * 10 + [95.0])  # price below its SMA

    assert run(session_factory, fake_market).alerts_triggered == 0
    assert reload(db_session, alert).last_price == 95.0

    fake_market.set("AAPL", [100.0] * 10 + [95.0, 110.0])  # jumps above the SMA
    assert run(session_factory, fake_market).triggered_ids == [alert.id]


def test_rsi_crossover(session_factory, db_session, owner, fake_market):
    alert = make_alert(db_session, owner, alert_type=AlertType.RSI_CROSSOVER, rsi_period=5, last_rsi=25.0)
    fake_market.set("AAPL", [100.0 + i for i in range(20)])  # RSI 100 now

    assert run(session_factory, fake_market).triggered_ids == [alert.id]


def test_combined_strong_sell_signal(session_factory, db_session, owner, fake_market):
    # Long decline keeps price under SMA/EMA(50); a short rally pushes RSI(5) above 70.
    closes = [110.0 - i for i in range(60)] + [51.0, 52.0, 53.0, 54.0, 55.0, 56.0]
    sell = make_alert(db_session, owner, alert_type=AlertType.STRONG_SELL_SIGNAL, sma_period=50, ema_period=50, rsi_period=5)
    buy = make_alert(db_session, owner, alert_type=AlertType.STRONG_BUY_SIGNAL, sma_period=50, ema_period=50, rsi_period=5)
    fake_market.set("AAPL", closes)

    assert run(session_factory, fake_market).triggered_ids == [sell.id]
    assert reload(db_session, buy).is_active is True


def test_custom_alert_behaves_like_price_rule(session_factory, db_session, owner, fake_market):
    alert = make_alert(db_session, owner, alert_type=AlertType.CUSTOM, condition=AlertCondition.LESS_THAN, target_value=50)
    fake_market.set("AAPL", [49.0])

    assert run(session_factory, fake_market).triggered_ids == [alert.id]


def test_insufficient_history_skips_without_signal(session_factory, db_session, owner, fake_market, emails):
    alert = make_alert(db_session, owner, alert_type=AlertType.SMA_ABOVE, sma_period=200)
    fake_market.set("AAPL", RISING[:100])  # price is above every average, but only 100 bars

    summary = run(session_factory, fake_market)

    assert summary.alerts_skipped == 1
    assert summary.alerts_triggered == 0
    assert fake_market.bars_requested["AAPL"] >= 201
    assert reload(db_session, alert).is_active is True
    assert emails == []


# ---------------------------------------------------------------------------
# market-data efficiency and failures
# ---------------------------------------------------------------------------

def test_one_fetch_per_symbol(session_factory, db_session, owner, fake_market):
    for target in (10, 20, 30):
        make_alert(db_session, owner, "AAPL", condition=AlertCondition.GREATER_THAN, target_value=target)
    make_alert(db_session, owner, "MSFT", condition=AlertCondition.GREATER_THAN, target_value=10)
    make_alert(db_session, owner, "MSFT", alert_type=AlertType.SMA_ABOVE, sma_period=20)
    fake_market.set("AAPL", RISING)
    fake_market.set("MSFT", RISING)

    summary = run(session_factory, fake_market)

    assert fake_market.calls == Counter({"AAPL": 1, "MSFT": 1})
    assert summary.alerts_checked == 5


def test_missing_price_skips_symbol_and_leaves_alert_untouched(session_factory, db_session, owner, fake_market, emails):
    missing = make_alert(db_session, owner, "NOPE", alert_type=AlertType.PERCENTAGE_CHANGE, target_value=5)
    ok = make_alert(db_session, owner, "AAPL", condition=AlertCondition.GREATER_THAN, target_value=1)
    fake_market.set("AAPL", [100.0])

    summary = run(session_factory, fake_market)

    assert "NOPE" in summary.symbol_errors
    assert summary.triggered_ids == [ok.id]
    missing = reload(db_session, missing)
    assert (missing.is_active, missing.last_price) == (True, None)


def test_zero_price_from_provider_is_never_used(session_factory, db_session, owner):
    alert = make_alert(db_session, owner, condition=AlertCondition.LESS_THAN, target_value=1)

    def fetch(symbol, bars):
        return snapshot_from_history(symbol, _frame([100.0, 0.0]))  # provider returned 0

    summary = run_alert_checks(session_factory=session_factory, fetch=fetch)

    assert summary.symbol_errors and summary.alerts_triggered == 0
    assert reload(db_session, alert).is_active is True


def test_crashing_fetch_for_one_symbol_does_not_stop_others(session_factory, db_session, owner, fake_market):
    make_alert(db_session, owner, "AAPL", condition=AlertCondition.GREATER_THAN, target_value=1)
    msft = make_alert(db_session, owner, "MSFT", condition=AlertCondition.GREATER_THAN, target_value=1)
    fake_market.errors["AAPL"] = RuntimeError("provider exploded")
    fake_market.set("MSFT", [100.0])

    summary = run(session_factory, fake_market)

    assert summary.symbol_errors["AAPL"] == "RuntimeError"
    assert summary.triggered_ids == [msft.id]


def test_broken_alert_does_not_stop_other_alerts(session_factory, db_session, owner, fake_market, monkeypatch):
    broken = make_alert(db_session, owner, "AAPL", condition=AlertCondition.GREATER_THAN, target_value=1)
    same_symbol = make_alert(db_session, owner, "AAPL", alert_type=AlertType.CRASH, target_value=5, last_price=200.0)
    other_symbol = make_alert(db_session, owner, "MSFT", condition=AlertCondition.GREATER_THAN, target_value=1)
    fake_market.set("AAPL", [100.0])
    fake_market.set("MSFT", [100.0])

    real_price_checker = CHECKERS[AlertType.PRICE]

    def flaky(alert, snapshot):
        if alert.id == broken.id:
            raise ZeroDivisionError("bad alert")
        return real_price_checker(alert, snapshot)

    monkeypatch.setitem(CHECKERS, AlertType.PRICE, flaky)

    summary = run(session_factory, fake_market)

    assert summary.alert_errors == 1
    assert sorted(summary.triggered_ids) == sorted([same_symbol.id, other_symbol.id])
    assert reload(db_session, broken).is_active is True


# ---------------------------------------------------------------------------
# lifecycle (one-shot) and notifications
# ---------------------------------------------------------------------------

def test_fired_alert_does_not_notify_again(session_factory, db_session, owner, fake_market, emails):
    alert = make_alert(db_session, owner, condition=AlertCondition.GREATER_THAN, target_value=150)
    fake_market.set("AAPL", [151.0])

    run(session_factory, fake_market)
    second = run(session_factory, fake_market)

    assert second.alerts_checked == 0
    assert len(emails) == 1
    assert len(history_for(db_session, alert)) == 1


def test_inactive_alerts_are_not_checked(session_factory, db_session, owner, fake_market):
    alert = make_alert(db_session, owner, condition=AlertCondition.GREATER_THAN, target_value=1)
    alert.is_active = False
    db_session.commit()
    fake_market.set("AAPL", [100.0])

    summary = run(session_factory, fake_market)

    assert summary.alerts_checked == 0
    assert fake_market.calls == Counter()


def test_reenabled_alert_fires_again(client, auth_headers, session_factory, db_session, fake_market, emails):
    alert_id = client.post(
        "/api/alerts", headers=auth_headers,
        json={"stock_symbol": "AAPL", "alert_type": "price", "condition": ">", "target_value": 150},
    ).json()["id"]
    fake_market.set("AAPL", [151.0])

    run(session_factory, fake_market)
    client.patch(f"/api/alerts/{alert_id}", headers=auth_headers, json={"is_active": True})
    run(session_factory, fake_market)

    db_session.expire_all()
    assert db_session.query(AlertHistory).filter(AlertHistory.alert_id == alert_id).count() == 2
    assert len(emails) == 2


def test_alert_disabled_mid_run_is_not_fired(session_factory, db_session, owner, fake_market, emails, monkeypatch):
    alert = make_alert(db_session, owner, condition=AlertCondition.GREATER_THAN, target_value=1)
    fake_market.set("AAPL", [100.0])
    real_checker = CHECKERS[AlertType.PRICE]

    def disable_then_check(checked_alert, snapshot):
        other = session_factory()
        other.get(Alert, checked_alert.id).is_active = False  # user pauses it concurrently
        other.commit()
        other.close()
        return real_checker(checked_alert, snapshot)

    monkeypatch.setitem(CHECKERS, AlertType.PRICE, disable_then_check)

    summary = run(session_factory, fake_market)

    assert summary.alerts_triggered == 0
    assert history_for(db_session, alert) == []
    assert emails == []


def test_notification_failure_keeps_trigger_and_continues(session_factory, db_session, owner, fake_market, monkeypatch):
    def failing_send(**kwargs):
        raise OSError("SMTP down")

    monkeypatch.setattr(settings, "ENABLE_EMAIL_NOTIFICATIONS", True)
    monkeypatch.setattr(notifier, "send_alert_notification", failing_send)
    first = make_alert(db_session, owner, "AAPL", condition=AlertCondition.GREATER_THAN, target_value=1)
    second = make_alert(db_session, owner, "MSFT", condition=AlertCondition.GREATER_THAN, target_value=1)
    fake_market.set("AAPL", [100.0])
    fake_market.set("MSFT", [100.0])

    summary = run(session_factory, fake_market)

    assert sorted(summary.triggered_ids) == sorted([first.id, second.id])
    assert summary.alert_errors == 0
    [history] = history_for(db_session, first)
    assert history.email_sent is False
    assert reload(db_session, first).is_active is False


def test_email_for_indicator_alert(session_factory, db_session, owner, fake_market, emails):
    make_alert(db_session, owner, alert_type=AlertType.SMA_ABOVE, sma_period=20)
    fake_market.set("AAPL", RISING)

    run(session_factory, fake_market)

    assert emails[0]["target_value"] is None and "SMA(20)" in emails[0]["description"]


def test_logs_do_not_contain_email_or_telegram_chat_id(session_factory, db_session, owner, fake_market, emails, monkeypatch):
    owner.telegram_chat_id = "987654321"
    db_session.commit()
    monkeypatch.setattr(settings, "ENABLE_TELEGRAM_NOTIFICATIONS", True)
    monkeypatch.setattr(notifier, "send_telegram_notification", lambda **kw: True)
    make_alert(db_session, owner, condition=AlertCondition.GREATER_THAN, target_value=1)
    fake_market.set("AAPL", [100.0])

    records = []
    handler = logging.Handler()
    handler.emit = lambda record: records.append(f"{record.getMessage()} {record.__dict__}")
    app_logger = logging.getLogger("app")
    previous_level = app_logger.level
    app_logger.setLevel(logging.DEBUG)  # independent of whichever logging config ran last
    app_logger.addHandler(handler)
    try:
        run(session_factory, fake_market)
    finally:
        app_logger.removeHandler(handler)
        app_logger.setLevel(previous_level)

    text = "\n".join(records)
    assert "Alert triggered" in text
    assert USER_EMAIL not in text and "987654321" not in text


def test_email_template_handles_indicator_alert_without_target(monkeypatch):
    from app.services import email_smtp

    captured = {}
    monkeypatch.setattr(email_smtp, "send_alert_email_smtp", lambda **kw: captured.update(kw) or True)

    assert email_smtp.send_alert_notification(
        user_email=USER_EMAIL, symbol="AAPL", current_price=190.1, condition="", target_value=None,
        triggered_at="2026-09-25T10:00:00", alert_type="sma_above", description="AAPL price 190.10 > SMA(50) 188.40",
    )
    assert "SMA(50) 188.40" in captured["text_body"] and "SMA(50) 188.40" in captured["html_body"]


def test_mask_helpers():
    from app.services.email_smtp import mask_email
    assert mask_email("jane.doe@example.com") == "ja***@example.com"


# ---------------------------------------------------------------------------
# scheduler and event loop
# ---------------------------------------------------------------------------

@pytest.fixture()
def background_loop():
    loop = asyncio.new_event_loop()
    thread = threading.Thread(target=loop.run_forever, daemon=True)
    thread.start()
    event_loop.set_main_loop(loop)
    yield loop, thread
    event_loop.clear_main_loop()
    loop.call_soon_threadsafe(loop.stop)
    thread.join(timeout=5)
    loop.close()


def test_coroutine_runs_on_main_loop_from_worker_thread(background_loop):
    loop, loop_thread = background_loop
    ran_on = []

    async def work():
        ran_on.append(threading.current_thread())

    worker_result = []
    worker = threading.Thread(target=lambda: worker_result.append(event_loop.run_coroutine_from_thread(work())))
    worker.start()
    worker.join(timeout=5)

    assert worker_result == [True]
    assert ran_on == [loop_thread]


def test_without_main_loop_coroutine_is_skipped_cleanly(recwarn):
    event_loop.clear_main_loop()

    async def work():
        raise AssertionError("must not run")

    assert event_loop.run_coroutine_from_thread(work()) is False
    assert not [w for w in recwarn if "never awaited" in str(w.message)]


def test_slow_coroutine_times_out_and_is_cancelled(background_loop):
    cancelled = threading.Event()

    async def slow():
        try:
            await asyncio.sleep(10)
        except asyncio.CancelledError:
            cancelled.set()
            raise

    assert event_loop.run_coroutine_from_thread(slow(), timeout=0.2) is False
    assert cancelled.wait(timeout=2)


def test_websocket_push_path_uses_main_loop(session_factory, db_session, owner, fake_market, background_loop, monkeypatch):
    from app.ws.connection_manager import alert_manager

    _, loop_thread = background_loop
    pushed = []

    async def fake_broadcast(payload):
        pushed.append((threading.current_thread(), payload))

    monkeypatch.setattr(notifier, "BROADCAST_ALERTS_OVER_WEBSOCKET", True)
    monkeypatch.setattr(alert_manager, "broadcast_alert", fake_broadcast)
    alert = make_alert(db_session, owner, condition=AlertCondition.GREATER_THAN, target_value=1)
    fake_market.set("AAPL", [100.0])

    worker = threading.Thread(target=lambda: run(session_factory, fake_market))  # like the scheduler thread
    worker.start()
    worker.join(timeout=10)

    [(thread, payload)] = pushed
    assert thread is loop_thread
    assert payload["alert_id"] == alert.id


def test_websocket_push_is_off_by_default(session_factory, db_session, owner, fake_market, background_loop, monkeypatch):
    from app.ws.connection_manager import alert_manager

    pushed = []

    async def fake_broadcast(payload):
        pushed.append(payload)

    monkeypatch.setattr(alert_manager, "broadcast_alert", fake_broadcast)
    make_alert(db_session, owner, condition=AlertCondition.GREATER_THAN, target_value=1)
    fake_market.set("AAPL", [100.0])

    assert run(session_factory, fake_market).alerts_triggered == 1
    assert pushed == []


def test_scheduler_runs_the_real_alert_job(session_factory, db_session, owner, fake_market, monkeypatch):
    from app.db import session as db_session_module
    from app.services import scheduler

    monkeypatch.setattr(db_session_module, "SessionLocal", session_factory)
    monkeypatch.setattr(alert_runner, "fetch_snapshot", fake_market.fetch)
    alert = make_alert(db_session, owner, condition=AlertCondition.GREATER_THAN, target_value=1)
    fake_market.set("AAPL", [100.0])

    scheduler.start_scheduler()
    try:
        scheduler.get_scheduler().get_job("check_alerts_job").modify(next_run_time=datetime.now().astimezone())
        deadline = time.monotonic() + 10
        while time.monotonic() < deadline and not history_for(db_session, alert):
            time.sleep(0.1)
    finally:
        scheduler.stop_scheduler(wait=True)

    assert len(history_for(db_session, alert)) == 1
    assert reload(db_session, alert).is_active is False
    assert not scheduler.is_scheduler_running()


def test_scheduler_survives_a_failing_run(monkeypatch):
    from app.services import scheduler

    calls = []

    def exploding_job():
        calls.append(time.monotonic())
        raise RuntimeError("run failed")

    monkeypatch.setattr(scheduler, "check_all_alerts", exploding_job)
    scheduler.start_scheduler()
    try:
        job = scheduler.get_scheduler().get_job("check_alerts_job")
        job.modify(next_run_time=datetime.now().astimezone())
        deadline = time.monotonic() + 5
        while time.monotonic() < deadline and not calls:
            time.sleep(0.05)
        job.modify(next_run_time=datetime.now().astimezone() + timedelta(milliseconds=50))
        while time.monotonic() < deadline and len(calls) < 2:
            time.sleep(0.05)
        assert scheduler.is_scheduler_running()
    finally:
        scheduler.stop_scheduler(wait=True)

    assert len(calls) >= 2


def test_telegram_notification_is_sent_for_triggered_user_alert(
    session_factory, db_session, owner, fake_market, monkeypatch
):
    sent = []
    owner.telegram_chat_id = "123456"
    db_session.commit()
    monkeypatch.setattr(settings, "ENABLE_TELEGRAM_NOTIFICATIONS", True)
    monkeypatch.setattr(
        notifier,
        "send_telegram_notification",
        lambda **kwargs: sent.append(kwargs) or True,
    )
    alert = make_alert(
        db_session, owner, condition=AlertCondition.GREATER_THAN, target_value=1
    )
    fake_market.set("AAPL", [100.0])

    summary = run(session_factory, fake_market)

    assert summary.triggered_ids == [alert.id]
    assert len(sent) == 1
    assert sent[0]["chat_id"] == "123456"
    assert "STOCKSENTINEL ALERT" in sent[0]["message"]
    assert "AAPL" in sent[0]["message"]
