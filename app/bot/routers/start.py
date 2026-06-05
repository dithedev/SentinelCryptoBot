"""Start command router.

The router only maps /start to the start use case.
"""

from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.types import Message
from sqlalchemy.ext.asyncio import AsyncSession

from app.bot.services import handle_start_flow

router = Router(name="start")


@router.message(CommandStart())
async def handle_start(
    message: Message,
    session: AsyncSession,
) -> None:
    """Handle /start command."""
    await handle_start_flow(
        message=message,
        session=session,
    )
