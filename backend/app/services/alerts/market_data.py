"""
Market data for the alert job: one daily-history fetch per symbol per run.

All alerts on a symbol are evaluated against the same `SymbolSnapshot`, so a
run with three AAPL alerts and two MSFT alerts makes two requests.

The lookback is sized to the most demanding alert on the symbol (see
`bars_needed`): about a month of daily bars for price/volume alerts, and
enough history for the longest indicator period otherwise (e.g. ~200
trading days for SMA-200).
"""

from __future__ import annotations

import contextlib
import io
import logging
import math
from dataclasses import dataclass
from datetime import date, timedelta
from typing import Protocol

import yfinance as yf

from app.models.alert import EMA_TYPES, RSI_TYPES, SMA_TYPES, Alert, AlertType

logger = logging.getLogger(__name__)

# Bars used for the average-volume baseline (the bars before the latest one).
VOLUME_AVERAGE_BARS = 20
# Minimum history requested for any symbol (covers the volume baseline).
MIN_BARS = VOLUME_AVERAGE_BARS + 1
# EMA and Wilder's RSI depend on their starting point; ~3x the period of
# history makes the result converge on the textbook value.
CONVERGENCE_FACTOR = 3
# Calendar days per trading day (weekends + holidays), with some margin.
CALENDAR_DAYS_PER_BAR = 1.5
REQUEST_TIMEOUT_SECONDS = 10


class MarketDataError(Exception):
    """No usable market data for a symbol; its alerts are skipped this run."""


@dataclass(frozen=True)
class SymbolSnapshot:
    symbol: str
    closes: tuple[float, ...]   # daily closes, oldest first; last = current price
    volumes: tuple[float, ...]  # daily volumes aligned with closes

    @property
    def price(self) -> float:
        return self.closes[-1]

    @property
    def current_volume(self) -> float | None:
        volume = self.volumes[-1] if self.volumes else None
        return volume if volume is not None and math.isfinite(volume) else None

    @property
    def average_volume(self) -> float | None:
        previous = [v for v in self.volumes[-(VOLUME_AVERAGE_BARS + 1):-1] if math.isfinite(v)]
        return sum(previous) / len(previous) if previous else None


class SnapshotFetcher(Protocol):
    def __call__(self, symbol: str, bars: int) -> SymbolSnapshot: ...


def bars_needed(alert: Alert) -> int:
    """Daily bars of history this alert needs to be evaluated reliably."""
    alert_type = AlertType(alert.alert_type)
    needed = MIN_BARS
    if alert_type in SMA_TYPES and alert.sma_period:
        needed = max(needed, alert.sma_period + 1)
    if alert_type in EMA_TYPES and alert.ema_period:
        needed = max(needed, CONVERGENCE_FACTOR * alert.ema_period)
    if alert_type in RSI_TYPES and alert.rsi_period:
        needed = max(needed, CONVERGENCE_FACTOR * alert.rsi_period + 1)
    # Combined signals are members of all three sets above.
    return needed


def fetch_snapshot(symbol: str, bars: int) -> SymbolSnapshot:
    """Fetch ~`bars` daily bars for `symbol` in one request.

    Raises MarketDataError if nothing usable comes back. A missing, zero,
    negative or NaN latest price is an error: no substitute price is used.
    """
    start = date.today() - timedelta(days=math.ceil(bars * CALENDAR_DAYS_PER_BAR) + 7)
    try:
        with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            history = yf.Ticker(symbol).history(
                start=start.isoformat(),
                interval="1d",
                timeout=REQUEST_TIMEOUT_SECONDS,
            )
    except Exception as exc:
        raise MarketDataError(f"request failed ({type(exc).__name__})") from exc

    return snapshot_from_history(symbol, history)


def snapshot_from_history(symbol: str, history) -> SymbolSnapshot:
    """Build a snapshot from a yfinance history DataFrame (Close/Volume columns)."""
    if history is None or getattr(history, "empty", True) or "Close" not in history.columns:
        raise MarketDataError("no price history returned")

    closes: list[float] = []
    volumes: list[float] = []
    has_volume = "Volume" in history.columns
    for index in range(len(history)):
        close = _as_float(history["Close"].iloc[index])
        if close is None or close <= 0:
            continue  # drop incomplete / bad bars rather than invent a price
        closes.append(close)
        volume = _as_float(history["Volume"].iloc[index]) if has_volume else None
        volumes.append(volume if volume is not None else math.nan)

    if not closes:
        raise MarketDataError("no valid prices in history")

    latest = _as_float(history["Close"].iloc[-1])
    if latest is None or latest <= 0:
        raise MarketDataError("latest price missing or not positive")

    return SymbolSnapshot(symbol=symbol, closes=tuple(closes), volumes=tuple(volumes))


def _as_float(value) -> float | None:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return number if math.isfinite(number) else None
