"""Notification service.

This module contains Telegram notification helpers.

The service builds message text through concrete text builder modules instead
of importing from app.bot.text_builders package __init__.py. This avoids circular
imports when bot text builders import domain service types for annotations.
"""

from decimal import Decimal

from aiogram import Bot
from aiogram.enums import ParseMode
from aiogram.exceptions import TelegramForbiddenError
from aiogram.types import InlineKeyboardMarkup

from app.bot.keyboards import build_notification_dismiss_keyboard
from app.bot.text_builders.alerts import build_alert_triggered_text
from app.bot.text_builders.whales import build_whale_alert_notification_text
from app.core.exceptions import TelegramDeliveryBlockedError
from app.database.models.alert import AlertCondition
from app.database.models.whale import WhaleEvent


async def send_price_alert_notification(
    bot: Bot,
    *,
    telegram_id: int,
    symbol: str,
    condition: AlertCondition,
    target_price: Decimal,
    current_price: Decimal,
) -> None:
    """Send a triggered price alert notification to a Telegram user."""
    text = build_alert_triggered_text(
        symbol=symbol,
        condition=condition,
        target_price=target_price,
        current_price=current_price,
    )

    await _send_html_message(
        bot,
        telegram_id=telegram_id,
        text=text,
        reply_markup=build_notification_dismiss_keyboard(),
    )


async def send_whale_alert_notification(
    bot: Bot,
    *,
    telegram_id: int,
    event: WhaleEvent,
) -> None:
    """Send a whale movement notification to a Telegram user."""
    text = build_whale_alert_notification_text(event)

    await _send_html_message(
        bot,
        telegram_id=telegram_id,
        text=text,
        reply_markup=build_notification_dismiss_keyboard(),
    )


async def _send_html_message(
    bot: Bot,
    *,
    telegram_id: int,
    text: str,
    reply_markup: InlineKeyboardMarkup | None = None,
) -> None:
    """Send one HTML message and map blocked chats to a domain error."""
    try:
        await bot.send_message(
            chat_id=telegram_id,
            text=text,
            parse_mode=ParseMode.HTML,
            reply_markup=reply_markup,
        )
    except TelegramForbiddenError as exc:
        raise TelegramDeliveryBlockedError(telegram_id=telegram_id) from exc
