"""Bot-level market price use cases.

This module keeps provider calls, expected errors, cache checks, and rendering
out of routers.
"""

import logging

from aiogram.types import CallbackQuery

from app.bot.keyboards import build_prices_keyboard, build_prices_loading_keyboard
from app.bot.text_builders import build_market_prices_text
from app.bot.texts import (
    PRICES_FAILED_TEXT,
    PRICES_LOADING_TEXT,
    PRICES_REFRESH_COOLDOWN_TEXT_TEMPLATE,
)
from app.bot.utils import edit_callback_message, safe_callback_answer
from app.core.exceptions import PriceProviderError
from app.integrations.coingecko import CoinGeckoClient
from app.services.prices_service import (
    get_supported_market_prices,
    get_supported_market_prices_cache_remaining_seconds,
)

logger = logging.getLogger(__name__)


async def show_prices_flow(
    *,
    callback: CallbackQuery,
) -> None:
    """Load supported market prices and render the bot prices screen."""
    provider = CoinGeckoClient()

    await edit_callback_message(
        callback,
        text=PRICES_LOADING_TEXT,
        reply_markup=build_prices_loading_keyboard(),
    )

    try:
        prices = await get_supported_market_prices(provider)
    except PriceProviderError:
        logger.exception("bot_market_prices_fetch_failed")

        await edit_callback_message(
            callback,
            text=PRICES_FAILED_TEXT,
            reply_markup=build_prices_keyboard(),
            answer_callback=False,
        )
        return

    await edit_callback_message(
        callback,
        text=build_market_prices_text(prices),
        reply_markup=build_prices_keyboard(),
        answer_callback=False,
    )


async def refresh_prices_flow(
    *,
    callback: CallbackQuery,
) -> None:
    """Refresh the bot prices screen when backend cache allows it.

    If the shared prices cache is still fresh, the bot answers the callback with
    a small popup and does not edit the message. This avoids unnecessary API
    calls and prevents Telegram's harmless "message is not modified" case.
    """
    remaining_seconds = get_supported_market_prices_cache_remaining_seconds()

    if remaining_seconds > 0:
        await safe_callback_answer(
            callback,
            PRICES_REFRESH_COOLDOWN_TEXT_TEMPLATE.format(
                seconds=remaining_seconds,
            ),
        )
        return

    await show_prices_flow(callback=callback)
