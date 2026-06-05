"""Unit tests for Telegram bot token risk check flow.

These tests verify that the bot service correctly connects Telegram input,
user lookup, reusable token risk service, and user-facing message rendering.

The external provider is not called here. Instead, check_token_risk is patched
to return deterministic TokenCheck objects. This keeps tests stable and proves
that the bot can display Medium risk when the service returns Medium risk.
"""

import asyncio
from datetime import UTC, datetime
from typing import Any

import pytest
from app.bot.services import risk_check as risk_check_service
from app.bot.services.risk_check import (
    RISK_CHECK_SCREEN_CHAT_ID_KEY,
    RISK_CHECK_SCREEN_MESSAGE_ID_KEY,
    handle_contract_address_flow,
)
from app.bot.texts import (
    INVALID_CONTRACT_ADDRESS_TEXT,
    MAIN_MENU_TEXT,
    RISK_CHECK_FAILED_TEXT,
    RISK_CHECK_LOADING_TEXT,
    RISK_CHECK_TOKEN_NOT_FOUND_TEXT,
)
from app.core.error_messages import GOPLUS_TOKEN_DATA_NOT_FOUND_ERROR
from app.core.exceptions import SecurityProviderError
from app.database.models.token_check import RiskLevel, TokenCheck
from app.database.models.user import User
from app.services.token_risk_service import TokenRiskCheckData

UNKNOWN_ADDRESS = "0x0000000000000000000000000000000000000000"
TELEGRAM_ID = 123456789
USER_ID = 7
RISK_CHECK_SCREEN_CHAT_ID = 123456789
RISK_CHECK_SCREEN_MESSAGE_ID = 42


class FakeTelegramUser:
    """Minimal Telegram user object used by the fake message."""

    id = TELEGRAM_ID


class FakeState:
    """Small fake FSM state for bot service tests."""

    def __init__(
        self,
        data: dict[str, Any] | None = None,
    ) -> None:
        self.data = data or {}
        self.clear_called = False

    async def get_data(self) -> dict[str, Any]:
        """Return stored fake FSM data."""
        return self.data

    async def clear(self) -> None:
        """Mark state as cleared."""
        self.clear_called = True


class FakeBot:
    """Small fake bot used to capture message edits."""

    def __init__(self) -> None:
        self.edits: list[dict[str, Any]] = []

    async def edit_message_text(
        self,
        *,
        chat_id: int,
        message_id: int,
        text: str,
        reply_markup: Any | None = None,
    ) -> None:
        """Store bot message edits for assertions."""
        self.edits.append(
            {
                "chat_id": chat_id,
                "message_id": message_id,
                "text": text,
                "reply_markup": reply_markup,
            },
        )


class FakeMessage:
    """Small fake Telegram message object for bot service tests."""

    def __init__(
        self,
        *,
        text: str | None,
        from_user: FakeTelegramUser | None = None,
    ) -> None:
        self.text = text
        self.from_user = from_user
        self.bot = FakeBot()
        self.delete_called = False
        self.answers: list[dict[str, Any]] = []

    async def answer(
        self,
        text: str,
        reply_markup: Any | None = None,
    ) -> None:
        """Store outgoing bot answers for assertions."""
        self.answers.append(
            {
                "text": text,
                "reply_markup": reply_markup,
            },
        )

    async def delete(self) -> None:
        """Mark the incoming user message as deleted."""
        self.delete_called = True


def build_risk_check_state_data(
    *,
    chain: str = "eth",
) -> dict[str, Any]:
    """Build FSM data with the reusable risk check screen reference."""
    return {
        "chain": chain,
        RISK_CHECK_SCREEN_CHAT_ID_KEY: RISK_CHECK_SCREEN_CHAT_ID,
        RISK_CHECK_SCREEN_MESSAGE_ID_KEY: RISK_CHECK_SCREEN_MESSAGE_ID,
    }


class FakeCallback:
    """Small fake callback object for callback-driven service tests."""


def run_async(result: Any) -> Any:
    """Run one async helper from a regular pytest test."""
    return asyncio.run(result)


def build_user() -> User:
    """Build a deterministic database user."""
    return User(
        id=USER_ID,
        telegram_id=TELEGRAM_ID,
        username="sentinel_user",
        first_name="Sentinel",
        last_name="User",
        is_active=True,
    )


def build_medium_token_check() -> TokenCheck:
    """Build a deterministic Medium risk token check."""
    return TokenCheck(
        id=10,
        user_id=USER_ID,
        chain="eth",
        contract_address=UNKNOWN_ADDRESS,
        risk_level=RiskLevel.MEDIUM,
        flags={
            "slippage_modifiable": True,
            "buy_tax": 15.0,
        },
        raw_response={
            "slippage_modifiable": "1",
            "buy_tax": "15",
        },
        created_at=datetime(2026, 5, 18, 10, 0, tzinfo=UTC),
    )


def test_handle_contract_address_flow_renders_medium_risk_result(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Bot flow should display Medium risk when the service returns it."""
    user_lookup_calls: list[int] = []
    risk_check_calls: list[TokenRiskCheckData] = []

    async def fake_get_user_by_telegram_id_or_raise(
        _session: object,
        *,
        telegram_id: int,
    ) -> User:
        """Return a deterministic user and capture lookup input."""
        user_lookup_calls.append(telegram_id)
        return build_user()

    async def fake_check_token_risk(
        _session: object,
        *,
        data: TokenRiskCheckData,
    ) -> TokenCheck:
        """Return a deterministic Medium risk token check."""
        risk_check_calls.append(data)
        return build_medium_token_check()

    monkeypatch.setattr(
        risk_check_service,
        "get_user_by_telegram_id_or_raise",
        fake_get_user_by_telegram_id_or_raise,
    )
    monkeypatch.setattr(
        risk_check_service,
        "check_token_risk",
        fake_check_token_risk,
    )

    state = FakeState(data=build_risk_check_state_data())
    message = FakeMessage(
        text=UNKNOWN_ADDRESS,
        from_user=FakeTelegramUser(),
    )

    run_async(
        handle_contract_address_flow(
            message=message,  # type: ignore[arg-type]
            state=state,  # type: ignore[arg-type]
            session=object(),  # type: ignore[arg-type]
        ),
    )

    assert user_lookup_calls == [TELEGRAM_ID]
    assert risk_check_calls == [
        TokenRiskCheckData(
            user_id=USER_ID,
            chain="eth",
            contract_address=UNKNOWN_ADDRESS,
        ),
    ]

    assert state.clear_called is True
    assert message.delete_called is True
    assert message.answers == []
    assert len(message.bot.edits) == 2

    loading_edit = message.bot.edits[0]
    assert loading_edit["text"] == RISK_CHECK_LOADING_TEXT
    assert loading_edit["reply_markup"] is None

    edit = message.bot.edits[1]
    text = edit["text"]

    assert "Risk level: <b>⚠️ Medium risk</b>" in text
    assert "Sell tax can be changed: detected" in text
    assert "Buy tax: 15%" in text
    assert UNKNOWN_ADDRESS in text

    assert "score" not in text.lower()
    assert "penalty" not in text.lower()
    assert "points" not in text.lower()
    assert edit["chat_id"] == RISK_CHECK_SCREEN_CHAT_ID
    assert edit["message_id"] == RISK_CHECK_SCREEN_MESSAGE_ID
    assert edit["reply_markup"] is not None


def test_handle_contract_address_flow_rejects_invalid_address_before_service_call(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Invalid contract input should not call user lookup or risk service."""

    async def fake_get_user_by_telegram_id_or_raise(
        *_args: object,
        **_kwargs: object,
    ) -> User:
        """Fail if user lookup is reached."""
        raise AssertionError("User lookup should not be called")

    async def fake_check_token_risk(
        *_args: object,
        **_kwargs: object,
    ) -> TokenCheck:
        """Fail if risk service is reached."""
        raise AssertionError("check_token_risk should not be called")

    monkeypatch.setattr(
        risk_check_service,
        "get_user_by_telegram_id_or_raise",
        fake_get_user_by_telegram_id_or_raise,
    )
    monkeypatch.setattr(
        risk_check_service,
        "check_token_risk",
        fake_check_token_risk,
    )

    state = FakeState(data=build_risk_check_state_data())
    message = FakeMessage(
        text="not-a-contract",
        from_user=FakeTelegramUser(),
    )

    run_async(
        handle_contract_address_flow(
            message=message,  # type: ignore[arg-type]
            state=state,  # type: ignore[arg-type]
            session=object(),  # type: ignore[arg-type]
        ),
    )

    assert state.clear_called is False
    assert message.delete_called is True
    assert message.answers == []
    assert len(message.bot.edits) == 1
    assert message.bot.edits[0]["text"] == INVALID_CONTRACT_ADDRESS_TEXT
    assert message.bot.edits[0]["reply_markup"] is not None


def test_handle_contract_address_flow_shows_provider_error_when_service_fails(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Provider failures should clear state and show risk check error text."""

    async def fake_get_user_by_telegram_id_or_raise(
        _session: object,
        *,
        telegram_id: int,
    ) -> User:
        """Return a deterministic user."""
        assert telegram_id == TELEGRAM_ID
        return build_user()

    async def fake_check_token_risk(
        _session: object,
        *,
        data: TokenRiskCheckData,
    ) -> TokenCheck:
        """Simulate token risk provider failure."""
        assert data.user_id == USER_ID
        assert data.chain == "eth"
        assert data.contract_address == UNKNOWN_ADDRESS

        raise SecurityProviderError("provider failed")

    monkeypatch.setattr(
        risk_check_service,
        "get_user_by_telegram_id_or_raise",
        fake_get_user_by_telegram_id_or_raise,
    )
    monkeypatch.setattr(
        risk_check_service,
        "check_token_risk",
        fake_check_token_risk,
    )

    state = FakeState(data=build_risk_check_state_data())
    message = FakeMessage(
        text=UNKNOWN_ADDRESS,
        from_user=FakeTelegramUser(),
    )

    run_async(
        handle_contract_address_flow(
            message=message,  # type: ignore[arg-type]
            state=state,  # type: ignore[arg-type]
            session=object(),  # type: ignore[arg-type]
        ),
    )

    assert state.clear_called is True
    assert message.delete_called is True
    assert message.answers == []
    assert len(message.bot.edits) == 2
    assert message.bot.edits[0]["text"] == RISK_CHECK_LOADING_TEXT
    assert message.bot.edits[0]["reply_markup"] is None
    assert message.bot.edits[1]["text"] == RISK_CHECK_FAILED_TEXT
    assert message.bot.edits[1]["reply_markup"] is not None


def test_handle_contract_address_flow_explains_token_not_found_on_network(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Missing provider token data should tell users to check the selected chain."""

    async def fake_get_user_by_telegram_id_or_raise(
        _session: object,
        *,
        telegram_id: int,
    ) -> User:
        """Return a deterministic user."""
        assert telegram_id == TELEGRAM_ID
        return build_user()

    async def fake_check_token_risk(
        _session: object,
        *,
        data: TokenRiskCheckData,
    ) -> TokenCheck:
        """Simulate a contract that is not found on the selected chain."""
        assert data.chain == "eth"
        assert data.contract_address == UNKNOWN_ADDRESS
        raise SecurityProviderError(GOPLUS_TOKEN_DATA_NOT_FOUND_ERROR)

    monkeypatch.setattr(
        risk_check_service,
        "get_user_by_telegram_id_or_raise",
        fake_get_user_by_telegram_id_or_raise,
    )
    monkeypatch.setattr(
        risk_check_service,
        "check_token_risk",
        fake_check_token_risk,
    )

    state = FakeState(data=build_risk_check_state_data())
    message = FakeMessage(
        text=UNKNOWN_ADDRESS,
        from_user=FakeTelegramUser(),
    )

    run_async(
        handle_contract_address_flow(
            message=message,  # type: ignore[arg-type]
            state=state,  # type: ignore[arg-type]
            session=object(),  # type: ignore[arg-type]
        ),
    )

    assert state.clear_called is True
    assert message.delete_called is True
    assert message.answers == []
    assert len(message.bot.edits) == 2
    assert message.bot.edits[0]["text"] == RISK_CHECK_LOADING_TEXT
    assert message.bot.edits[1]["text"] == RISK_CHECK_TOKEN_NOT_FOUND_TEXT
    assert message.bot.edits[1]["reply_markup"] is not None


def test_cancel_risk_check_flow_returns_to_main_menu(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Cancel should clear risk check state and render the root menu."""
    edits: list[dict[str, Any]] = []

    async def fake_edit_callback_message(
        callback: object,
        *,
        text: str,
        reply_markup: object | None = None,
    ) -> None:
        """Capture callback edits for assertions."""
        edits.append(
            {
                "callback": callback,
                "text": text,
                "reply_markup": reply_markup,
            },
        )

    monkeypatch.setattr(
        risk_check_service,
        "edit_callback_message",
        fake_edit_callback_message,
    )

    state = FakeState(data={"chain": "eth"})
    callback = FakeCallback()

    run_async(
        risk_check_service.cancel_risk_check_flow(
            callback=callback,  # type: ignore[arg-type]
            state=state,  # type: ignore[arg-type]
        ),
    )

    assert state.clear_called is True
    assert edits == [
        {
            "callback": callback,
            "text": MAIN_MENU_TEXT,
            "reply_markup": edits[0]["reply_markup"],
        },
    ]
    assert edits[0]["reply_markup"] is not None
