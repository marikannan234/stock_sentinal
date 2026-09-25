"""Paper-trading cash balance, Numeric money columns, lot/position reconciliation

Revision ID: 0006_trading_cash_numeric
Revises: 0005_add_whatsapp_phone
Create Date: 2026-09-25 22:00:00.000000

1. users.cash_balance NUMERIC(18,2); existing users get PAPER_TRADING_STARTING_CASH.
2. Trading/portfolio float columns become NUMERIC:
   quantities NUMERIC(20,8), prices NUMERIC(18,6), profit_loss NUMERIC(18,2).
3. trades.symbol / trade_history.symbol widened 10 -> 20 to match the models
   (longer symbols such as BINANCE:BTCUSDT failed with a DB error).
4. Reconcile trades with portfolios. Open trades are now the source of truth
   for positions, but before this revision no trade ever changed a portfolio
   (the trade-type comparison never matched) and holdings were only created
   through POST /portfolio. So:
   - every trade still OPEN/PENDING is marked CANCELLED (it never held shares);
   - every portfolio row becomes one OPEN lot at its average price, so the
     holding stays exactly as it was and can be sold normally.

Downgrade reverts the column changes. The reconciliation in step 4 is not
reversed.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

from app.config import settings


revision: str = "0006_trading_cash_numeric"
down_revision: Union[str, None] = "0005_add_whatsapp_phone"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


QUANTITY = sa.Numeric(20, 8)
PRICE = sa.Numeric(18, 6)
MONEY = sa.Numeric(18, 2)

_NUMERIC_COLUMNS = [
    ("portfolios", "quantity", QUANTITY),
    ("portfolios", "average_price", PRICE),
    ("trades", "quantity", QUANTITY),
    ("trades", "entry_price", PRICE),
    ("trades", "current_price", PRICE),
    ("trade_history", "quantity", QUANTITY),
    ("trade_history", "entry_price", PRICE),
    ("trade_history", "exit_price", PRICE),
    ("trade_history", "profit_loss", MONEY),
]


def upgrade() -> None:
    # 1. Cash balance
    op.add_column("users", sa.Column("cash_balance", MONEY, nullable=True))
    op.execute(
        sa.text("UPDATE users SET cash_balance = :cash").bindparams(
            cash=settings.PAPER_TRADING_STARTING_CASH
        )
    )
    op.alter_column("users", "cash_balance", existing_type=MONEY, nullable=False)

    # 2. Money / quantity precision
    for table, column, new_type in _NUMERIC_COLUMNS:
        op.alter_column(
            table,
            column,
            existing_type=sa.Float(),
            type_=new_type,
            postgresql_using=f"ROUND({column}::numeric, {new_type.scale})",
        )

    # 3. Symbol length
    for table in ("trades", "trade_history"):
        op.alter_column(table, "symbol", existing_type=sa.String(10), type_=sa.String(20))

    # 4. Reconcile trades with portfolios
    op.execute(
        """
        UPDATE trades
        SET status = 'CANCELLED',
            updated_at = CURRENT_TIMESTAMP,
            notes = TRIM(COALESCE(notes, '') || ' [Cancelled by migration 0006: this trade never updated the portfolio]')
        WHERE UPPER(status) IN ('OPEN', 'PENDING')
        """
    )
    op.execute("DELETE FROM portfolios WHERE quantity = 0")
    op.execute(
        """
        INSERT INTO trades
            (user_id, symbol, quantity, entry_price, current_price, trade_type,
             status, notes, created_at, updated_at, executed_at)
        SELECT user_id, ticker, ABS(quantity), average_price, average_price,
               CASE WHEN quantity > 0 THEN 'BUY' ELSE 'SHORT' END,
               'OPEN', 'Opening position carried over from portfolio (migration 0006)',
               created_at, CURRENT_TIMESTAMP, created_at
        FROM portfolios
        """
    )


def downgrade() -> None:
    for table in ("trades", "trade_history"):
        op.alter_column(table, "symbol", existing_type=sa.String(20), type_=sa.String(10))

    for table, column, new_type in _NUMERIC_COLUMNS:
        op.alter_column(
            table,
            column,
            existing_type=new_type,
            type_=sa.Float(),
            postgresql_using=f"{column}::double precision",
        )

    op.drop_column("users", "cash_balance")
