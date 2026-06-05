"""Unit tests for Telegram bot price alert flows."""

from datetime import UTC, datetime
from decimal import Decimal
from typing import Any

import pytest
from app.bot.constants import CB_ALERTS_IGNORE
from app.bot.screens.alerts import AlertPageRequest, build_alerts_page_screen
from app.bot.services import alerts as alerts_service
from app.bot.services.alerts import (
    ALERT_CREATION_SCREEN_CHAT_ID_KEY,
    ALERT_CREATION_SCREEN_MESSAGE_ID_KEY,
    handle_alert_price_input_flow,
)
from app.bot.texts import ALERT_CREATION_LOADING_TEXT
from app.database.models.alert import Alert, AlertCondition, AlertStatus
from app.services.alerts_service import AlertCreateData, AlertHistoryPage

ALERT_SCREEN_CHAT_ID = 123456789
ALERT_SCREEN_MESSAGE_ID = 42


class FakeBot:
    """Minimal bot object for editing existing messages."""

    def __init__(self) -> None:
        self.edits: list[dict[str, Any]] = []

    async def edit_message_text(
        self,
        *,
        chat_id: int,
        message_id: int,
        text: str,
        reply_markup: object | None = None,
    ) -> None:
        """Capture message edits."""
        self.edits.append(
            {
                "chat_id": chat_id,
                "message_id": message_id,
                "text": text,
                "reply_markup": reply_markup,
            },
        )


class FakeMessage:
    """Minimal message object for alert input tests."""

    def __init__(self, *, text: str) -> None:
        self.text = text
        self.from_user = object()
        self.bot = FakeBot()
        self.delete_called = False
        self.answers: list[dict[str, Any]] = []

    async def delete(self) -> None:
        """Mark user input as deleted."""
        self.delete_called = True

    async def answer(
        self,
        *,
        text: str,
        reply_markup: object | None = None,
    ) -> None:
        """Capture fallback messages."""
        self.answers.append(
            {
                "text": text,
                "reply_markup": reply_markup,
            },
        )


class FakeState:
    """Minimal FSM state for alert input tests."""

    def __init__(self) -> None:
        self.cleared = False
        self.data: dict[str, Any] = {
            "coin_id": "bitcoin",
            "condition": AlertCondition.ABOVE.value,
            ALERT_CREATION_SCREEN_CHAT_ID_KEY: ALERT_SCREEN_CHAT_ID,
            ALERT_CREATION_SCREEN_MESSAGE_ID_KEY: ALERT_SCREEN_MESSAGE_ID,
        }

    async def get_data(self) -> dict[str, Any]:
        """Return stored FSM data."""
        return self.data

    async def clear(self) -> None:
        """Mark state as cleared."""
        self.cleared = True


def build_alert() -> Alert:
    """Build a deterministic price alert."""
    now = datetime(2026, 5, 23, 10, 0, tzinfo=UTC)
    return Alert(
        id=1,
        user_id=1,
        coin_id="bitcoin",
        symbol="BTC",
        target_price=Decimal("50000"),
        condition=AlertCondition.ABOVE,
        status=AlertStatus.ACTIVE,
        triggered_at=None,
        created_at=now,
        updated_at=now,
    )


@pytest.mark.asyncio
async def test_handle_alert_price_input_flow_edits_existing_screen(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Valid price input should delete user message and edit the bot screen."""
    message = FakeMessage(text="50000")
    state = FakeState()

    async def fake_get_current_user_id(**_kwargs: Any) -> int:
        return 1

    async def fake_create_price_alert(
        _session: object,
        *,
        data: AlertCreateData,
    ) -> Alert:
        assert data.user_id == 1
        assert data.coin_id == "bitcoin"
        assert data.target_price == Decimal("50000.00000000")
        assert data.condition == AlertCondition.ABOVE
        return build_alert()

    monkeypatch.setattr(
        alerts_service,
        "get_current_user_id",
        fake_get_current_user_id,
    )
    monkeypatch.setattr(
        alerts_service,
        "create_price_alert",
        fake_create_price_alert,
    )

    await handle_alert_price_input_flow(
        message=message,  # type: ignore[arg-type]
        state=state,  # type: ignore[arg-type]
        session=object(),  # type: ignore[arg-type]
    )

    assert state.cleared is True
    assert message.delete_called is True
    assert message.answers == []
    assert len(message.bot.edits) == 2
    assert message.bot.edits[0]["text"] == ALERT_CREATION_LOADING_TEXT
    assert message.bot.edits[0]["reply_markup"] is None
    assert "Alert created" in message.bot.edits[1]["text"]
    assert message.bot.edits[1]["reply_markup"] is not None


@pytest.mark.asyncio
async def test_handle_alert_price_input_flow_edits_validation_error() -> None:
    """Invalid price input should delete user message and edit the same screen."""
    message = FakeMessage(text="not-a-price")
    state = FakeState()

    await handle_alert_price_input_flow(
        message=message,  # type: ignore[arg-type]
        state=state,  # type: ignore[arg-type]
        session=object(),  # type: ignore[arg-type]
    )

    assert state.cleared is False
    assert message.delete_called is True
    assert message.answers == []
    assert len(message.bot.edits) == 1
    assert "valid number" in message.bot.edits[0]["text"].lower()
    assert message.bot.edits[0]["reply_markup"] is not None


@pytest.mark.asyncio
async def test_alerts_page_screen_caps_visible_pages(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Bot alert pagination should stop at the visible page cap."""

    async def fake_get_user_alerts_page(
        _session: object,
        *,
        user_id: int,
        status_filter: AlertStatus | None,
        limit: int,
        offset: int,
    ) -> AlertHistoryPage:
        assert user_id == 1
        assert status_filter is None
        assert limit > 0
        assert offset == 19 * limit

        return AlertHistoryPage(
            items=[build_alert()],
            limit=limit,
            offset=offset,
            has_more=True,
            total_count=250,
            total_pages=25,
        )

    monkeypatch.setattr(
        "app.bot.screens.alerts.get_user_alerts_page",
        fake_get_user_alerts_page,
    )

    screen = await build_alerts_page_screen(
        session=object(),  # type: ignore[arg-type]
        user_id=1,
        request=AlertPageRequest(
            filter_value="all",
            page_number=30,
        ),
    )

    assert screen.reply_markup is not None
    pagination_row = screen.reply_markup.inline_keyboard[2]
    assert pagination_row[1].text == "20/20"
    assert pagination_row[2].callback_data == CB_ALERTS_IGNORE
