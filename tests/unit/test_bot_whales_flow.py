"""Unit tests for Telegram bot whale alert flows."""

from datetime import UTC, datetime
from decimal import Decimal
from typing import Any

import pytest
from app.bot.screens.whales import (
    WhaleEventsPageRequest,
    build_whale_events_page_screen,
)
from app.bot.services import whales as whales_service
from app.bot.services.whales import (
    WHALE_THRESHOLD_SCREEN_CHAT_ID_KEY,
    WHALE_THRESHOLD_SCREEN_MESSAGE_ID_KEY,
)
from app.bot.texts import (
    WHALES_ALERTS_ENABLED_TEXT,
    WHALES_THRESHOLD_LOADING_TEXT,
    WHALES_THRESHOLD_UPDATED_TEXT,
)
from app.database.models.whale import WhaleAlertSettings, WhaleEvent, WhaleEventType
from app.services.whales_service import UserWhaleSettings, WhaleEventsPage


class FakeTelegramUser:
    """Minimal Telegram user object for callback/message tests."""

    def __init__(self, *, user_id: int = 777) -> None:
        self.id = user_id


class FakeCallback:
    """Minimal callback object for bot whale flow tests."""

    def __init__(self, *, data: str | None = None) -> None:
        self.data = data
        self.from_user = FakeTelegramUser()
        self.answers: list[tuple[str | None, bool]] = []
        self.edits: list[dict[str, Any]] = []

    async def answer(
        self,
        text: str | None = None,
        *,
        show_alert: bool = False,
    ) -> None:
        self.answers.append((text, show_alert))


WHALE_SCREEN_CHAT_ID = 123456789
WHALE_SCREEN_MESSAGE_ID = 42


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
        self.edits.append(
            {
                "chat_id": chat_id,
                "message_id": message_id,
                "text": text,
                "reply_markup": reply_markup,
            },
        )


class FakeMessage:
    """Minimal message object for bot whale flow tests."""

    def __init__(self, *, text: str) -> None:
        self.text = text
        self.from_user = FakeTelegramUser()
        self.bot = FakeBot()
        self.delete_called = False
        self.answers: list[dict[str, Any]] = []

    async def answer(
        self,
        *,
        text: str,
        reply_markup: object | None = None,
    ) -> None:
        self.answers.append(
            {
                "text": text,
                "reply_markup": reply_markup,
            },
        )

    async def delete(self) -> None:
        self.delete_called = True


class FakeState:
    """Minimal FSM state for bot whale flow tests."""

    def __init__(self) -> None:
        self.cleared = False
        self.data = {
            WHALE_THRESHOLD_SCREEN_CHAT_ID_KEY: WHALE_SCREEN_CHAT_ID,
            WHALE_THRESHOLD_SCREEN_MESSAGE_ID_KEY: WHALE_SCREEN_MESSAGE_ID,
        }

    async def set_state(self, _state: object) -> None:
        return None

    async def clear(self) -> None:
        self.cleared = True

    async def get_data(self) -> dict[str, Any]:
        return self.data

    async def update_data(self, **kwargs: Any) -> None:
        self.data.update(kwargs)


def _build_settings(
    *,
    is_enabled: bool = False,
    min_usd_value: Decimal = Decimal("1000000"),
) -> WhaleAlertSettings:
    """Build deterministic whale settings."""
    created_at = datetime(2026, 5, 20, 10, 0, tzinfo=UTC)

    return WhaleAlertSettings(
        id=1,
        user_id=1,
        is_enabled=is_enabled,
        min_usd_value=min_usd_value,
        created_at=created_at,
        updated_at=created_at,
    )


def _build_whale_event() -> WhaleEvent:
    """Build deterministic whale event for screen tests."""
    detected_at = datetime(2026, 5, 20, 10, 0, tzinfo=UTC)

    return WhaleEvent(
        id=1,
        coin_id="bitcoin",
        symbol="BTC",
        network="btc",
        transaction_hash="0xabc",
        from_address="from",
        to_address="to",
        amount=Decimal("15.000000000000000000"),
        amount_usd=Decimal("1500000"),
        event_type=WhaleEventType.TRANSFER,
        detected_at=detected_at,
        raw_payload={},
        created_at=detected_at,
    )


@pytest.mark.asyncio
async def test_toggle_whale_alerts_flow_enables_settings(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Toggle flow should flip disabled settings to enabled."""
    callback = FakeCallback()
    existing_settings = _build_settings(is_enabled=False)

    async def fake_get_current_user_whale_settings(
        **_kwargs: Any,
    ) -> UserWhaleSettings:
        return UserWhaleSettings(user_id=1, settings=existing_settings)

    async def fake_update(
        _session: object,
        *,
        settings: WhaleAlertSettings,
        is_enabled: bool | None = None,
        min_usd_value: Decimal | None = None,
    ) -> WhaleAlertSettings:
        assert settings is existing_settings
        assert is_enabled is True
        assert min_usd_value is None
        return _build_settings(is_enabled=True)

    async def fake_edit_callback_message(
        _callback: object,
        **kwargs: Any,
    ) -> None:
        callback.edits.append(kwargs)

    monkeypatch.setattr(
        whales_service,
        "_get_current_user_whale_settings",
        fake_get_current_user_whale_settings,
    )
    monkeypatch.setattr(
        whales_service,
        "update_loaded_user_whale_settings",
        fake_update,
    )
    monkeypatch.setattr(
        whales_service,
        "edit_callback_message",
        fake_edit_callback_message,
    )

    await whales_service.toggle_whale_alerts_flow(
        callback=callback,  # type: ignore[arg-type]
        session=object(),  # type: ignore[arg-type]
    )

    assert callback.answers[0][0] == WHALES_ALERTS_ENABLED_TEXT
    assert "Enabled" in callback.edits[-1]["text"]


@pytest.mark.asyncio
async def test_handle_whale_threshold_input_flow_updates_settings(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Threshold input should update settings and clear FSM state."""
    message = FakeMessage(text="2500000")
    state = FakeState()
    updated_settings = _build_settings(
        is_enabled=True,
        min_usd_value=Decimal("2500000.00"),
    )

    async def fake_get_current_user_whale_settings(
        **_kwargs: Any,
    ) -> UserWhaleSettings:
        return UserWhaleSettings(user_id=1, settings=_build_settings(is_enabled=True))

    async def fake_update(
        _session: object,
        *,
        settings: WhaleAlertSettings,
        is_enabled: bool | None = None,
        min_usd_value: Decimal | None = None,
    ) -> WhaleAlertSettings:
        assert settings.is_enabled is True
        assert is_enabled is None
        assert min_usd_value == Decimal("2500000.00")
        return updated_settings

    monkeypatch.setattr(
        whales_service,
        "_get_current_user_whale_settings",
        fake_get_current_user_whale_settings,
    )
    monkeypatch.setattr(
        whales_service,
        "update_loaded_user_whale_settings",
        fake_update,
    )

    await whales_service.handle_whale_threshold_input_flow(
        message=message,  # type: ignore[arg-type]
        state=state,  # type: ignore[arg-type]
        session=object(),  # type: ignore[arg-type]
    )

    assert state.cleared is True
    assert message.delete_called is True
    assert message.answers == []
    assert len(message.bot.edits) == 2
    assert message.bot.edits[0]["text"] == WHALES_THRESHOLD_LOADING_TEXT
    assert message.bot.edits[0]["reply_markup"] is None
    assert WHALES_THRESHOLD_UPDATED_TEXT in message.bot.edits[1]["text"]
    assert message.bot.edits[1]["reply_markup"] is not None


@pytest.mark.asyncio
async def test_handle_whale_threshold_input_flow_rejects_invalid_value(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Invalid threshold input should return a validation message."""
    message = FakeMessage(text="not-a-number")
    state = FakeState()

    await whales_service.handle_whale_threshold_input_flow(
        message=message,  # type: ignore[arg-type]
        state=state,  # type: ignore[arg-type]
        session=object(),  # type: ignore[arg-type]
    )

    assert state.cleared is False
    assert message.delete_called is True
    assert message.answers == []
    assert len(message.bot.edits) == 1
    assert "valid number" in message.bot.edits[0]["text"].lower()


@pytest.mark.asyncio
async def test_whale_events_page_screen_uses_service_total_pages(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Whale events pagination should show the real total page count."""

    async def fake_get_latest_whale_events_page(
        _session: object,
        *,
        limit: int,
        offset: int,
    ) -> WhaleEventsPage:
        assert limit > 0
        assert offset == 2 * limit

        return WhaleEventsPage(
            items=[_build_whale_event()],
            limit=limit,
            offset=offset,
            has_more=True,
            total_count=95,
            total_pages=19,
        )

    monkeypatch.setattr(
        "app.bot.screens.whales.get_latest_whale_events_page",
        fake_get_latest_whale_events_page,
    )

    screen = await build_whale_events_page_screen(
        session=object(),  # type: ignore[arg-type]
        request=WhaleEventsPageRequest(page_number=2),
    )

    assert screen.reply_markup is not None
    pagination_row = screen.reply_markup.inline_keyboard[0]
    assert pagination_row[1].text == "3/19"


@pytest.mark.asyncio
async def test_whale_events_page_screen_caps_visible_pages(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Whale events pagination should stop at the bot-visible page cap."""

    async def fake_get_latest_whale_events_page(
        _session: object,
        *,
        limit: int,
        offset: int,
    ) -> WhaleEventsPage:
        assert limit > 0
        assert offset == 19 * limit

        return WhaleEventsPage(
            items=[_build_whale_event()],
            limit=limit,
            offset=offset,
            has_more=True,
            total_count=200,
            total_pages=40,
        )

    monkeypatch.setattr(
        "app.bot.screens.whales.get_latest_whale_events_page",
        fake_get_latest_whale_events_page,
    )

    screen = await build_whale_events_page_screen(
        session=object(),  # type: ignore[arg-type]
        request=WhaleEventsPageRequest(page_number=30),
    )

    assert screen.reply_markup is not None
    pagination_row = screen.reply_markup.inline_keyboard[0]
    assert pagination_row[1].text == "20/20"
    assert pagination_row[2].callback_data == "whales:ignore"


@pytest.mark.asyncio
async def test_ignore_whales_callback_flow_answers_without_navigation() -> None:
    """No-op whale pagination callbacks should only answer the callback."""
    callback = FakeCallback()

    await whales_service.ignore_whales_callback_flow(
        callback=callback,  # type: ignore[arg-type]
    )

    assert len(callback.answers) == 1
    assert callback.answers[0] == (None, False)
    assert callback.edits == []
