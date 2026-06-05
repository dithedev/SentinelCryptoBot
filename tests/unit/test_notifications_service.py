"""Unit tests for Telegram notification helpers."""

from datetime import UTC, datetime
from decimal import Decimal

import pytest
from aiogram.exceptions import TelegramForbiddenError
from aiogram.methods import SendMessage
from app.core.exceptions import TelegramDeliveryBlockedError
from app.database.models.alert import AlertCondition
from app.database.models.whale import WhaleEvent, WhaleEventType
from app.services.notifications_service import (
    send_price_alert_notification,
    send_whale_alert_notification,
)


class FakeBot:
    """Minimal Bot stub for notification tests."""

    def __init__(self, *, should_forbid: bool = False) -> None:
        self.should_forbid = should_forbid
        self.sent_messages: list[dict[str, object]] = []

    async def send_message(self, **kwargs: object) -> None:
        if self.should_forbid:
            raise TelegramForbiddenError(
                method=SendMessage(chat_id=0, text="blocked"),
                message="blocked",
            )

        self.sent_messages.append(kwargs)


@pytest.mark.asyncio
async def test_send_price_alert_notification_maps_forbidden_to_domain_error() -> None:
    """Blocked Telegram chats should raise TelegramDeliveryBlockedError."""
    bot = FakeBot(should_forbid=True)

    with pytest.raises(TelegramDeliveryBlockedError) as exc_info:
        await send_price_alert_notification(
            bot,  # type: ignore[arg-type]
            telegram_id=123456,
            symbol="BTC",
            condition=AlertCondition.ABOVE,
            target_price=Decimal("50000"),
            current_price=Decimal("60000"),
        )

    assert exc_info.value.telegram_id == 123456


@pytest.mark.asyncio
async def test_send_price_alert_notification_includes_dismiss_keyboard() -> None:
    """Price alert notifications should be user-dismissible."""
    bot = FakeBot()

    await send_price_alert_notification(
        bot,  # type: ignore[arg-type]
        telegram_id=123456,
        symbol="BTC",
        condition=AlertCondition.ABOVE,
        target_price=Decimal("50000"),
        current_price=Decimal("60000"),
    )

    assert len(bot.sent_messages) == 1
    sent_message = bot.sent_messages[0]

    assert "<b>Find it later:</b> Main menu > Alerts > My alerts > History." in str(
        sent_message["text"]
    )
    assert sent_message["reply_markup"] is not None


@pytest.mark.asyncio
async def test_send_whale_alert_notification_includes_dismiss_keyboard() -> None:
    """Whale alert notifications should be user-dismissible."""
    bot = FakeBot()
    event = WhaleEvent(
        coin_id="bitcoin",
        symbol="BTC",
        network="btc",
        transaction_hash="tx-1",
        amount=Decimal("100"),
        amount_usd=Decimal("10000000"),
        event_type=WhaleEventType.TRANSFER,
        detected_at=datetime(2026, 5, 23, 10, 0, tzinfo=UTC),
        raw_payload={},
    )

    await send_whale_alert_notification(
        bot,  # type: ignore[arg-type]
        telegram_id=123456,
        event=event,
    )

    assert len(bot.sent_messages) == 1
    sent_message = bot.sent_messages[0]

    assert "<b>Find it later:</b> Main menu > Whales > Recent events." in str(
        sent_message["text"]
    )
    assert sent_message["reply_markup"] is not None
