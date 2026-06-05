from datetime import datetime
from decimal import Decimal
from enum import StrEnum
from typing import TYPE_CHECKING, Any

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Index,
    Numeric,
    String,
    UniqueConstraint,
)
from sqlalchemy import Enum as SqlEnum
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.constants import DEFAULT_WHALE_MIN_USD_VALUE
from app.database.base import Base, created_at, updated_at

if TYPE_CHECKING:
    from app.database.models.user import User


class WhaleEventType(StrEnum):
    """Normalized type of a large market-moving transaction."""

    TRANSFER = "transfer"
    EXCHANGE_INFLOW = "exchange_inflow"
    EXCHANGE_OUTFLOW = "exchange_outflow"
    UNKNOWN = "unknown"


class WhaleAlertSettings(Base):
    """Per-user settings for whale movement notifications."""

    __tablename__ = "whale_alert_settings"

    id: Mapped[int] = mapped_column(primary_key=True)

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
        index=True,
    )

    is_enabled: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )

    min_usd_value: Mapped[Decimal] = mapped_column(
        Numeric(20, 2),
        default=DEFAULT_WHALE_MIN_USD_VALUE,
        nullable=False,
    )

    created_at: Mapped[created_at]
    updated_at: Mapped[updated_at]

    user: Mapped["User"] = relationship(back_populates="whale_alert_settings")

    def __repr__(self) -> str:
        return (
            f"WhaleAlertSettings(id={self.id!r}, "
            f"user_id={self.user_id!r}, "
            f"is_enabled={self.is_enabled!r}, "
            f"min_usd_value={self.min_usd_value!r})"
        )


class WhaleNotificationDeliveryStatus(StrEnum):
    """Delivery state for one whale event and one user."""

    PENDING = "pending"
    SENT = "sent"
    FAILED = "failed"


class WhaleNotificationDelivery(Base):
    """Tracks whale notification delivery per user and event."""

    __tablename__ = "whale_notification_deliveries"

    id: Mapped[int] = mapped_column(primary_key=True)

    whale_event_id: Mapped[int] = mapped_column(
        ForeignKey("whale_events.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    status: Mapped[WhaleNotificationDeliveryStatus] = mapped_column(
        SqlEnum(
            WhaleNotificationDeliveryStatus,
            name="whale_notification_delivery_status",
            values_callable=lambda enum_cls: [item.value for item in enum_cls],
        ),
        default=WhaleNotificationDeliveryStatus.PENDING,
        nullable=False,
    )

    attempts: Mapped[int] = mapped_column(default=0, nullable=False)

    last_error: Mapped[str | None] = mapped_column(String(500), nullable=True)

    created_at: Mapped[created_at]
    updated_at: Mapped[updated_at]

    __table_args__ = (
        UniqueConstraint(
            "whale_event_id",
            "user_id",
            name="uq_whale_notification_deliveries_event_user",
        ),
    )


class WhaleEvent(Base):
    """Stored whale movement event.

    Events are global, not user-owned. User-specific delivery is decided by
    WhaleAlertSettings and handled later by the whale worker.
    """

    __tablename__ = "whale_events"

    id: Mapped[int] = mapped_column(primary_key=True)

    # CoinGecko coin id, for example: bitcoin, ethereum, the-open-network.
    coin_id: Mapped[str] = mapped_column(String(100), nullable=False)

    # User-facing symbol, for example: BTC, ETH, TON.
    symbol: Mapped[str] = mapped_column(String(20), nullable=False)

    # Network/source label used by the whale provider, for example: eth, btc.
    network: Mapped[str] = mapped_column(String(50), nullable=False)

    # Provider transaction hash or unique event id.
    transaction_hash: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        nullable=False,
    )

    from_address: Mapped[str | None] = mapped_column(String(255), nullable=True)
    to_address: Mapped[str | None] = mapped_column(String(255), nullable=True)

    amount: Mapped[Decimal] = mapped_column(
        Numeric(36, 18),
        nullable=False,
    )

    amount_usd: Mapped[Decimal] = mapped_column(
        Numeric(20, 2),
        nullable=False,
    )

    event_type: Mapped[WhaleEventType] = mapped_column(
        SqlEnum(
            WhaleEventType,
            name="whale_event_type",
            values_callable=lambda enum_cls: [item.value for item in enum_cls],
        ),
        default=WhaleEventType.UNKNOWN,
        nullable=False,
    )

    # Provider event time. If the provider does not provide it, the service can
    # use current UTC time when creating the event.
    detected_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )

    # Raw provider payload is stored for debugging and future analytics.
    raw_payload: Mapped[dict[str, Any]] = mapped_column(
        JSONB,
        default=dict,
        nullable=False,
    )

    created_at: Mapped[created_at]

    __table_args__ = (
        Index(
            "ix_whale_events_coin_detected_at",
            "coin_id",
            "detected_at",
        ),
        Index(
            "ix_whale_events_amount_usd",
            "amount_usd",
        ),
    )

    def __repr__(self) -> str:
        return (
            f"WhaleEvent(id={self.id!r}, "
            f"symbol={self.symbol!r}, "
            f"amount_usd={self.amount_usd!r}, "
            f"event_type={self.event_type.value!r})"
        )
