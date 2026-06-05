"""FastAPI dependencies."""

from collections.abc import AsyncGenerator
from typing import Annotated

from fastapi import Depends, Header, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.texts import (
    AUTHENTICATION_FAILED_MESSAGE,
    AUTHORIZATION_HEADER_NAME,
)
from app.core.config import get_settings
from app.core.exceptions import AuthenticationError
from app.database.models.user import User
from app.database.session import async_session_maker
from app.services.telegram_webapp_auth import validate_telegram_webapp_init_data
from app.services.users_service import register_or_update_user


async def get_db_session() -> AsyncGenerator[AsyncSession]:
    """Provide a database session for API routes.

    The session is committed when the request handler finishes successfully.
    If an exception happens, all uncommitted changes are rolled back.
    """
    async with async_session_maker() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        else:
            await session.commit()


DbSession = Annotated[AsyncSession, Depends(get_db_session)]
TelegramInitDataHeader = Annotated[
    str | None,
    Header(alias=AUTHORIZATION_HEADER_NAME),
]


async def get_current_miniapp_user(
    session: DbSession,
    init_data: TelegramInitDataHeader = None,
) -> User:
    """Authenticate Telegram Mini App request and return database user.

    The frontend sends raw Telegram WebApp initData in X-Telegram-Init-Data.
    The backend verifies the signature and then creates or updates the user
    from trusted Telegram data.
    """
    settings = get_settings()

    try:
        telegram_user = validate_telegram_webapp_init_data(
            init_data=init_data or "",
            bot_token=settings.bot_token,
        )
    except AuthenticationError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(exc) or AUTHENTICATION_FAILED_MESSAGE,
        ) from exc

    return await register_or_update_user(
        session,
        telegram_id=telegram_user.telegram_id,
        username=telegram_user.username,
        first_name=telegram_user.first_name,
        last_name=telegram_user.last_name,
    )
