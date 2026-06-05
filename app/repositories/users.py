from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models.user import User


async def get_user_by_id(session: AsyncSession, user_id: int) -> User | None:
    """Return user by internal database id."""
    result = await session.execute(
        select(User).where(User.id == user_id),
    )
    return result.scalar_one_or_none()


async def get_user_by_telegram_id(
    session: AsyncSession,
    telegram_id: int,
) -> User | None:
    """Return user by Telegram id."""
    result = await session.execute(
        select(User).where(User.telegram_id == telegram_id),
    )
    return result.scalar_one_or_none()


async def create_user(
    session: AsyncSession,
    *,
    telegram_id: int,
    username: str | None,
    first_name: str | None,
    last_name: str | None,
) -> User:
    """Create a new Telegram user."""
    user = User(
        telegram_id=telegram_id,
        username=username,
        first_name=first_name,
        last_name=last_name,
        is_active=True,
    )

    session.add(user)
    await session.flush()

    return user


async def get_or_create_user(
    session: AsyncSession,
    *,
    telegram_id: int,
    username: str | None,
    first_name: str | None,
    last_name: str | None,
) -> User:
    """Return existing user or create a new one.

    User profile fields are refreshed on every call because Telegram usernames
    and names can change over time.
    """
    user = await get_user_by_telegram_id(session, telegram_id)

    if user is None:
        return await create_user(
            session,
            telegram_id=telegram_id,
            username=username,
            first_name=first_name,
            last_name=last_name,
        )

    user.username = username
    user.first_name = first_name
    user.last_name = last_name
    user.is_active = True

    await session.flush()

    return user


async def deactivate_user(
    session: AsyncSession,
    *,
    telegram_id: int,
) -> User | None:
    """Mark user as inactive without deleting historical data."""
    user = await get_user_by_telegram_id(session, telegram_id)

    if user is None:
        return None

    user.is_active = False
    await session.flush()

    return user


async def set_user_active_bot_message(
    session: AsyncSession,
    *,
    user: User,
    chat_id: int,
    message_id: int,
) -> User:
    """Store the latest reusable bot screen for a user."""
    user.active_bot_chat_id = chat_id
    user.active_bot_message_id = message_id

    await session.flush()

    return user
