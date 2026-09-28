"""Shared types for alert checkers."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable

from app.models.alert import Alert
from app.services.alerts.market_data import SymbolSnapshot


@dataclass
class CheckResult:
    """Outcome of evaluating one alert against a symbol snapshot."""

    triggered: bool = False
    # Human-readable description of the rule and the observed values; used in
    # alert history and notifications.
    description: str = ""
    # Indicator values/periods for notifications (e.g. {"sma_value": 188.4, "sma_period": 50}).
    indicators: dict[str, float | int] = field(default_factory=dict)
    # Alert attributes to persist after this check (e.g. {"last_price": 190.1}).
    state: dict[str, float | None] = field(default_factory=dict)
    # Set when the alert could not be evaluated this run (never triggers).
    skipped: str | None = None

    @classmethod
    def skip(cls, reason: str, state: dict[str, float | None] | None = None) -> "CheckResult":
        return cls(triggered=False, skipped=reason, state=state or {})


Checker = Callable[[Alert, SymbolSnapshot], CheckResult]
