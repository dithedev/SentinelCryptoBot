"""Repository helpers for whale alert settings.

Repository functions contain only database access. Business rules, validation,
and notification decisions stay in app.services.whales_service.
"""

from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database.models.user import User
from app.database.models.whale import WhaleAlertSettings


async def get_whale_alert_settings_by_user_id(
    session: AsyncSession,
    *,
    user_id: int,
) -> WhaleAlertSettings | None:
    """Return whale alert settings for a user."""
    result = await session.execute(
        select(WhaleAlertSettings)
        .where(
            WhaleAlertSettings.user_id == user_id,
        )
        .execution_options(populate_existing=True),
    )
    return result.scalar_one_or_none()


async def get_user_id_and_whale_alert_settings_by_telegram_id(
    session: AsyncSession,
    *,
    telegram_id: int,
) -> tuple[int, WhaleAlertSettings | None] | None:
    """Return a user's id and whale settings in one round-trip."""
    result = await session.execute(
        select(User.id, WhaleAlertSettings)
        .outerjoin(
            WhaleAlertSettings,
            WhaleAlertSettings.user_id == User.id,
        )
        .where(User.telegram_id == telegram_id),
    )
    row = result.one_or_none()

    if row is None:
        return None

    user_id, settings = row
    return user_id, settings


async def create_whale_alert_settings(
    session: AsyncSession,
    *,
    user_id: int,
    is_enabled: bool,
    min_usd_value: Decimal,
) -> WhaleAlertSettings:
    """Create whale alert settings for a user.

    The row is refreshed after flush so server-managed datetime fields are
    loaded before API presenters access them. This avoids implicit async lazy
    loading outside SQLAlchemy's greenlet context.
    """
    settings = WhaleAlertSettings(
        user_id=user_id,
        is_enabled=is_enabled,
        min_usd_value=min_usd_value,
    )

    session.add(settings)
    await session.flush()
    await session.refresh(settings)

    return settings


async def update_whale_alert_settings(
    session: AsyncSession,
    *,
    settings: WhaleAlertSettings,
    is_enabled: bool | None = None,
    min_usd_value: Decimal | None = None,
) -> WhaleAlertSettings:
    """Update existing whale alert settings in-place.

    SQLAlchemy can expire server-managed columns after flush. Refreshing the
    instance makes created_at and updated_at safe to read in response presenters.
    """
    if is_enabled is not None:
        settings.is_enabled = is_enabled

    if min_usd_value is not None:
        settings.min_usd_value = min_usd_value

    await session.flush()
    await session.refresh(settings)

    return settings


async def list_enabled_whale_alert_settings_for_amount(
    session: AsyncSession,
    *,
    amount_usd: Decimal,
) -> list[WhaleAlertSettings]:
    """Return enabled settings that match a whale event USD value.

    The user relationship is loaded here because the whale worker will need the
    Telegram id when it sends notifications.
    """
    result = await session.execute(
        select(WhaleAlertSettings)
        .options(selectinload(WhaleAlertSettings.user))
        .join(User, WhaleAlertSettings.user_id == User.id)
        .where(
            WhaleAlertSettings.is_enabled.is_(True),
            WhaleAlertSettings.min_usd_value <= amount_usd,
            User.is_active.is_(True),
        )
        .order_by(WhaleAlertSettings.user_id.asc()),
    )
    return list(result.scalars().all())
