"""
Indicator math for alerts, computed from an already-fetched series.

The formulas are the ones app.services.indicator_service uses (and results are
rounded to 2 decimals the same way), but they take a list of closes instead
of fetching data themselves, so one download serves every alert on a symbol.
"""

from __future__ import annotations

from typing import Sequence


class InsufficientHistoryError(Exception):
    """Not enough bars to compute an indicator. The alert is not evaluated."""

    def __init__(self, indicator: str, period: int, required: int, available: int):
        super().__init__(
            f"{indicator}({period}) needs {required} daily closes, only {available} available"
        )
        self.indicator = indicator
        self.period = period
        self.required = required
        self.available = available


def sma(closes: Sequence[float], period: int) -> float:
    """Simple moving average of the last `period` closes."""
    _require(closes, "SMA", period, period)
    window = closes[-period:]
    return round(sum(window) / period, 2)


def ema(closes: Sequence[float], period: int) -> float:
    """Exponential moving average, seeded with the SMA of the first `period` closes."""
    _require(closes, "EMA", period, period)
    k = 2 / (period + 1)
    value = sum(closes[:period]) / period
    for price in closes[period:]:
        value = price * k + value * (1 - k)
    return round(value, 2)


def rsi(closes: Sequence[float], period: int) -> float:
    """Relative Strength Index with Wilder's smoothing."""
    _require(closes, "RSI", period, period + 1)
    deltas = [closes[i] - closes[i - 1] for i in range(1, len(closes))]
    gains = [d if d > 0 else 0.0 for d in deltas]
    losses = [-d if d < 0 else 0.0 for d in deltas]

    avg_gain = sum(gains[:period]) / period
    avg_loss = sum(losses[:period]) / period
    for i in range(period, len(gains)):
        avg_gain = (avg_gain * (period - 1) + gains[i]) / period
        avg_loss = (avg_loss * (period - 1) + losses[i]) / period

    if avg_loss == 0:
        value = 100.0 if avg_gain > 0 else 0.0
    else:
        value = 100 - (100 / (1 + avg_gain / avg_loss))
    return round(value, 2)


def _require(closes: Sequence[float], indicator: str, period: int, required: int) -> None:
    if period < 2:
        raise ValueError(f"{indicator} period must be at least 2, got {period}")
    if len(closes) < required:
        raise InsufficientHistoryError(indicator, period, required, len(closes))
