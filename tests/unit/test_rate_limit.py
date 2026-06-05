"""Unit tests for in-memory rate limiters."""

import pytest
from app.core.rate_limit import FixedWindowRateLimiter, MinIntervalRateLimiter


def test_min_interval_rate_limiter_blocks_rapid_repeats() -> None:
    """Second call for the same key should be throttled."""
    limiter = MinIntervalRateLimiter(min_interval_seconds=10.0)

    assert limiter.allow("user-1") is True
    assert limiter.allow("user-1") is False


def test_min_interval_rate_limiter_allows_different_keys() -> None:
    """Different keys should not share the same throttle window."""
    limiter = MinIntervalRateLimiter(min_interval_seconds=10.0)

    assert limiter.allow("user-1") is True
    assert limiter.allow("user-2") is True


def test_min_interval_rate_limiter_rejects_non_positive_interval() -> None:
    """Invalid interval configuration should fail fast."""
    with pytest.raises(ValueError, match="greater than zero"):
        MinIntervalRateLimiter(min_interval_seconds=0)


def test_fixed_window_rate_limiter_blocks_after_max_calls() -> None:
    """Limiter should reject calls above the configured window cap."""
    limiter = FixedWindowRateLimiter(max_calls=2, period_seconds=60.0)

    assert limiter.allow("client-1") is True
    assert limiter.allow("client-1") is True
    assert limiter.allow("client-1") is False


def test_fixed_window_rate_limiter_rejects_invalid_configuration() -> None:
    """Invalid window configuration should fail fast."""
    with pytest.raises(ValueError, match="greater than zero"):
        FixedWindowRateLimiter(max_calls=0, period_seconds=60.0)

    with pytest.raises(ValueError, match="greater than zero"):
        FixedWindowRateLimiter(max_calls=1, period_seconds=0)
