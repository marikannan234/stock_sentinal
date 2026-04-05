"""initial schema - create all tables

Revision ID: 0001_initial_schema
Revises: 
Create Date: 2026-04-02 18:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "0001_initial_schema"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create users table
    op.create_table(
        'users',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('email', sa.String(255), nullable=False),
        sa.Column('full_name', sa.String(255), nullable=True),
        sa.Column('password_hash', sa.String(255), nullable=False),
        sa.Column('is_active', sa.Boolean(), server_default=sa.text('true'), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('email'),
        sa.Index('ix_users_email', 'email')
    )

    # Create stocks table
    op.create_table(
        'stocks',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('symbol', sa.String(10), nullable=False),
        sa.Column('name', sa.String(255), nullable=True),
        sa.Column('sector', sa.String(100), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('symbol'),
        sa.Index('ix_stocks_symbol', 'symbol')
    )

    # Create watchlist table
    op.create_table(
        'watchlist',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('stock_id', sa.Integer(), nullable=False),
        sa.Column('added_at', sa.DateTime(), nullable=False),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.ForeignKeyConstraint(['stock_id'], ['stocks.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.Index('ix_watchlist_user_id', 'user_id'),
        sa.Index('ix_watchlist_stock_id', 'stock_id')
    )

    # Create portfolio table
    op.create_table(
        'portfolio',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('stock_id', sa.Integer(), nullable=False),
        sa.Column('quantity', sa.Float(), nullable=False),
        sa.Column('average_cost', sa.Float(), nullable=False),
        sa.Column('added_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.ForeignKeyConstraint(['stock_id'], ['stocks.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.Index('ix_portfolio_user_id', 'user_id'),
        sa.Index('ix_portfolio_stock_id', 'stock_id')
    )

    # Create sentiment_records table
    op.create_table(
        'sentiment_records',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('stock_id', sa.Integer(), nullable=False),
        sa.Column('source', sa.String(32), nullable=False),
        sa.Column('window_start', sa.DateTime(), nullable=False),
        sa.Column('window_end', sa.DateTime(), nullable=False),
        sa.Column('sentiment_score', sa.Float(), nullable=False),
        sa.Column('confidence', sa.Float(), nullable=True),
        sa.Column('mentions_count', sa.Integer(), nullable=True),
        sa.Column('raw_sample_count', sa.Integer(), nullable=True),
        sa.Column('extra_data', postgresql.JSONB(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['stock_id'], ['stocks.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.Index('ix_sentiment_records_stock_id', 'stock_id'),
        sa.Index('ix_sentiment_records_created_at', 'created_at')
    )

    # Create stock_predictions table
    op.create_table(
        'stock_predictions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('stock_id', sa.Integer(), nullable=False),
        sa.Column('predicted_price', sa.Float(), nullable=False),
        sa.Column('confidence', sa.Float(), nullable=False),
        sa.Column('prediction_date', sa.DateTime(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['stock_id'], ['stocks.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.Index('ix_stock_predictions_stock_id', 'stock_id'),
        sa.Index('ix_stock_predictions_created_at', 'created_at')
    )

    # Create alerts table
    op.create_table(
        'alerts',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('stock_symbol', sa.String(16), nullable=False),
        sa.Column('condition', sa.String(50), nullable=True),
        sa.Column('target_value', sa.Float(), nullable=False),
        sa.Column('alert_type', sa.String(50), nullable=False),
        sa.Column('last_price', sa.Float(), nullable=True),
        sa.Column('sma_period', sa.Integer(), nullable=True),
        sa.Column('ema_period', sa.Integer(), nullable=True),
        sa.Column('last_ema', sa.Float(), nullable=True),
        sa.Column('rsi_period', sa.Integer(), nullable=True),
        sa.Column('last_rsi', sa.Float(), nullable=True),
        sa.Column('is_active', sa.Boolean(), server_default=sa.text('true'), nullable=False),
        sa.Column('is_triggered', sa.Boolean(), server_default=sa.text('false'), nullable=False),
        sa.Column('last_triggered_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('triggered_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id', 'stock_symbol', 'alert_type', 'condition', 'target_value', name='uq_alerts_user_stock_type_condition'),
        sa.Index('ix_alerts_user_id', 'user_id'),
        sa.Index('ix_alerts_alert_type', 'alert_type'),
        sa.Index('ix_alerts_is_triggered', 'is_triggered'),
        sa.Index('ix_alerts_created_at', 'created_at'),
        sa.Index('ix_alerts_user_id_active', 'user_id', 'is_active'),
        sa.Index('ix_alerts_user_stock', 'user_id', 'stock_symbol')
    )

    # Create alert_history table
    op.create_table(
        'alert_history',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('alert_id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('triggered_at', sa.DateTime(), nullable=False),
        sa.Column('stock_symbol', sa.String(16), nullable=False),
        sa.Column('alert_type', sa.String(50), nullable=False),
        sa.Column('price_at_trigger', sa.Float(), nullable=True),
        sa.Column('target_value', sa.Float(), nullable=False),
        sa.Column('condition', sa.String(50), nullable=True),
        sa.Column('message', sa.String(500), nullable=False),
        sa.Column('email_sent', sa.Boolean(), server_default=sa.text('false'), nullable=False),
        sa.Column('email_sent_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['alert_id'], ['alerts.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.Index('ix_alert_history_alert_id', 'alert_id'),
        sa.Index('ix_alert_history_user_id', 'user_id'),
        sa.Index('ix_alert_history_triggered_at', 'triggered_at'),
        sa.Index('ix_alert_history_alert_user', 'alert_id', 'user_id')
    )


def downgrade() -> None:
    # Drop tables in reverse order (respecting foreign keys)
    op.drop_table('alert_history')
    op.drop_table('alerts')
    op.drop_table('stock_predictions')
    op.drop_table('sentiment_records')
    op.drop_table('portfolio')
    op.drop_table('watchlist')
    op.drop_table('stocks')
    op.drop_table('users')
