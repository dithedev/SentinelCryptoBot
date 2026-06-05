"""In-memory rate limiting helpers for bot and API (per process)."""

import time


class MinIntervalRateLimiter:
    """Allow at most one event per key every min_interval_seconds."""

    def __init__(self, *, min_interval_seconds: float) -> None:
        if min_interval_seconds <= 0:
            message = "min_interval_seconds must be greater than zero"
            raise ValueError(message)

        self._min_interval_seconds = min_interval_seconds
        self._last_allowed_at: dict[str, float] = {}

    def allow(self, key: str) -> bool:
        """Return True when the key may proceed; False when throttled."""
        now = time.monotonic()
        last_allowed_at = self._last_allowed_at.get(key)

        if (
            last_allowed_at is not None
            and now - last_allowed_at < self._min_interval_seconds
        ):
            return False

        self._last_allowed_at[key] = now
        return True


class FixedWindowRateLimiter:
    """Allow up to max_calls events per key within each fixed time window."""

    def __init__(self, *, max_calls: int, period_seconds: float) -> None:
        if max_calls <= 0:
            message = "max_calls must be greater than zero"
            raise ValueError(message)

        if period_seconds <= 0:
            message = "period_seconds must be greater than zero"
            raise ValueError(message)

        self._max_calls = max_calls
        self._period_seconds = period_seconds
        self._windows: dict[str, tuple[float, int]] = {}

    def allow(self, key: str) -> bool:
        """Return True when the key may proceed; False when throttled."""
        now = time.monotonic()
        window_start, count = self._windows.get(key, (now, 0))

        if now - window_start >= self._period_seconds:
            window_start = now
            count = 0

        if count >= self._max_calls:
            self._windows[key] = (window_start, count)
            return False

        self._windows[key] = (window_start, count + 1)
        return True
