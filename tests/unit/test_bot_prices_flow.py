"""Unit tests for Telegram bot prices flow."""

from decimal import Decimal
from typing import Any

import pytest
from app.bot.services import prices as prices_service
from app.bot.services.prices import show_prices_flow
from app.bot.texts import PRICES_LOADING_TEXT
from app.core.exceptions import PriceProviderError
from app.services.prices_service import MarketPrice


class FakeCallback:
    """Minimal callback object for prices flow tests."""


@pytest.mark.asyncio
async def test_show_prices_flow_edits_loading_before_prices(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Prices screen should show immediate loading feedback before results."""
    edits: list[dict[str, Any]] = []

    async def fake_edit_callback_message(
        callback: object,
        *,
        text: str,
        reply_markup: object | None = None,
        answer_callback: bool = True,
    ) -> None:
        edits.append(
            {
                "callback": callback,
                "text": text,
                "reply_markup": reply_markup,
                "answer_callback": answer_callback,
            },
        )

    async def fake_get_supported_market_prices(_provider: object) -> list[MarketPrice]:
        return [
            MarketPrice(
                coin_id="bitcoin",
                symbol="BTC",
                name="Bitcoin",
                price_usd=Decimal("50000"),
            ),
        ]

    monkeypatch.setattr(
        prices_service,
        "edit_callback_message",
        fake_edit_callback_message,
    )
    monkeypatch.setattr(
        prices_service,
        "get_supported_market_prices",
        fake_get_supported_market_prices,
    )

    callback = FakeCallback()

    await show_prices_flow(callback=callback)  # type: ignore[arg-type]

    assert len(edits) == 2
    assert edits[0] == {
        "callback": callback,
        "text": PRICES_LOADING_TEXT,
        "reply_markup": edits[0]["reply_markup"],
        "answer_callback": True,
    }
    assert "<b>BTC</b> -" in edits[0]["text"]
    assert "<b>BNB</b> -" in edits[0]["text"]
    assert edits[0]["reply_markup"] is not None
    assert "BTC" in edits[1]["text"]
    assert edits[1]["reply_markup"] is not None
    assert edits[1]["answer_callback"] is False


@pytest.mark.asyncio
async def test_show_prices_flow_replaces_loading_with_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Provider failures should replace the loading screen with an error."""
    edits: list[dict[str, Any]] = []

    async def fake_edit_callback_message(
        _callback: object,
        *,
        text: str,
        reply_markup: object | None = None,
        answer_callback: bool = True,
    ) -> None:
        edits.append(
            {
                "text": text,
                "reply_markup": reply_markup,
                "answer_callback": answer_callback,
            },
        )

    async def fake_get_supported_market_prices(_provider: object) -> list[MarketPrice]:
        raise PriceProviderError("provider failed")

    monkeypatch.setattr(
        prices_service,
        "edit_callback_message",
        fake_edit_callback_message,
    )
    monkeypatch.setattr(
        prices_service,
        "get_supported_market_prices",
        fake_get_supported_market_prices,
    )

    await show_prices_flow(callback=FakeCallback())  # type: ignore[arg-type]

    assert len(edits) == 2
    assert edits[0]["text"] == PRICES_LOADING_TEXT
    assert edits[1]["reply_markup"] is not None
    assert edits[1]["answer_callback"] is False
