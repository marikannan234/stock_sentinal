"""Add whatsapp_phone column to users table

Revision ID: 0005_add_whatsapp_phone
Revises: 0004_trade_history_duration
Create Date: 2026-04-10 12:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '0005_add_whatsapp_phone'
down_revision: Union[str, None] = '0004_trade_history_duration'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add whatsapp_phone column to users table
    op.add_column('users', sa.Column('whatsapp_phone', sa.String(length=20), nullable=True))
    
    # Create unique index on whatsapp_phone to allow duplicates only as NULL
    op.create_index(op.f('ix_users_whatsapp_phone'), 'users', ['whatsapp_phone'], unique=True)


def downgrade() -> None:
    # Drop the index and column
    op.drop_index(op.f('ix_users_whatsapp_phone'), table_name='users')
    op.drop_column('users', 'whatsapp_phone')
