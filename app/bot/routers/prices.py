"""Market prices router.

The router only maps Telegram callbacks to bot-level price use cases.
All provider calls, cache checks, error handling, and rendering live in
app.bot.services.prices.
"""

from aiogram import F, Router
from aiogram.types import CallbackQuery

from app.bot.constants import CB_PRICES_IGNORE, CB_PRICES_MENU, CB_PRICES_REFRESH
from app.bot.services import refresh_prices_flow, show_prices_flow
from app.bot.utils import safe_callback_answer

router = Router(name="prices")


@router.callback_query(F.data == CB_PRICES_MENU)
async def show_prices(callback: CallbackQuery) -> None:
    """Show current supported market prices."""
    await show_prices_flow(callback=callback)


@router.callback_query(F.data == CB_PRICES_REFRESH)
async def refresh_prices(callback: CallbackQuery) -> None:
    """Refresh current supported market prices."""
    await refresh_prices_flow(callback=callback)


@router.callback_query(F.data == CB_PRICES_IGNORE)
async def ignore_prices_callback(callback: CallbackQuery) -> None:
    """Ignore disabled prices buttons."""
    await safe_callback_answer(callback)
