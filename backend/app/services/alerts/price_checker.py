"""PRICE alerts: current price compared with a target using >, <, >= or <=."""

from __future__ import annotations

import operator

from app.models.alert import Alert, AlertCondition
from app.services.alerts.base import CheckResult
from app.services.alerts.market_data import SymbolSnapshot

_OPERATORS = {
    AlertCondition.GREATER_THAN: operator.gt,
    AlertCondition.LESS_THAN: operator.lt,
    AlertCondition.GREATER_THAN_OR_EQUAL: operator.ge,
    AlertCondition.LESS_THAN_OR_EQUAL: operator.le,
}


def check_price(alert: Alert, snapshot: SymbolSnapshot) -> CheckResult:
    compare = _OPERATORS.get(alert.condition)
    if compare is None or alert.target_value is None:
        return CheckResult.skip("price rule needs a condition (>, <, >=, <=) and a target value")

    price = snapshot.price
    return CheckResult(
        triggered=compare(price, alert.target_value),
        description=(
            f"{snapshot.symbol} price {price:.2f} {alert.condition.value} {alert.target_value:.2f}"
        ),
    )
