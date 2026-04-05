"""Make legacy trade_history.duration column nullable.

Revision ID: 0004_trade_history_duration
Revises: 0003_align_runtime_schema
Create Date: 2026-04-05 13:45:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "0004_trade_history_duration"
down_revision: Union[str, None] = "0003_align_runtime_schema"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.alter_column("trade_history", "duration", existing_type=sa.Float(), nullable=True)


def downgrade() -> None:
    op.alter_column("trade_history", "duration", existing_type=sa.Float(), nullable=False)
