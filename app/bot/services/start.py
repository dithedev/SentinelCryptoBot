"""Bot-level start command use case."""

from aiogram.exceptions import TelegramBadRequest
from aiogram.types import Message
from sqlalchemy.ext.asyncio import AsyncSession

from app.bot.keyboards import build_main_menu_keyboard
from app.bot.texts import START_TEXT
from app.services.users_service import (
    register_or_update_user,
    remember_user_active_bot_message,
)


async def handle_start_flow(
    *,
    message: Message,
    session: AsyncSession,
) -> None:
    """Register or refresh Telegram user and show the main menu."""
    user = message.from_user

    if user is not None:
        db_user = await register_or_update_user(
            session,
            telegram_id=user.id,
            username=user.username,
            first_name=user.first_name,
            last_name=user.last_name,
        )
        await _delete_previous_start_window(
            message=message,
            chat_id=db_user.active_bot_chat_id,
            message_id=db_user.active_bot_message_id,
        )
    else:
        db_user = None

    await _delete_user_start_command(message)

    sent_message = await message.answer(
        text=START_TEXT,
        reply_markup=build_main_menu_keyboard(),
    )

    if db_user is not None:
        await remember_user_active_bot_message(
            session,
            user=db_user,
            chat_id=sent_message.chat.id,
            message_id=sent_message.message_id,
        )


async def _delete_previous_start_window(
    *,
    message: Message,
    chat_id: int | None,
    message_id: int | None,
) -> None:
    """Delete the previous reusable bot screen when Telegram still allows it."""
    if chat_id is None or message_id is None:
        return

    bot = message.bot
    if bot is None:
        return

    try:
        await bot.delete_message(
            chat_id=chat_id,
            message_id=message_id,
        )
    except TelegramBadRequest:
        return


async def _delete_user_start_command(message: Message) -> None:
    """Remove the user's /start command to keep the chat compact."""
    try:
        await message.delete()
    except TelegramBadRequest:
        return
