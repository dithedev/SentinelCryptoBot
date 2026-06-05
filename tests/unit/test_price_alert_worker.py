"""Unit tests for price alert worker orchestration."""

from datetime import UTC, datetime
from decimal import Decimal
from typing import Any

import pytest
from app.database.models.alert import Alert, AlertCondition, AlertStatus
from app.database.models.user import User
from app.worker.price_alert_worker import PriceAlertWorker


class FakeSession:
    """Tiny async session used by the worker tests."""

    def __init__(self) -> None:
        self.was_committed = False

    async def __aenter__(self) -> "FakeSession":
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        traceback: object | None,
    ) -> None:
        return None

    async def commit(self) -> None:
        self.was_committed = True


class FakeSessionMaker:
    """Callable fake matching AsyncSessionFactory."""

    def __init__(self, session: FakeSession) -> None:
        self.session = session

    def __call__(self, **_kwargs: Any) -> FakeSession:
        return self.session


class FakeSettings:
    """Minimal settings object required by PriceAlertWorker."""

    price_check_interval_seconds = 60
    whale_check_interval_seconds = 120


def _build_active_alert() -> Alert:
    """Build one active alert with a loaded user."""
    user = User(
        id=1,
        telegram_id=123456,
        username="demo",
        first_name="Demo",
        last_name=None,
        is_active=True,
        created_at=datetime(2026, 5, 20, 10, 0, tzinfo=UTC),
        updated_at=datetime(2026, 5, 20, 10, 0, tzinfo=UTC),
    )
    alert = Alert(
        id=1,
        user_id=1,
        coin_id="bitcoin",
        symbol="BTC",
        target_price=Decimal("50000"),
        condition=AlertCondition.ABOVE,
        status=AlertStatus.ACTIVE,
        triggered_at=None,
        created_at=datetime(2026, 5, 20, 10, 0, tzinfo=UTC),
        updated_at=datetime(2026, 5, 20, 10, 0, tzinfo=UTC),
    )
    alert.user = user

    return alert


@pytest.mark.asyncio
async def test_price_alert_worker_claims_before_notification(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Triggered alerts should be claimed before Telegram delivery."""
    session = FakeSession()
    alert = _build_active_alert()
    claim_was_called = False
    notification_was_sent = False
    limiter_was_called = False

    async def fake_get_all_active_alerts(_session: object) -> list[Alert]:
        return [alert]

    async def fake_get_prices(_self: object, _coin_ids: set[str]) -> dict[str, Decimal]:
        return {"bitcoin": Decimal("60000")}

    async def fake_try_claim_alert_trigger(
        _session: object,
        *,
        alert_id: int,
    ) -> Alert:
        nonlocal claim_was_called
        claim_was_called = True
        assert alert_id == alert.id
        return alert

    class FakeLimiter:
        async def acquire(self) -> None:
            nonlocal limiter_was_called
            limiter_was_called = True

    async def fake_send_price_alert_notification(
        _bot: object,
        **kwargs: Any,
    ) -> None:
        nonlocal notification_was_sent
        notification_was_sent = True
        assert kwargs["telegram_id"] == 123456

    monkeypatch.setattr(
        "app.worker.price_alert_worker.get_all_active_alerts",
        fake_get_all_active_alerts,
    )
    monkeypatch.setattr(
        PriceAlertWorker,
        "_get_prices",
        fake_get_prices,
    )
    monkeypatch.setattr(
        "app.worker.price_alert_worker.try_claim_alert_trigger",
        fake_try_claim_alert_trigger,
    )
    monkeypatch.setattr(
        "app.worker.price_alert_worker.send_price_alert_notification",
        fake_send_price_alert_notification,
    )

    worker = PriceAlertWorker(
        bot=object(),  # type: ignore[arg-type]
        session_maker=FakeSessionMaker(session),  # type: ignore[arg-type]
        settings=FakeSettings(),  # type: ignore[arg-type]
        telegram_rate_limiter=FakeLimiter(),  # type: ignore[arg-type]
    )

    await worker.run_once()

    assert session.was_committed is True
    assert claim_was_called is True
    assert limiter_was_called is True
    assert notification_was_sent is True
