"""Unit tests for safe callback answer helper."""

from unittest.mock import AsyncMock, MagicMock

import pytest
from aiogram.exceptions import TelegramBadRequest
from aiogram.methods import AnswerCallbackQuery
from app.bot.utils.callbacks import safe_callback_answer


@pytest.mark.asyncio
async def test_safe_callback_answer_ignores_stale_query_error() -> None:
    """Expired callback queries should not crash the bot."""
    callback = MagicMock()
    callback.answer = AsyncMock(
        side_effect=TelegramBadRequest(
            method=AnswerCallbackQuery(callback_query_id="1"),
            message=(
                "Bad Request: query is too old and response timeout expired "
                "or query ID is invalid"
            ),
        ),
    )

    await safe_callback_answer(callback, "Too many requests")

    callback.answer.assert_awaited_once()
