"""Unit tests for Telegram bot start flow."""

from dataclasses import dataclass
from typing import Any

import pytest
from app.bot.services import start as start_service
from app.bot.services.start import handle_start_flow

TELEGRAM_ID = 123456789
OLD_CHAT_ID = 123456789
OLD_MESSAGE_ID = 7
NEW_MESSAGE_ID = 8


@dataclass
class FakeTelegramUser:
    """Minimal Telegram user object used by start flow tests."""

    id: int = TELEGRAM_ID
    username: str | None = "sentinel_user"
    first_name: str | None = "Sentinel"
    last_name: str | None = "User"


class FakeDbUser:
    """Minimal persisted user object used by start flow tests."""

    active_bot_chat_id = OLD_CHAT_ID
    active_bot_message_id = OLD_MESSAGE_ID


class FakeChat:
    """Minimal Telegram chat object."""

    id = TELEGRAM_ID


class FakeSentMessage:
    """Minimal sent bot message object."""

    chat = FakeChat()
    message_id = NEW_MESSAGE_ID


class FakeBot:
    """Minimal bot object for delete calls."""

    def __init__(self) -> None:
        self.deleted_messages: list[tuple[int, int]] = []

    async def delete_message(
        self,
        *,
        chat_id: int,
        message_id: int,
    ) -> None:
        """Capture deleted messages."""
        self.deleted_messages.append((chat_id, message_id))


class FakeMessage:
    """Minimal incoming /start message."""

    def __init__(self) -> None:
        self.from_user = FakeTelegramUser()
        self.bot = FakeBot()
        self.delete_called = False
        self.answers: list[dict[str, Any]] = []

    async def delete(self) -> None:
        """Mark incoming /start as deleted."""
        self.delete_called = True

    async def answer(
        self,
        *,
        text: str,
        reply_markup: Any,
    ) -> FakeSentMessage:
        """Capture outgoing start message."""
        self.answers.append(
            {
                "text": text,
                "reply_markup": reply_markup,
            },
        )
        return FakeSentMessage()


@pytest.mark.asyncio
async def test_handle_start_flow_replaces_previous_start_window(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Repeated /start should remove old bot and user messages."""
    remembered_messages: list[tuple[int, int]] = []

    async def fake_register_or_update_user(
        _session: object,
        *,
        telegram_id: int,
        username: str | None,
        first_name: str | None,
        last_name: str | None,
    ) -> FakeDbUser:
        """Return a fake persisted user with an old active window."""
        assert telegram_id == TELEGRAM_ID
        assert username == "sentinel_user"
        assert first_name == "Sentinel"
        assert last_name == "User"
        return FakeDbUser()

    async def fake_remember_user_active_bot_message(
        _session: object,
        *,
        user: FakeDbUser,
        chat_id: int,
        message_id: int,
    ) -> FakeDbUser:
        """Capture the new active bot window."""
        assert isinstance(user, FakeDbUser)
        remembered_messages.append((chat_id, message_id))
        return user

    monkeypatch.setattr(
        start_service,
        "register_or_update_user",
        fake_register_or_update_user,
    )
    monkeypatch.setattr(
        start_service,
        "remember_user_active_bot_message",
        fake_remember_user_active_bot_message,
    )

    message = FakeMessage()

    await handle_start_flow(
        message=message,  # type: ignore[arg-type]
        session=object(),  # type: ignore[arg-type]
    )

    assert message.bot.deleted_messages == [(OLD_CHAT_ID, OLD_MESSAGE_ID)]
    assert message.delete_called is True
    assert len(message.answers) == 1
    assert remembered_messages == [(TELEGRAM_ID, NEW_MESSAGE_ID)]
