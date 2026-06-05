"""Database session middleware for aiogram handlers."""

from collections.abc import Awaitable, Callable
from typing import Any

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject

from app.database.session import AsyncSessionFactory


class DbSessionMiddleware(BaseMiddleware):
    """Attach an AsyncSession to every aiogram handler.

    Handlers receive the session through the dependency name: session.
    The middleware commits successful updates and rolls back failed updates.
    """

    def __init__(
        self,
        session_maker: AsyncSessionFactory,
    ) -> None:
        self._session_maker = session_maker

    async def __call__(
        self,
        handler: Callable[
            [TelegramObject, dict[str, Any]],
            Awaitable[Any],
        ],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        async with self._session_maker() as session:
            data["session"] = session

            try:
                result = await handler(event, data)
            except Exception:
                await session.rollback()
                raise

            await session.commit()
            return result
