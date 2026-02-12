"""Initial models for StockSentinel.

Revision ID: 0001_initial
Revises: 
Create Date: 2026-02-11 00:00:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "0001_initial"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("full_name", sa.String(length=255), nullable=True),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_users_id", "users", ["id"])
    op.create_index("ix_users_email", "users", ["email"], unique=True)

    op.create_table(
        "stocks",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("ticker", sa.String(length=16), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("exchange", sa.String(length=64), nullable=True),
        sa.Column("sector", sa.String(length=128), nullable=True),
        sa.Column("currency", sa.String(length=8), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.UniqueConstraint("ticker", name="uq_stocks_ticker"),
    )
    op.create_index("ix_stocks_id", "stocks", ["id"])
    op.create_index("ix_stocks_ticker", "stocks", ["ticker"])

    op.create_table(
        "watchlists",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_watchlists_id", "watchlists", ["id"])

    op.create_table(
        "portfolios",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("base_currency", sa.String(length=8), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_portfolios_id", "portfolios", ["id"])

    op.create_table(
        "watchlist_items",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("watchlist_id", sa.Integer(), sa.ForeignKey("watchlists.id", ondelete="CASCADE"), nullable=False),
        sa.Column("stock_id", sa.Integer(), sa.ForeignKey("stocks.id", ondelete="CASCADE"), nullable=False),
        sa.Column("added_at", sa.DateTime(), nullable=False),
        sa.UniqueConstraint("watchlist_id", "stock_id", name="uq_watchlist_stock"),
    )
    op.create_index("ix_watchlist_items_id", "watchlist_items", ["id"])

    op.create_table(
        "portfolio_positions",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("portfolio_id", sa.Integer(), sa.ForeignKey("portfolios.id", ondelete="CASCADE"), nullable=False),
        sa.Column("stock_id", sa.Integer(), sa.ForeignKey("stocks.id", ondelete="CASCADE"), nullable=False),
        sa.Column("quantity", sa.Float(), nullable=False),
        sa.Column("average_price", sa.Float(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.UniqueConstraint("portfolio_id", "stock_id", name="uq_portfolio_stock"),
    )
    op.create_index("ix_portfolio_positions_id", "portfolio_positions", ["id"])

    op.create_table(
        "sentiment_records",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("stock_id", sa.Integer(), sa.ForeignKey("stocks.id", ondelete="CASCADE"), nullable=False),
        sa.Column("source", sa.String(length=32), nullable=False),
        sa.Column("window_start", sa.DateTime(), nullable=False),
        sa.Column("window_end", sa.DateTime(), nullable=False),
        sa.Column("sentiment_score", sa.Float(), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=True),
        sa.Column("mentions_count", sa.Integer(), nullable=True),
        sa.Column("raw_sample_count", sa.Integer(), nullable=True),
        sa.Column("extra_data", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_sentiment_records_id", "sentiment_records", ["id"])
    op.create_index("ix_sentiment_records_stock_id", "sentiment_records", ["stock_id"])
    op.create_index("ix_sentiment_records_window_start", "sentiment_records", ["window_start"])

    op.create_table(
        "stock_predictions",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("stock_id", sa.Integer(), sa.ForeignKey("stocks.id", ondelete="CASCADE"), nullable=False),
        sa.Column("generated_at", sa.DateTime(), nullable=False),
        sa.Column("horizon_days", sa.Integer(), nullable=False),
        sa.Column("target_date", sa.DateTime(), nullable=False),
        sa.Column("predicted_price", sa.Float(), nullable=False),
        sa.Column("predicted_return", sa.Float(), nullable=True),
        sa.Column("confidence", sa.Float(), nullable=True),
        sa.Column("model_version", sa.String(length=64), nullable=True),
        sa.Column("feature_snapshot", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("actual_price", sa.Float(), nullable=True),
        sa.Column("actual_return", sa.Float(), nullable=True),
    )
    op.create_index("ix_stock_predictions_id", "stock_predictions", ["id"])
    op.create_index("ix_stock_predictions_stock_id", "stock_predictions", ["stock_id"])


def downgrade() -> None:
    op.drop_index("ix_stock_predictions_stock_id", table_name="stock_predictions")
    op.drop_index("ix_stock_predictions_id", table_name="stock_predictions")
    op.drop_table("stock_predictions")

    op.drop_index("ix_sentiment_records_window_start", table_name="sentiment_records")
    op.drop_index("ix_sentiment_records_stock_id", table_name="sentiment_records")
    op.drop_index("ix_sentiment_records_id", table_name="sentiment_records")
    op.drop_table("sentiment_records")

    op.drop_index("ix_portfolio_positions_id", table_name="portfolio_positions")
    op.drop_table("portfolio_positions")

    op.drop_index("ix_watchlist_items_id", table_name="watchlist_items")
    op.drop_table("watchlist_items")

    op.drop_index("ix_portfolios_id", table_name="portfolios")
    op.drop_table("portfolios")

    op.drop_index("ix_watchlists_id", table_name="watchlists")
    op.drop_table("watchlists")

    op.drop_index("ix_stocks_ticker", table_name="stocks")
    op.drop_index("ix_stocks_id", table_name="stocks")
    op.drop_table("stocks")

    op.drop_index("ix_users_email", table_name="users")
    op.drop_index("ix_users_id", table_name="users")
    op.drop_table("users")

