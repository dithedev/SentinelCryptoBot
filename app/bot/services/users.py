"""Bot-specific user helpers.

These helpers adapt Telegram events to the domain user service. They are kept
outside routers so every bot flow can reuse the same current-user logic.
"""

from aiogram.types import CallbackQuery, Message
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import UserNotFoundError
from app.database.models.user import User
from app.services.users_service import get_user_by_telegram_id_or_raise


async def get_current_user(
    *,
    event: CallbackQuery | Message,
    session: AsyncSession,
) -> User:
    """Return the database user for the Telegram event sender."""
    from_user = event.from_user

    if from_user is None:
        raise UserNotFoundError

    return await get_user_by_telegram_id_or_raise(
        session,
        telegram_id=from_user.id,
    )


async def get_current_user_id(
    *,
    event: CallbackQuery | Message,
    session: AsyncSession,
) -> int:
    """Return the internal database id for the Telegram event sender."""
    user = await get_current_user(
        event=event,
        session=session,
    )

    return user.id
