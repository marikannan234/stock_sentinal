"""Add alert tracking and history table for production enhancements

Revision ID: add_tracking_history
Revises: 25e65135c38c
Create Date: 2026-04-02 08:30:00.000000

This migration adds:
1. is_triggered column to alerts table (for cooldown management)
2. last_triggered_at column to alerts table (for cooldown tracking)
3. alert_history table (for complete audit trail of all triggers)
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = 'add_tracking_history'
down_revision: Union[str, None] = '25e65135c38c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add new columns and create alert_history table"""
    
    # Add is_triggered column to alerts table
    op.add_column(
        'alerts',
        sa.Column('is_triggered', sa.Boolean(), nullable=False, server_default=sa.false())
    )
    
    # Add last_triggered_at column to alerts table
    op.add_column(
        'alerts',
        sa.Column('last_triggered_at', sa.DateTime(), nullable=True)
    )
    
    # Create alert_history table for complete audit trail
    # NOTE: Indexes are defined in the AlertHistory model's __table_args__
    #       and will be created automatically by Alembic when this migration runs
    op.create_table(
        'alert_history',
        sa.Column('id', sa.Integer(), nullable=False, primary_key=True),
        sa.Column('alert_id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('triggered_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('stock_symbol', sa.String(length=16), nullable=False),
        sa.Column('alert_type', sa.String(length=50), nullable=False),
        sa.Column('price_at_trigger', sa.Float(), nullable=True),
        sa.Column('target_value', sa.Float(), nullable=False),
        sa.Column('condition', sa.String(length=50), nullable=True),
        sa.Column('message', sa.String(length=500), nullable=True),
        sa.Column('email_sent', sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column('email_sent_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['alert_id'], ['alerts.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
    )


def downgrade() -> None:
    """Remove new columns and drop alert_history table"""
    
    # Drop alert_history table (CASCADE will drop dependent indexes)
    op.drop_table('alert_history')
    
    # Remove columns from alerts table (CASCADE will drop dependent indexes)
    op.drop_column('alerts', 'last_triggered_at')
    op.drop_column('alerts', 'is_triggered')
