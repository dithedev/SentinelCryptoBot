"""Async rate limiter for Telegram message delivery in workers."""

import asyncio
import time


class TelegramSendRateLimiter:
    """Simple global async rate limiter for Telegram sends.

    The limiter spaces out message sends to reduce burst traffic that can
    trigger Telegram rate limits when many alerts fire in one worker cycle.
    """

    def __init__(self, *, messages_per_second: float = 20.0) -> None:
        if messages_per_second <= 0:
            message = "messages_per_second must be greater than zero"
            raise ValueError(message)

        self._min_interval_seconds = 1.0 / messages_per_second
        self._lock = asyncio.Lock()
        self._next_allowed_at = 0.0

    async def acquire(self) -> None:
        """Wait until the next Telegram send slot is available."""
        async with self._lock:
            now = time.monotonic()
            wait_seconds = self._next_allowed_at - now

            if wait_seconds > 0:
                await asyncio.sleep(wait_seconds)
                now = time.monotonic()

            self._next_allowed_at = now + self._min_interval_seconds
