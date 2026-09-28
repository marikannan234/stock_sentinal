"""VOLUME_SPIKE alerts: latest volume above N x the average of the previous 20 days."""

from __future__ import annotations

from app.models.alert import Alert
from app.services.alerts.base import CheckResult
from app.services.alerts.market_data import VOLUME_AVERAGE_BARS, SymbolSnapshot


def check_volume_spike(alert: Alert, snapshot: SymbolSnapshot) -> CheckResult:
    current = snapshot.current_volume
    average = snapshot.average_volume
    if current is None or average is None or average <= 0:
        return CheckResult.skip("volume data unavailable")

    ratio = current / average
    return CheckResult(
        triggered=current > average * alert.target_value,
        description=(
            f"{snapshot.symbol} volume {current:,.0f} is {ratio:.2f}x its "
            f"{VOLUME_AVERAGE_BARS}-day average {average:,.0f} (threshold {alert.target_value:g}x)"
        ),
    )
