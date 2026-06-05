"""Unit tests for Telegram send rate limiter."""

import pytest
from app.worker.telegram_rate_limiter import TelegramSendRateLimiter


@pytest.mark.asyncio
async def test_telegram_send_rate_limiter_spaces_out_acquire_calls() -> None:
    """Limiter should delay the second acquire when interval is large."""
    limiter = TelegramSendRateLimiter(messages_per_second=2.0)

    await limiter.acquire()
    await limiter.acquire()

    assert limiter._min_interval_seconds == 0.5


def test_telegram_send_rate_limiter_rejects_non_positive_rate() -> None:
    """Invalid rate configuration should fail fast."""
    with pytest.raises(ValueError, match="greater than zero"):
        TelegramSendRateLimiter(messages_per_second=0)
