"""Unit tests for whale alert worker orchestration."""

from datetime import UTC, datetime
from decimal import Decimal
from typing import Any

import pytest
from app.database.models.user import User
from app.database.models.whale import (
    WhaleAlertSettings,
    WhaleEvent,
    WhaleEventType,
    WhaleNotificationDeliveryStatus,
)
from app.integrations.whales import WhaleProviderEvent
from app.worker.whale_alert_worker import WhaleAlertWorker


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
    """Minimal settings object required by WhaleAlertWorker."""

    price_check_interval_seconds = 60
    whale_check_interval_seconds = 120


class FakeProvider:
    """Fake whale provider returning deterministic events."""

    def __init__(self, events: list[WhaleProviderEvent]) -> None:
        self.events = events

    async def get_latest_events(self) -> list[WhaleProviderEvent]:
        return self.events


def _build_provider_event() -> WhaleProviderEvent:
    """Build one deterministic provider event."""
    return WhaleProviderEvent(
        coin_id="bitcoin",
        network="btc",
        transaction_hash="0xabc",
        amount=Decimal("10"),
        amount_usd=Decimal("1000000"),
        event_type=WhaleEventType.TRANSFER,
        detected_at=datetime(2026, 5, 20, 10, 0, tzinfo=UTC),
        raw_payload={"source": "test"},
    )


def _build_stored_event() -> WhaleEvent:
    """Build one deterministic stored whale event."""
    return WhaleEvent(
        id=1,
        coin_id="bitcoin",
        symbol="BTC",
        network="btc",
        transaction_hash="0xabc",
        from_address=None,
        to_address=None,
        amount=Decimal("10"),
        amount_usd=Decimal("1000000"),
        event_type=WhaleEventType.TRANSFER,
        detected_at=datetime(2026, 5, 20, 10, 0, tzinfo=UTC),
        raw_payload={"source": "test"},
        created_at=datetime(2026, 5, 20, 10, 0, tzinfo=UTC),
    )


def _build_matching_settings() -> WhaleAlertSettings:
    """Build enabled whale settings with loaded user relationship."""
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
    settings = WhaleAlertSettings(
        id=1,
        user_id=1,
        is_enabled=True,
        min_usd_value=Decimal("500000"),
        created_at=datetime(2026, 5, 20, 10, 0, tzinfo=UTC),
        updated_at=datetime(2026, 5, 20, 10, 0, tzinfo=UTC),
    )
    settings.user = user

    return settings


@pytest.mark.asyncio
async def test_whale_alert_worker_commits_without_events() -> None:
    """No provider events should produce no DB session and no notifications."""
    session = FakeSession()
    worker = WhaleAlertWorker(
        bot=object(),  # type: ignore[arg-type]
        session_maker=FakeSessionMaker(session),  # type: ignore[arg-type]
        settings=FakeSettings(),  # type: ignore[arg-type]
        provider=FakeProvider([]),
    )

    await worker.run_once()

    assert session.was_committed is False


@pytest.mark.asyncio
async def test_whale_alert_worker_stores_new_event_and_sends_notification(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """New whale events should be stored and sent to matching users."""
    session = FakeSession()
    stored_event = _build_stored_event()
    matching_settings = [_build_matching_settings()]
    sent_notifications: list[tuple[int, WhaleEvent]] = []
    limiter_was_called = False

    async def fake_create_whale_event_if_new(
        _session: object,
        *,
        data: object,
    ) -> object:
        assert data is not None

        class Result:
            event = stored_event
            was_created = True

        return Result()

    async def fake_get_matching_whale_settings(
        _session: object,
        *,
        event: WhaleEvent,
    ) -> list[WhaleAlertSettings]:
        assert event is stored_event
        return matching_settings

    class FakeDelivery:
        status = WhaleNotificationDeliveryStatus.PENDING
        attempts = 0

    async def fake_get_or_create_delivery(
        _session: object,
        *,
        whale_event_id: int,
        user_id: int,
    ) -> FakeDelivery:
        assert whale_event_id == stored_event.id
        assert user_id == matching_settings[0].user_id
        return FakeDelivery()

    async def fake_mark_delivery_sent(
        _session: object,
        *,
        delivery: FakeDelivery,
    ) -> FakeDelivery:
        delivery.status = WhaleNotificationDeliveryStatus.SENT
        return delivery

    class FakeLimiter:
        async def acquire(self) -> None:
            nonlocal limiter_was_called
            limiter_was_called = True

    async def fake_send_whale_alert_notification(
        _bot: object,
        *,
        telegram_id: int,
        event: WhaleEvent,
    ) -> None:
        sent_notifications.append((telegram_id, event))

    monkeypatch.setattr(
        "app.worker.whale_alert_worker.get_or_create_whale_notification_delivery",
        fake_get_or_create_delivery,
    )
    monkeypatch.setattr(
        "app.worker.whale_alert_worker.mark_whale_notification_delivery_sent",
        fake_mark_delivery_sent,
    )
    monkeypatch.setattr(
        "app.worker.whale_alert_worker.create_whale_event_if_new",
        fake_create_whale_event_if_new,
    )
    monkeypatch.setattr(
        "app.worker.whale_alert_worker.get_matching_whale_settings",
        fake_get_matching_whale_settings,
    )
    monkeypatch.setattr(
        "app.worker.whale_alert_worker.send_whale_alert_notification",
        fake_send_whale_alert_notification,
    )

    worker = WhaleAlertWorker(
        bot=object(),  # type: ignore[arg-type]
        session_maker=FakeSessionMaker(session),  # type: ignore[arg-type]
        settings=FakeSettings(),  # type: ignore[arg-type]
        provider=FakeProvider([_build_provider_event()]),
        telegram_rate_limiter=FakeLimiter(),  # type: ignore[arg-type]
    )

    await worker.run_once()

    assert session.was_committed is True
    assert limiter_was_called is True
    assert sent_notifications == [(123456, stored_event)]


@pytest.mark.asyncio
async def test_whale_alert_worker_skips_duplicate_events_when_already_sent(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Duplicate whale events should not resend after successful delivery."""
    session = FakeSession()
    stored_event = _build_stored_event()
    sent_notifications: list[tuple[int, WhaleEvent]] = []

    async def fake_create_whale_event_if_new(
        _session: object,
        *,
        data: object,
    ) -> object:
        assert data is not None

        class Result:
            event = stored_event
            was_created = False

        return Result()

    async def fake_get_matching_whale_settings(
        _session: object,
        *,
        event: WhaleEvent,
    ) -> list[WhaleAlertSettings]:
        assert event is stored_event
        return [_build_matching_settings()]

    class FakeDelivery:
        status = WhaleNotificationDeliveryStatus.SENT
        attempts = 1

    async def fake_get_or_create_delivery(
        _session: object,
        *,
        whale_event_id: int,
        user_id: int,
    ) -> FakeDelivery:
        return FakeDelivery()

    async def fake_send_whale_alert_notification(
        _bot: object,
        *,
        telegram_id: int,
        event: WhaleEvent,
    ) -> None:
        sent_notifications.append((telegram_id, event))

    monkeypatch.setattr(
        "app.worker.whale_alert_worker.create_whale_event_if_new",
        fake_create_whale_event_if_new,
    )
    monkeypatch.setattr(
        "app.worker.whale_alert_worker.get_matching_whale_settings",
        fake_get_matching_whale_settings,
    )
    monkeypatch.setattr(
        "app.worker.whale_alert_worker.get_or_create_whale_notification_delivery",
        fake_get_or_create_delivery,
    )
    monkeypatch.setattr(
        "app.worker.whale_alert_worker.send_whale_alert_notification",
        fake_send_whale_alert_notification,
    )

    worker = WhaleAlertWorker(
        bot=object(),  # type: ignore[arg-type]
        session_maker=FakeSessionMaker(session),  # type: ignore[arg-type]
        settings=FakeSettings(),  # type: ignore[arg-type]
        provider=FakeProvider([_build_provider_event()]),
    )

    await worker.run_once()

    assert session.was_committed is True
    assert sent_notifications == []
