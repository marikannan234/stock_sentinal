"""Align runtime schema with current SQLAlchemy models.

Revision ID: 0003_align_runtime_schema
Revises: 0002_add_trading_tables
Create Date: 2026-04-05 13:30:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "0003_align_runtime_schema"
down_revision: Union[str, None] = "0002_add_trading_tables"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "watchlists",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("ticker", sa.String(length=16), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", "ticker", name="uq_watchlist_user_ticker"),
    )
    op.create_index("ix_watchlists_ticker", "watchlists", ["ticker"], unique=False)

    op.create_table(
        "portfolios",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("ticker", sa.String(length=16), nullable=False),
        sa.Column("quantity", sa.Float(), nullable=False),
        sa.Column("average_price", sa.Float(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", "ticker", name="uq_portfolio_user_ticker"),
    )
    op.create_index("ix_portfolios_ticker", "portfolios", ["ticker"], unique=False)

    op.add_column("support_tickets", sa.Column("resolved_at", sa.DateTime(), nullable=True))

    op.add_column("trades", sa.Column("notes", sa.Text(), nullable=True))
    op.add_column("trades", sa.Column("executed_at", sa.DateTime(), nullable=True))

    op.add_column("trade_history", sa.Column("trade_id", sa.Integer(), nullable=True))
    op.add_column("trade_history", sa.Column("profit_loss_percent", sa.Float(), nullable=True))
    op.add_column("trade_history", sa.Column("duration_minutes", sa.Integer(), nullable=True))
    op.add_column("trade_history", sa.Column("notes", sa.Text(), nullable=True))
    op.add_column(
        "trade_history",
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
    )
    op.create_foreign_key(
        "fk_trade_history_trade_id_trades",
        "trade_history",
        "trades",
        ["trade_id"],
        ["id"],
        ondelete="SET NULL",
    )

    op.execute("UPDATE trade_history SET duration_minutes = CAST(duration AS INTEGER) WHERE duration_minutes IS NULL")


def downgrade() -> None:
    op.drop_constraint("fk_trade_history_trade_id_trades", "trade_history", type_="foreignkey")
    op.drop_column("trade_history", "created_at")
    op.drop_column("trade_history", "notes")
    op.drop_column("trade_history", "duration_minutes")
    op.drop_column("trade_history", "profit_loss_percent")
    op.drop_column("trade_history", "trade_id")

    op.drop_column("trades", "executed_at")
    op.drop_column("trades", "notes")

    op.drop_column("support_tickets", "resolved_at")

    op.drop_index("ix_portfolios_ticker", table_name="portfolios")
    op.drop_table("portfolios")

    op.drop_index("ix_watchlists_ticker", table_name="watchlists")
    op.drop_table("watchlists")
