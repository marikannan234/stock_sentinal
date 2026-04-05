"""Add trading, user settings, and support tables

Revision ID: 0002_add_trading_tables
Revises: 0001_initial_schema
Create Date: 2026-04-02 19:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "0002_add_trading_tables"
down_revision: Union[str, None] = "0001_initial_schema"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create user_settings table
    op.create_table(
        'user_settings',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('email_notifications', sa.Boolean(), server_default=sa.text('true'), nullable=False),
        sa.Column('dark_mode', sa.Boolean(), server_default=sa.text('true'), nullable=False),
        sa.Column('preferred_currency', sa.String(10), server_default='USD', nullable=False),
        sa.Column('two_factor_enabled', sa.Boolean(), server_default=sa.text('false'), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id'),
        sa.Index('ix_user_settings_user_id', 'user_id')
    )

    # Create support_tickets table
    op.create_table(
        'support_tickets',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('subject', sa.String(255), nullable=False),
        sa.Column('message', sa.Text(), nullable=False),
        sa.Column('status', sa.String(50), server_default='open', nullable=False),
        sa.Column('priority', sa.String(50), server_default='normal', nullable=False),
        sa.Column('response', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.Index('ix_support_tickets_user_id', 'user_id'),
        sa.Index('ix_support_tickets_status', 'status'),
        sa.Index('ix_support_tickets_created_at', 'created_at')
    )

    # Create trades table
    op.create_table(
        'trades',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('symbol', sa.String(10), nullable=False),
        sa.Column('quantity', sa.Float(), nullable=False),
        sa.Column('entry_price', sa.Float(), nullable=False),
        sa.Column('current_price', sa.Float(), nullable=False),
        sa.Column('trade_type', sa.String(20), nullable=False),
        sa.Column('status', sa.String(20), server_default='open', nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.Index('ix_trades_user_id', 'user_id'),
        sa.Index('ix_trades_symbol', 'symbol'),
        sa.Index('ix_trades_status', 'status'),
        sa.Index('ix_trades_created_at', 'created_at')
    )

    # Create trade_history table
    op.create_table(
        'trade_history',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('symbol', sa.String(10), nullable=False),
        sa.Column('quantity', sa.Float(), nullable=False),
        sa.Column('entry_price', sa.Float(), nullable=False),
        sa.Column('exit_price', sa.Float(), nullable=False),
        sa.Column('profit_loss', sa.Float(), nullable=False),
        sa.Column('duration', sa.Float(), nullable=False),
        sa.Column('trade_type', sa.String(20), nullable=False),
        sa.Column('closed_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.Index('ix_trade_history_user_id', 'user_id'),
        sa.Index('ix_trade_history_symbol', 'symbol'),
        sa.Index('ix_trade_history_closed_at', 'closed_at')
    )


def downgrade() -> None:
    op.drop_table('trade_history')
    op.drop_table('trades')
    op.drop_table('support_tickets')
    op.drop_table('user_settings')
