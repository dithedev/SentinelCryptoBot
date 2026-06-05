from typing import TYPE_CHECKING

from sqlalchemy import BigInteger, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base, created_at, updated_at

if TYPE_CHECKING:
    from app.database.models.alert import Alert
    from app.database.models.token_check import TokenCheck
    from app.database.models.whale import WhaleAlertSettings


class User(Base):
    """Telegram user registered in the bot."""

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)

    telegram_id: Mapped[int] = mapped_column(
        BigInteger,
        unique=True,
        index=True,
        nullable=False,
    )
    username: Mapped[str | None] = mapped_column(String(255), nullable=True)
    first_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    last_name: Mapped[str | None] = mapped_column(String(255), nullable=True)

    is_active: Mapped[bool] = mapped_column(default=True, nullable=False)
    active_bot_chat_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    active_bot_message_id: Mapped[int | None] = mapped_column(
        BigInteger,
        nullable=True,
    )

    created_at: Mapped[created_at]
    updated_at: Mapped[updated_at]

    alerts: Mapped[list["Alert"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
    )
    token_checks: Mapped[list["TokenCheck"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
    )
    whale_alert_settings: Mapped["WhaleAlertSettings | None"] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return (
            f"User(id={self.id!r}, "
            f"telegram_id={self.telegram_id!r}, "
            f"username={self.username!r})"
        )
