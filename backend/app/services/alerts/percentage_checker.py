"""PERCENTAGE_CHANGE alerts: price moved at least N% (up or down).

The move is measured from the reference price stored in `alert.last_price`,
recorded on the alert's first check after it is created or re-enabled. The
reference is not overwritten afterwards, so "5%" means a 5% move since the
alert started watching.
"""

from __future__ import annotations

from app.models.alert import Alert
from app.services.alerts.base import CheckResult
from app.services.alerts.market_data import SymbolSnapshot

REFERENCE_RECORDED = "reference price recorded; the move is measured from the next check"


def percent_move(alert: Alert, snapshot: SymbolSnapshot) -> tuple[float, float] | CheckResult:
    """(reference price, % change) or a skip result that records the reference."""
    reference = alert.last_price
    if reference is None or reference <= 0:
        return CheckResult.skip(REFERENCE_RECORDED, state={"last_price": snapshot.price})
    return reference, (snapshot.price - reference) / reference * 100


def check_percentage_change(alert: Alert, snapshot: SymbolSnapshot) -> CheckResult:
    move = percent_move(alert, snapshot)
    if isinstance(move, CheckResult):
        return move
    reference, change = move
    return CheckResult(
        triggered=abs(change) >= alert.target_value,
        description=(
            f"{snapshot.symbol} moved {change:+.2f}% from {reference:.2f} to {snapshot.price:.2f} "
            f"(threshold {alert.target_value:g}%)"
        ),
    )
