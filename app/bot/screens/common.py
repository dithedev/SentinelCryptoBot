"""Reusable bot screen objects."""

from dataclasses import dataclass

from aiogram.types import InlineKeyboardMarkup


@dataclass(frozen=True)
class BotScreen:
    """Prepared Telegram message screen.

    Routers should only send or edit this screen. Text building, keyboard
    building, pagination and selection logic should happen before the router.
    """

    text: str
    reply_markup: InlineKeyboardMarkup | None = None
