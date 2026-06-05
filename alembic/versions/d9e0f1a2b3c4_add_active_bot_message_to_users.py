"""add active bot message to users

Revision ID: d9e0f1a2b3c4
Revises: c8f1a2b3d4e5
Create Date: 2026-05-23 13:45:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "d9e0f1a2b3c4"
down_revision: str | None = "c8f1a2b3d4e5"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Apply database changes."""
    op.add_column(
        "users",
        sa.Column("active_bot_chat_id", sa.BigInteger(), nullable=True),
    )
    op.add_column(
        "users",
        sa.Column("active_bot_message_id", sa.BigInteger(), nullable=True),
    )


def downgrade() -> None:
    """Revert database changes."""
    op.drop_column("users", "active_bot_message_id")
    op.drop_column("users", "active_bot_chat_id")
