"""Alert parameters per type: nullable target_value + CHECK constraint

Revision ID: 0007_alert_type_parameters
Revises: 0006_trading_cash_numeric
Create Date: 2026-09-25 23:30:00.000000

Indicator alerts (SMA/EMA/RSI and the combined signals) are defined by their
periods and have no target value, but alerts.target_value was NOT NULL, so
they could never be created. This revision:

1. makes alerts.target_value and alert_history.target_value nullable;
2. adds CHECK constraint ck_alerts_type_parameters so each alert type still
   must carry the parameters it is evaluated with (same rules as the API
   schema, see app.models.alert.ALERT_PARAMETERS_CHECK):
     target_value  for price, custom, percentage_change, volume_spike, crash
     condition     for price, custom
     sma_period    for sma_* and the combined signals
     ema_period    for ema_* and the combined signals
     rsi_period    for rsi_* and the combined signals
3. removes existing rows that violate those rules first. They cannot be
   evaluated (e.g. a custom alert without a condition raised an error on every
   check) and so never fired; the number removed is printed.

Downgrade drops the constraint and restores NOT NULL, setting missing target
values to 0 (ignored by indicator alerts) so no alert is lost.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "0007_alert_type_parameters"
down_revision: Union[str, None] = "0006_trading_cash_numeric"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


# Frozen copy of the rules at this revision (alert_type/condition hold enum names).
ALERT_PARAMETERS_CHECK = (
    "(alert_type NOT IN ('CRASH', 'CUSTOM', 'PERCENTAGE_CHANGE', 'PRICE', 'VOLUME_SPIKE') OR target_value IS NOT NULL)"
    " AND (alert_type NOT IN ('CUSTOM', 'PRICE') OR condition IS NOT NULL)"
    " AND (alert_type NOT IN ('SMA_ABOVE', 'SMA_BELOW', 'SMA_CROSSOVER', 'STRONG_BUY_SIGNAL', 'STRONG_SELL_SIGNAL') OR sma_period IS NOT NULL)"
    " AND (alert_type NOT IN ('EMA_ABOVE', 'EMA_BELOW', 'EMA_CROSSOVER', 'STRONG_BUY_SIGNAL', 'STRONG_SELL_SIGNAL') OR ema_period IS NOT NULL)"
    " AND (alert_type NOT IN ('RSI_CROSSOVER', 'RSI_OVERBOUGHT', 'RSI_OVERSOLD', 'STRONG_BUY_SIGNAL', 'STRONG_SELL_SIGNAL') OR rsi_period IS NOT NULL)"
)


def upgrade() -> None:
    op.alter_column("alerts", "target_value", existing_type=sa.Float(), nullable=True)
    op.alter_column("alert_history", "target_value", existing_type=sa.Float(), nullable=True)

    removed = op.get_bind().execute(
        sa.text(f"DELETE FROM alerts WHERE NOT ({ALERT_PARAMETERS_CHECK})")
    ).rowcount
    if removed:
        print(f"0007: removed {removed} alert(s) missing the parameters their type requires")

    op.create_check_constraint("ck_alerts_type_parameters", "alerts", ALERT_PARAMETERS_CHECK)


def downgrade() -> None:
    op.drop_constraint("ck_alerts_type_parameters", "alerts", type_="check")
    op.execute("UPDATE alert_history SET target_value = 0 WHERE target_value IS NULL")
    op.execute("UPDATE alerts SET target_value = 0 WHERE target_value IS NULL")
    op.alter_column("alert_history", "target_value", existing_type=sa.Float(), nullable=False)
    op.alter_column("alerts", "target_value", existing_type=sa.Float(), nullable=False)
