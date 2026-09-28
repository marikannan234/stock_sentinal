"""CUSTOM alerts.

CUSTOM is a placeholder type that has always been evaluated exactly like a
PRICE rule (condition + target_value); that behavior is kept.
"""

from app.services.alerts.price_checker import check_price as check_custom

__all__ = ["check_custom"]
