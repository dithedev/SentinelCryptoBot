"""add whale notification deliveries

Revision ID: c8f1a2b3d4e5
Revises: 25b904257766
Create Date: 2026-05-20 19:30:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "c8f1a2b3d4e5"
down_revision: str | None = "25b904257766"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Apply database changes."""
    op.create_table(
        "whale_notification_deliveries",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("whale_event_id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column(
            "status",
            sa.Enum(
                "pending",
                "sent",
                "failed",
                name="whale_notification_delivery_status",
            ),
            nullable=False,
        ),
        sa.Column("attempts", sa.Integer(), nullable=False),
        sa.Column("last_error", sa.String(length=500), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            name=op.f("fk_whale_notification_deliveries_user_id_users"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["whale_event_id"],
            ["whale_events.id"],
            name=op.f(
                "fk_whale_notification_deliveries_whale_event_id_whale_events",
            ),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint(
            "id",
            name=op.f("pk_whale_notification_deliveries"),
        ),
    )
    op.create_index(
        "uq_whale_notification_deliveries_event_user",
        "whale_notification_deliveries",
        ["whale_event_id", "user_id"],
        unique=True,
    )
    op.create_index(
        op.f("ix_whale_notification_deliveries_user_id"),
        "whale_notification_deliveries",
        ["user_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_whale_notification_deliveries_whale_event_id"),
        "whale_notification_deliveries",
        ["whale_event_id"],
        unique=False,
    )


def downgrade() -> None:
    """Revert database changes."""
    op.drop_index(
        op.f("ix_whale_notification_deliveries_whale_event_id"),
        table_name="whale_notification_deliveries",
    )
    op.drop_index(
        op.f("ix_whale_notification_deliveries_user_id"),
        table_name="whale_notification_deliveries",
    )
    op.drop_index(
        "uq_whale_notification_deliveries_event_user",
        table_name="whale_notification_deliveries",
    )
    op.drop_table("whale_notification_deliveries")
    op.execute("DROP TYPE IF EXISTS whale_notification_delivery_status")
