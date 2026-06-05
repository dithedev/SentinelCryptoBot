"""make alert triggered_at timezone aware

Revision ID: 0060d6798583
Revises: bc4cc12712c9
Create Date: 2026-05-11 18:23:28.519057

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0060d6798583"
down_revision: str | None = "bc4cc12712c9"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Apply database changes."""
    op.alter_column(
        "alerts",
        "triggered_at",
        existing_type=sa.DateTime(timezone=False),
        type_=sa.DateTime(timezone=True),
        existing_nullable=True,
        postgresql_using="triggered_at AT TIME ZONE 'UTC'",
    )


def downgrade() -> None:
    """Rollback database changes."""
    op.alter_column(
        "alerts",
        "triggered_at",
        existing_type=sa.DateTime(timezone=True),
        type_=sa.DateTime(timezone=False),
        existing_nullable=True,
        postgresql_using="triggered_at AT TIME ZONE 'UTC'",
    )
