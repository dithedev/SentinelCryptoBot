from enum import StrEnum
from typing import TYPE_CHECKING, Any

from sqlalchemy import Enum as SqlEnum
from sqlalchemy import ForeignKey, Index, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base, created_at

if TYPE_CHECKING:
    from app.database.models.user import User


class RiskLevel(StrEnum):
    """Normalized token risk level shown to the user."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    UNKNOWN = "unknown"


class TokenCheck(Base):
    """Stored result of a token risk check."""

    __tablename__ = "token_checks"

    id: Mapped[int] = mapped_column(primary_key=True)

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Chain identifier used by the security provider.
    # Examples: eth, bsc, polygon, ton.
    chain: Mapped[str] = mapped_column(String(50), nullable=False)

    contract_address: Mapped[str] = mapped_column(String(255), nullable=False)

    risk_level: Mapped[RiskLevel] = mapped_column(
        SqlEnum(
            RiskLevel,
            name="risk_level",
            values_callable=lambda enum_cls: [item.value for item in enum_cls],
        ),
        default=RiskLevel.UNKNOWN,
        nullable=False,
    )

    # Normalized flags are useful for displaying a readable report later.
    flags: Mapped[dict[str, Any]] = mapped_column(
        JSONB,
        default=dict,
        nullable=False,
    )

    # Raw provider response is stored for debugging and auditability.
    raw_response: Mapped[dict[str, Any]] = mapped_column(
        JSONB,
        default=dict,
        nullable=False,
    )

    created_at: Mapped[created_at]

    user: Mapped["User"] = relationship(back_populates="token_checks")

    __table_args__ = (
        Index(
            "ix_token_checks_chain_contract",
            "chain",
            "contract_address",
        ),
    )

    def __repr__(self) -> str:
        return (
            f"TokenCheck(id={self.id!r}, "
            f"user_id={self.user_id!r}, "
            f"chain={self.chain!r}, "
            f"contract_address={self.contract_address!r}, "
            f"risk_level={self.risk_level.value!r})"
        )
