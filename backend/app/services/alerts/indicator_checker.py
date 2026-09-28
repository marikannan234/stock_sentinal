"""
Indicator alerts: SMA, EMA and RSI rules and the combined buy/sell signals.

Rules (unchanged from the original alert job):
  sma_above / sma_below        price > / < SMA(period)
  sma_crossover                price moved to the other side of SMA since the previous check
  ema_above / ema_below        price > / < EMA(period)
  ema_crossover                price moved to the other side of EMA since the previous check
  rsi_overbought / oversold    RSI(period) > 70 / < 30
  rsi_crossover                RSI rose through 30 or fell through 70 since the previous check
  strong_buy_signal            price > SMA and price > EMA and RSI < 30
  strong_sell_signal           price < SMA and price < EMA and RSI > 70

Crossover alerts store the previous observation (`last_price`, `last_rsi`,
`last_ema`) on every check; the first check only records it.

If there is not enough history for the requested period, the alert is
skipped with the reason; it never triggers on partial data.
"""

from __future__ import annotations

from typing import Callable

from app.models.alert import Alert, AlertType
from app.services.alerts import indicators
from app.services.alerts.base import CheckResult
from app.services.alerts.market_data import SymbolSnapshot

RSI_OVERBOUGHT = 70.0
RSI_OVERSOLD = 30.0


def _guard(check: Callable[[Alert, SymbolSnapshot], CheckResult]):
    def wrapper(alert: Alert, snapshot: SymbolSnapshot) -> CheckResult:
        try:
            return check(alert, snapshot)
        except indicators.InsufficientHistoryError as exc:
            return CheckResult.skip(f"insufficient history: {exc}")
    wrapper.__name__ = check.__name__
    return wrapper


def _moving_average(alert: Alert, snapshot: SymbolSnapshot) -> tuple[str, int, float]:
    if AlertType(alert.alert_type).value.startswith("sma"):
        return "SMA", alert.sma_period, indicators.sma(snapshot.closes, alert.sma_period)
    return "EMA", alert.ema_period, indicators.ema(snapshot.closes, alert.ema_period)


@_guard
def check_moving_average_level(alert: Alert, snapshot: SymbolSnapshot) -> CheckResult:
    """sma_above, sma_below, ema_above, ema_below."""
    name, period, average = _moving_average(alert, snapshot)
    price = snapshot.price
    above = AlertType(alert.alert_type).value.endswith("above")
    return CheckResult(
        triggered=price > average if above else price < average,
        description=f"{snapshot.symbol} price {price:.2f} {'>' if above else '<'} {name}({period}) {average:.2f}",
        indicators={f"{name.lower()}_value": average, f"{name.lower()}_period": period},
    )


@_guard
def check_moving_average_crossover(alert: Alert, snapshot: SymbolSnapshot) -> CheckResult:
    """sma_crossover, ema_crossover."""
    name, period, average = _moving_average(alert, snapshot)
    price = snapshot.price
    state: dict[str, float | None] = {"last_price": price}
    if name == "EMA":
        state["last_ema"] = average
    values = {f"{name.lower()}_value": average, f"{name.lower()}_period": period}

    previous = alert.last_price
    if previous is None:
        return CheckResult(
            description=f"{snapshot.symbol} {name}({period}) baseline recorded at price {price:.2f}",
            indicators=values,
            state=state,
        )

    now_above = price > average
    crossed = (previous > average) != now_above
    return CheckResult(
        triggered=crossed,
        description=(
            f"{snapshot.symbol} price {price:.2f} crossed {'above' if now_above else 'below'} "
            f"{name}({period}) {average:.2f} (previous price {previous:.2f})"
            if crossed
            else f"{snapshot.symbol} price {price:.2f} stayed {'above' if now_above else 'below'} {name}({period}) {average:.2f}"
        ),
        indicators=values,
        state=state,
    )


@_guard
def check_rsi_level(alert: Alert, snapshot: SymbolSnapshot) -> CheckResult:
    """rsi_overbought, rsi_oversold."""
    value = indicators.rsi(snapshot.closes, alert.rsi_period)
    overbought = AlertType(alert.alert_type) == AlertType.RSI_OVERBOUGHT
    return CheckResult(
        triggered=value > RSI_OVERBOUGHT if overbought else value < RSI_OVERSOLD,
        description=(
            f"{snapshot.symbol} RSI({alert.rsi_period}) {value:.2f} "
            + (f"> {RSI_OVERBOUGHT:g} (overbought)" if overbought else f"< {RSI_OVERSOLD:g} (oversold)")
        ),
        indicators={"rsi_value": value, "rsi_period": alert.rsi_period},
    )


@_guard
def check_rsi_crossover(alert: Alert, snapshot: SymbolSnapshot) -> CheckResult:
    value = indicators.rsi(snapshot.closes, alert.rsi_period)
    values = {"rsi_value": value, "rsi_period": alert.rsi_period}
    previous = alert.last_rsi
    state = {"last_rsi": value}
    if previous is None:
        return CheckResult(
            description=f"{snapshot.symbol} RSI({alert.rsi_period}) baseline recorded at {value:.2f}",
            indicators=values,
            state=state,
        )

    rose_through_oversold = previous <= RSI_OVERSOLD < value
    fell_through_overbought = previous >= RSI_OVERBOUGHT > value
    if rose_through_oversold:
        description = f"{snapshot.symbol} RSI({alert.rsi_period}) rose through {RSI_OVERSOLD:g}: {previous:.2f} -> {value:.2f}"
    elif fell_through_overbought:
        description = f"{snapshot.symbol} RSI({alert.rsi_period}) fell through {RSI_OVERBOUGHT:g}: {previous:.2f} -> {value:.2f}"
    else:
        description = f"{snapshot.symbol} RSI({alert.rsi_period}) {previous:.2f} -> {value:.2f}, no crossover"
    return CheckResult(
        triggered=rose_through_oversold or fell_through_overbought,
        description=description,
        indicators=values,
        state=state,
    )


@_guard
def check_combined_signal(alert: Alert, snapshot: SymbolSnapshot) -> CheckResult:
    """strong_buy_signal, strong_sell_signal."""
    price = snapshot.price
    sma_value = indicators.sma(snapshot.closes, alert.sma_period)
    ema_value = indicators.ema(snapshot.closes, alert.ema_period)
    rsi_value = indicators.rsi(snapshot.closes, alert.rsi_period)
    values = {
        "sma_value": sma_value, "sma_period": alert.sma_period,
        "ema_value": ema_value, "ema_period": alert.ema_period,
        "rsi_value": rsi_value, "rsi_period": alert.rsi_period,
    }
    if AlertType(alert.alert_type) == AlertType.STRONG_BUY_SIGNAL:
        triggered = price > sma_value and price > ema_value and rsi_value < RSI_OVERSOLD
        label, rule = "strong buy", f"price > SMA and > EMA, RSI < {RSI_OVERSOLD:g}"
    else:
        triggered = price < sma_value and price < ema_value and rsi_value > RSI_OVERBOUGHT
        label, rule = "strong sell", f"price < SMA and < EMA, RSI > {RSI_OVERBOUGHT:g}"
    return CheckResult(
        triggered=triggered,
        description=(
            f"{snapshot.symbol} {label} ({rule}): price {price:.2f}, SMA({alert.sma_period}) {sma_value:.2f}, "
            f"EMA({alert.ema_period}) {ema_value:.2f}, RSI({alert.rsi_period}) {rsi_value:.2f}"
        ),
        indicators=values,
    )
