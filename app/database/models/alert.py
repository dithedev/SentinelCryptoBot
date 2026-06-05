from datetime import datetime
from decimal import Decimal
from enum import StrEnum
from typing import TYPE_CHECKING

from sqlalchemy import (
    DateTime,
    ForeignKey,
    Index,
    Numeric,
    String,
)
from sqlalchemy import Enum as SqlEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base, created_at, updated_at

if TYPE_CHECKING:
    from app.database.models.user import User


class AlertCondition(StrEnum):
    """Supported price alert conditions."""

    ABOVE = "above"
    BELOW = "below"


class AlertStatus(StrEnum):
    """Lifecycle status for a price alert."""

    ACTIVE = "active"
    TRIGGERED = "triggered"
    DISABLED = "disabled"


class Alert(Base):
    """User price alert for a selected cryptocurrency."""

    __tablename__ = "alerts"

    id: Mapped[int] = mapped_column(primary_key=True)

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # CoinGecko coin id, for example: bitcoin, ethereum, the-open-network.
    coin_id: Mapped[str] = mapped_column(String(100), nullable=False)

    # User-facing symbol, for example: BTC, ETH, TON.
    symbol: Mapped[str] = mapped_column(String(20), nullable=False)

    target_price: Mapped[Decimal] = mapped_column(
        Numeric(18, 8),
        nullable=False,
    )

    condition: Mapped[AlertCondition] = mapped_column(
        SqlEnum(
            AlertCondition,
            name="alert_condition",
            values_callable=lambda enum_cls: [item.value for item in enum_cls],
        ),
        nullable=False,
    )

    status: Mapped[AlertStatus] = mapped_column(
        SqlEnum(
            AlertStatus,
            name="alert_status",
            values_callable=lambda enum_cls: [item.value for item in enum_cls],
        ),
        default=AlertStatus.ACTIVE,
        nullable=False,
    )

    # The worker writes datetime.now(UTC), so this column must be
    # timezone-aware in PostgreSQL.
    triggered_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    created_at: Mapped[created_at]
    updated_at: Mapped[updated_at]

    user: Mapped["User"] = relationship(back_populates="alerts")

    __table_args__ = (
        Index(
            "ix_alerts_status_coin_condition",
            "status",
            "coin_id",
            "condition",
        ),
    )

    def __repr__(self) -> str:
        return (
            f"Alert(id={self.id!r}, "
            f"user_id={self.user_id!r}, "
            f"symbol={self.symbol!r}, "
            f"condition={self.condition.value!r}, "
            f"target_price={self.target_price!r}, "
            f"status={self.status.value!r})"
        )
