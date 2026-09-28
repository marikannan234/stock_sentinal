"""CRASH alerts: price dropped at least N% from the alert's reference price.

Same reference price as PERCENTAGE_CHANGE (see percentage_checker), but only
downward moves count.
"""

from __future__ import annotations

from app.models.alert import Alert
from app.services.alerts.base import CheckResult
from app.services.alerts.market_data import SymbolSnapshot
from app.services.alerts.percentage_checker import percent_move


def check_crash(alert: Alert, snapshot: SymbolSnapshot) -> CheckResult:
    move = percent_move(alert, snapshot)
    if isinstance(move, CheckResult):
        return move
    reference, change = move
    return CheckResult(
        triggered=change <= -alert.target_value,
        description=(
            f"{snapshot.symbol} changed {change:+.2f}% from {reference:.2f} to {snapshot.price:.2f} "
            f"(crash threshold -{alert.target_value:g}%)"
        ),
    )
