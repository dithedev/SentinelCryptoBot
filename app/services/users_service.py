"""User domain service.

The service layer contains application use cases and coordinates repositories.
It does not know anything about Telegram handlers, buttons, or user-facing text.
"""

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import UserNotFoundError
from app.database.models.user import User
from app.repositories.users import (
    get_or_create_user,
    get_user_by_id,
    get_user_by_telegram_id,
    set_user_active_bot_message,
)


async def get_user_or_raise(
    session: AsyncSession,
    *,
    user_id: int,
) -> User:
    """Return a user by internal database id or raise a domain error."""
    user = await get_user_by_id(session, user_id)

    if user is None:
        raise UserNotFoundError

    return user


async def get_user_by_telegram_id_or_raise(
    session: AsyncSession,
    *,
    telegram_id: int,
) -> User:
    """Return a user by Telegram id or raise a domain error."""
    user = await get_user_by_telegram_id(session, telegram_id)

    if user is None:
        raise UserNotFoundError

    return user


async def register_or_update_user(
    session: AsyncSession,
    *,
    telegram_id: int,
    username: str | None,
    first_name: str | None,
    last_name: str | None,
) -> User:
    """Create a user or refresh profile fields if the user already exists."""
    return await get_or_create_user(
        session,
        telegram_id=telegram_id,
        username=username,
        first_name=first_name,
        last_name=last_name,
    )


async def remember_user_active_bot_message(
    session: AsyncSession,
    *,
    user: User,
    chat_id: int,
    message_id: int,
) -> User:
    """Remember the latest bot screen that can be cleaned up later."""
    return await set_user_active_bot_message(
        session,
        user=user,
        chat_id=chat_id,
        message_id=message_id,
    )
