"""Align stock catalog and prediction models with the deployed schema.

Revision ID: 0009_stock_prediction_schema
Revises: 0008_telegram_chat_id
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "0009_stock_prediction_schema"
down_revision: Union[str, None] = "0008_telegram_chat_id"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Migration 0003 introduced this column without the index declared by the model.
    op.create_index("ix_trade_history_created_at", "trade_history", ["created_at"], unique=False)
    # Preserve existing stock records while bringing the catalog names/fields
    # into line with the runtime model.
    op.alter_column("stocks", "symbol", new_column_name="ticker", existing_type=sa.String(length=10))
    op.alter_column("stocks", "ticker", existing_type=sa.String(length=10), type_=sa.String(length=16))
    op.drop_constraint("stocks_symbol_key", "stocks", type_="unique")
    op.drop_index("ix_stocks_symbol", table_name="stocks")
    op.alter_column("stocks", "sector", existing_type=sa.String(length=100), type_=sa.String(length=128))
    op.add_column("stocks", sa.Column("exchange", sa.String(length=64), nullable=True))
    op.add_column("stocks", sa.Column("currency", sa.String(length=8), nullable=True))
    op.execute("UPDATE stocks SET name = ticker WHERE name IS NULL OR btrim(name) = ''")
    op.alter_column("stocks", "name", existing_type=sa.String(length=255), nullable=False)
    op.create_unique_constraint("uq_stocks_ticker", "stocks", ["ticker"])
    op.create_index("ix_stocks_ticker", "stocks", ["ticker"], unique=False)

    # Retain historical timestamps and prediction data; derive the new metadata
    # from the original creation/prediction dates before making it mandatory.
    op.alter_column(
        "stock_predictions", "prediction_date",
        new_column_name="target_date",
        existing_type=sa.DateTime(),
    )
    op.add_column("stock_predictions", sa.Column("generated_at", sa.DateTime(), nullable=True))
    op.add_column("stock_predictions", sa.Column("horizon_days", sa.Integer(), nullable=True))
    op.add_column("stock_predictions", sa.Column("predicted_return", sa.Float(), nullable=True))
    op.add_column("stock_predictions", sa.Column("model_version", sa.String(length=64), nullable=True))
    op.add_column("stock_predictions", sa.Column("feature_snapshot", postgresql.JSONB(astext_type=sa.Text()), nullable=True))
    op.add_column("stock_predictions", sa.Column("actual_price", sa.Float(), nullable=True))
    op.add_column("stock_predictions", sa.Column("actual_return", sa.Float(), nullable=True))
    op.execute("UPDATE stock_predictions SET generated_at = created_at")
    op.execute(
        """UPDATE stock_predictions
           SET horizon_days = GREATEST(1, CEIL(EXTRACT(EPOCH FROM (target_date - created_at)) / 86400.0)::integer)"""
    )
    op.alter_column("stock_predictions", "generated_at", existing_type=sa.DateTime(), nullable=False)
    op.alter_column("stock_predictions", "horizon_days", existing_type=sa.Integer(), nullable=False)


def downgrade() -> None:
    op.drop_index("ix_trade_history_created_at", table_name="trade_history")
    op.drop_column("stock_predictions", "actual_return")
    op.drop_column("stock_predictions", "actual_price")
    op.drop_column("stock_predictions", "feature_snapshot")
    op.drop_column("stock_predictions", "model_version")
    op.drop_column("stock_predictions", "predicted_return")
    op.drop_column("stock_predictions", "horizon_days")
    op.drop_column("stock_predictions", "generated_at")
    op.alter_column(
        "stock_predictions", "target_date",
        new_column_name="prediction_date",
        existing_type=sa.DateTime(),
    )

    op.drop_index("ix_stocks_ticker", table_name="stocks")
    op.drop_constraint("uq_stocks_ticker", "stocks", type_="unique")
    op.alter_column("stocks", "name", existing_type=sa.String(length=255), nullable=True)
    op.drop_column("stocks", "currency")
    op.drop_column("stocks", "exchange")
    op.alter_column("stocks", "sector", existing_type=sa.String(length=128), type_=sa.String(length=100))
    op.alter_column("stocks", "ticker", existing_type=sa.String(length=16), type_=sa.String(length=10))
    op.alter_column("stocks", "ticker", new_column_name="symbol", existing_type=sa.String(length=10))
    op.create_unique_constraint("stocks_symbol_key", "stocks", ["symbol"])
    op.create_index("ix_stocks_symbol", "stocks", ["symbol"], unique=False)
