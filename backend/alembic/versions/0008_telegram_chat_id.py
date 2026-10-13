"""Add optional Telegram chat IDs for alert notifications.

Revision ID: 0008_telegram_chat_id
Revises: 0007_alert_type_parameters
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "0008_telegram_chat_id"
down_revision: Union[str, None] = "0007_alert_type_parameters"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("users", sa.Column("telegram_chat_id", sa.String(length=64), nullable=True))
    op.create_index("ix_users_telegram_chat_id", "users", ["telegram_chat_id"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_users_telegram_chat_id", table_name="users")
    op.drop_column("users", "telegram_chat_id")
