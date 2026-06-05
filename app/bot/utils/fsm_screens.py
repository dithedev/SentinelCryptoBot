"""Shared helpers for FSM flows that reuse one bot message as a screen."""

from aiogram.exceptions import TelegramBadRequest
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, Message


async def remember_fsm_screen(
    *,
    callback: CallbackQuery,
    state: FSMContext,
    chat_id_key: str,
    message_id_key: str,
) -> None:
    """Store the bot message that should be edited during an FSM flow."""
    if not isinstance(callback.message, Message):
        return

    await state.update_data(
        {
            chat_id_key: callback.message.chat.id,
            message_id_key: callback.message.message_id,
        },
    )


async def delete_user_message(message: Message) -> None:
    """Remove user input messages to keep the chat compact."""
    try:
        await message.delete()
    except TelegramBadRequest:
        return


async def edit_fsm_screen_or_answer(
    *,
    message: Message,
    chat_id: object | None,
    message_id: object | None,
    text: str,
    reply_markup: InlineKeyboardMarkup | None,
) -> None:
    """Edit a remembered FSM screen message, falling back to a new message."""
    if not isinstance(chat_id, int) or not isinstance(message_id, int):
        await message.answer(text=text, reply_markup=reply_markup)
        return

    bot = message.bot
    if bot is None:
        await message.answer(text=text, reply_markup=reply_markup)
        return

    try:
        await bot.edit_message_text(
            chat_id=chat_id,
            message_id=message_id,
            text=text,
            reply_markup=reply_markup,
        )
    except TelegramBadRequest:
        await message.answer(text=text, reply_markup=reply_markup)
