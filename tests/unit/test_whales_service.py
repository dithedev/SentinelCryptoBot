"""Unit tests for whale alert domain service.

These tests patch repository functions and verify business rules without a real
database connection.
"""

from datetime import UTC, datetime
from decimal import Decimal
from typing import Any

import pytest
from app.core.constants import DEFAULT_WHALE_MIN_USD_VALUE
from app.core.exceptions import UserNotFoundError, ValidationError
from app.database.models.whale import WhaleAlertSettings, WhaleEvent, WhaleEventType
from app.services.whales_service import (
    UserWhaleSettings,
    WhaleEventCreateData,
    WhaleSettingsUpdateData,
    create_whale_event_if_new,
    get_latest_whale_events_page,
    get_or_create_user_whale_settings,
    get_or_create_user_whale_settings_by_telegram_id,
    should_notify_user_about_whale_event,
    update_loaded_user_whale_settings,
    update_user_whale_settings,
)
from sqlalchemy.exc import IntegrityError


def _build_whale_settings(
    *,
    is_enabled: bool = True,
    min_usd_value: Decimal = Decimal("1000000"),
) -> WhaleAlertSettings:
    """Build deterministic whale settings for service tests."""
    created_at = datetime(2026, 5, 20, 10, 0, tzinfo=UTC)

    return WhaleAlertSettings(
        id=1,
        user_id=1,
        is_enabled=is_enabled,
        min_usd_value=min_usd_value,
        created_at=created_at,
        updated_at=created_at,
    )


def _build_whale_event(
    *,
    amount_usd: Decimal = Decimal("1500000"),
    transaction_hash: str = "0xabc",
) -> WhaleEvent:
    """Build deterministic whale event for service tests."""
    detected_at = datetime(2026, 5, 20, 10, 0, tzinfo=UTC)

    return WhaleEvent(
        id=1,
        coin_id="bitcoin",
        symbol="BTC",
        network="btc",
        transaction_hash=transaction_hash,
        from_address="from",
        to_address="to",
        amount=Decimal("15.000000000000000000"),
        amount_usd=amount_usd,
        event_type=WhaleEventType.TRANSFER,
        detected_at=detected_at,
        raw_payload={},
        created_at=detected_at,
    )


@pytest.mark.asyncio
async def test_get_or_create_user_whale_settings_returns_existing_settings(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Existing settings should be returned without creating a new row."""
    existing_settings = _build_whale_settings()
    create_was_called = False

    async def fake_get_settings(
        _session: object,
        *,
        user_id: int,
    ) -> WhaleAlertSettings | None:
        assert user_id == 1
        return existing_settings

    async def fake_create_settings(
        _session: object,
        **_kwargs: Any,
    ) -> WhaleAlertSettings:
        nonlocal create_was_called
        create_was_called = True
        return existing_settings

    monkeypatch.setattr(
        "app.services.whales_service.get_whale_alert_settings_by_user_id",
        fake_get_settings,
    )
    monkeypatch.setattr(
        "app.services.whales_service.create_whale_alert_settings",
        fake_create_settings,
    )

    result = await get_or_create_user_whale_settings(
        object(),  # type: ignore[arg-type]
        user_id=1,
    )

    assert result is existing_settings
    assert create_was_called is False


@pytest.mark.asyncio
async def test_get_or_create_user_whale_settings_creates_default_settings(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Missing settings should be created with safe defaults."""
    created_settings = _build_whale_settings(
        is_enabled=False,
        min_usd_value=DEFAULT_WHALE_MIN_USD_VALUE,
    )

    async def fake_get_settings(
        _session: object,
        *,
        user_id: int,
    ) -> WhaleAlertSettings | None:
        assert user_id == 1
        return None

    async def fake_create_settings(
        _session: object,
        *,
        user_id: int,
        is_enabled: bool,
        min_usd_value: Decimal,
    ) -> WhaleAlertSettings:
        assert user_id == 1
        assert is_enabled is False
        assert min_usd_value == DEFAULT_WHALE_MIN_USD_VALUE
        return created_settings

    monkeypatch.setattr(
        "app.services.whales_service.get_whale_alert_settings_by_user_id",
        fake_get_settings,
    )
    monkeypatch.setattr(
        "app.services.whales_service.create_whale_alert_settings",
        fake_create_settings,
    )

    result = await get_or_create_user_whale_settings(
        object(),  # type: ignore[arg-type]
        user_id=1,
    )

    assert result is created_settings


@pytest.mark.asyncio
async def test_get_or_create_user_whale_settings_by_telegram_id_returns_existing(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Telegram lookup should return user id and settings from one repository call."""
    existing_settings = _build_whale_settings()
    create_was_called = False

    async def fake_get_user_settings(
        _session: object,
        *,
        telegram_id: int,
    ) -> tuple[int, WhaleAlertSettings | None] | None:
        assert telegram_id == 777
        return 1, existing_settings

    async def fake_create_settings(
        _session: object,
        **_kwargs: Any,
    ) -> WhaleAlertSettings:
        nonlocal create_was_called
        create_was_called = True
        return existing_settings

    monkeypatch.setattr(
        "app.services.whales_service.get_user_id_and_whale_alert_settings_by_telegram_id",
        fake_get_user_settings,
    )
    monkeypatch.setattr(
        "app.services.whales_service.create_whale_alert_settings",
        fake_create_settings,
    )

    result = await get_or_create_user_whale_settings_by_telegram_id(
        object(),  # type: ignore[arg-type]
        telegram_id=777,
    )

    assert result == UserWhaleSettings(user_id=1, settings=existing_settings)
    assert create_was_called is False


@pytest.mark.asyncio
async def test_get_or_create_user_whale_settings_by_telegram_id_creates_default(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Missing joined settings should be created for an existing user."""
    created_settings = _build_whale_settings(
        is_enabled=False,
        min_usd_value=DEFAULT_WHALE_MIN_USD_VALUE,
    )

    async def fake_get_user_settings(
        _session: object,
        *,
        telegram_id: int,
    ) -> tuple[int, WhaleAlertSettings | None] | None:
        assert telegram_id == 777
        return 1, None

    async def fake_create_settings(
        _session: object,
        *,
        user_id: int,
        is_enabled: bool,
        min_usd_value: Decimal,
    ) -> WhaleAlertSettings:
        assert user_id == 1
        assert is_enabled is False
        assert min_usd_value == DEFAULT_WHALE_MIN_USD_VALUE
        return created_settings

    monkeypatch.setattr(
        "app.services.whales_service.get_user_id_and_whale_alert_settings_by_telegram_id",
        fake_get_user_settings,
    )
    monkeypatch.setattr(
        "app.services.whales_service.create_whale_alert_settings",
        fake_create_settings,
    )

    result = await get_or_create_user_whale_settings_by_telegram_id(
        object(),  # type: ignore[arg-type]
        telegram_id=777,
    )

    assert result == UserWhaleSettings(user_id=1, settings=created_settings)


@pytest.mark.asyncio
async def test_get_or_create_user_whale_settings_by_telegram_id_raises_for_missing_user(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Telegram lookup should preserve existing missing-user behavior."""

    async def fake_get_user_settings(
        _session: object,
        *,
        telegram_id: int,
    ) -> tuple[int, WhaleAlertSettings | None] | None:
        assert telegram_id == 777
        return None

    monkeypatch.setattr(
        "app.services.whales_service.get_user_id_and_whale_alert_settings_by_telegram_id",
        fake_get_user_settings,
    )

    with pytest.raises(UserNotFoundError):
        await get_or_create_user_whale_settings_by_telegram_id(
            object(),  # type: ignore[arg-type]
            telegram_id=777,
        )


@pytest.mark.asyncio
async def test_update_user_whale_settings_validates_and_normalizes_threshold(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Whale alert threshold should be normalized to cents before storing."""
    existing_settings = _build_whale_settings(is_enabled=False)

    async def fake_get_or_create(
        _session: object,
        *,
        user_id: int,
    ) -> WhaleAlertSettings:
        assert user_id == 1
        return existing_settings

    async def fake_update_settings(
        _session: object,
        *,
        settings: WhaleAlertSettings,
        is_enabled: bool | None = None,
        min_usd_value: Decimal | None = None,
    ) -> WhaleAlertSettings:
        assert settings is existing_settings
        assert is_enabled is True
        assert min_usd_value == Decimal("2500000.12")

        settings.is_enabled = bool(is_enabled)
        settings.min_usd_value = min_usd_value or settings.min_usd_value
        return settings

    monkeypatch.setattr(
        "app.services.whales_service.get_or_create_user_whale_settings",
        fake_get_or_create,
    )
    monkeypatch.setattr(
        "app.services.whales_service.update_whale_alert_settings",
        fake_update_settings,
    )

    result = await update_user_whale_settings(
        object(),  # type: ignore[arg-type]
        data=WhaleSettingsUpdateData(
            user_id=1,
            is_enabled=True,
            min_usd_value=Decimal("2500000.123"),
        ),
    )

    assert result.is_enabled is True
    assert result.min_usd_value == Decimal("2500000.12")


@pytest.mark.asyncio
async def test_update_user_whale_settings_can_disable_without_threshold_change(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Disabling whale alerts should not require a threshold update."""
    existing_settings = _build_whale_settings(is_enabled=True)

    async def fake_get_or_create(
        _session: object,
        *,
        user_id: int,
    ) -> WhaleAlertSettings:
        assert user_id == 1
        return existing_settings

    async def fake_update_settings(
        _session: object,
        *,
        settings: WhaleAlertSettings,
        is_enabled: bool | None = None,
        min_usd_value: Decimal | None = None,
    ) -> WhaleAlertSettings:
        assert settings is existing_settings
        assert is_enabled is False
        assert min_usd_value is None

        settings.is_enabled = False
        return settings

    monkeypatch.setattr(
        "app.services.whales_service.get_or_create_user_whale_settings",
        fake_get_or_create,
    )
    monkeypatch.setattr(
        "app.services.whales_service.update_whale_alert_settings",
        fake_update_settings,
    )

    result = await update_user_whale_settings(
        object(),  # type: ignore[arg-type]
        data=WhaleSettingsUpdateData(
            user_id=1,
            is_enabled=False,
        ),
    )

    assert result.is_enabled is False
    assert result.min_usd_value == Decimal("1000000")


@pytest.mark.asyncio
async def test_update_loaded_user_whale_settings_reuses_existing_settings(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Already-loaded settings should be updated without another settings lookup."""
    existing_settings = _build_whale_settings(is_enabled=False)

    async def fake_update_settings(
        _session: object,
        *,
        settings: WhaleAlertSettings,
        is_enabled: bool | None = None,
        min_usd_value: Decimal | None = None,
    ) -> WhaleAlertSettings:
        assert settings is existing_settings
        assert is_enabled is True
        assert min_usd_value == Decimal("2500000.12")

        settings.is_enabled = True
        settings.min_usd_value = min_usd_value or settings.min_usd_value
        return settings

    monkeypatch.setattr(
        "app.services.whales_service.update_whale_alert_settings",
        fake_update_settings,
    )

    result = await update_loaded_user_whale_settings(
        object(),  # type: ignore[arg-type]
        settings=existing_settings,
        is_enabled=True,
        min_usd_value=Decimal("2500000.123"),
    )

    assert result.is_enabled is True
    assert result.min_usd_value == Decimal("2500000.12")


@pytest.mark.asyncio
async def test_update_user_whale_settings_rejects_too_low_threshold(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Too small thresholds should be rejected by the domain layer."""
    existing_settings = _build_whale_settings()

    async def fake_get_or_create(
        _session: object,
        *,
        user_id: int,
    ) -> WhaleAlertSettings:
        assert user_id == 1
        return existing_settings

    monkeypatch.setattr(
        "app.services.whales_service.get_or_create_user_whale_settings",
        fake_get_or_create,
    )

    with pytest.raises(ValidationError):
        await update_user_whale_settings(
            object(),  # type: ignore[arg-type]
            data=WhaleSettingsUpdateData(
                user_id=1,
                min_usd_value=Decimal("999.99"),
            ),
        )


@pytest.mark.asyncio
async def test_create_whale_event_if_new_returns_existing_event(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Duplicate transaction hashes should not create new whale events."""
    existing_event = _build_whale_event(transaction_hash="0xabc")
    create_was_called = False

    async def fake_get_event(
        _session: object,
        *,
        transaction_hash: str,
    ) -> WhaleEvent | None:
        assert transaction_hash == "0xabc"
        return existing_event

    async def fake_create_event(
        _session: object,
        **_kwargs: Any,
    ) -> WhaleEvent:
        nonlocal create_was_called
        create_was_called = True
        return existing_event

    monkeypatch.setattr(
        "app.services.whales_service.get_whale_event_by_transaction_hash",
        fake_get_event,
    )
    monkeypatch.setattr(
        "app.services.whales_service.create_whale_event",
        fake_create_event,
    )

    result = await create_whale_event_if_new(
        object(),  # type: ignore[arg-type]
        data=WhaleEventCreateData(
            coin_id="bitcoin",
            network="btc",
            transaction_hash=" 0xabc ",
            amount=Decimal("15"),
            amount_usd=Decimal("1500000"),
        ),
    )

    assert result.event is existing_event
    assert result.was_created is False
    assert create_was_called is False


@pytest.mark.asyncio
async def test_create_whale_event_if_new_normalizes_and_creates_event(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """New whale events should be normalized before persistence."""
    created_event = _build_whale_event(
        amount_usd=Decimal("1500000.12"),
        transaction_hash="0xnew",
    )

    async def fake_get_event(
        _session: object,
        *,
        transaction_hash: str,
    ) -> WhaleEvent | None:
        assert transaction_hash == "0xnew"
        return None

    async def fake_create_event(
        _session: object,
        *,
        coin_id: str,
        symbol: str,
        network: str,
        transaction_hash: str,
        from_address: str | None,
        to_address: str | None,
        amount: Decimal,
        amount_usd: Decimal,
        event_type: WhaleEventType,
        detected_at: datetime,
        raw_payload: dict[str, Any],
    ) -> WhaleEvent:
        assert coin_id == "bitcoin"
        assert symbol == "BTC"
        assert network == "btc"
        assert transaction_hash == "0xnew"
        assert from_address is None
        assert to_address == "receiver"
        assert amount == Decimal("15.000000000000000000")
        assert amount_usd == Decimal("1500000.12")
        assert event_type == WhaleEventType.EXCHANGE_OUTFLOW
        assert detected_at == datetime(2026, 5, 20, 10, 0, tzinfo=UTC)
        assert raw_payload == {"source": "test"}

        return created_event

    monkeypatch.setattr(
        "app.services.whales_service.get_whale_event_by_transaction_hash",
        fake_get_event,
    )
    monkeypatch.setattr(
        "app.services.whales_service.create_whale_event",
        fake_create_event,
    )

    result = await create_whale_event_if_new(
        object(),  # type: ignore[arg-type]
        data=WhaleEventCreateData(
            coin_id=" Bitcoin ",
            network=" BTC ",
            transaction_hash=" 0xnew ",
            amount=Decimal("15"),
            amount_usd=Decimal("1500000.123"),
            event_type=WhaleEventType.EXCHANGE_OUTFLOW,
            from_address=" ",
            to_address=" receiver ",
            detected_at=datetime(2026, 5, 20, 10, 0, tzinfo=UTC),
            raw_payload={"source": "test"},
        ),
    )

    assert result.event is created_event
    assert result.was_created is True


@pytest.mark.asyncio
async def test_create_whale_event_if_new_rejects_invalid_amount(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Whale events with zero token amount should be rejected."""

    async def fake_get_event(
        _session: object,
        *,
        transaction_hash: str,
    ) -> WhaleEvent | None:
        assert transaction_hash == "0xnew"
        return None

    monkeypatch.setattr(
        "app.services.whales_service.get_whale_event_by_transaction_hash",
        fake_get_event,
    )

    with pytest.raises(ValidationError):
        await create_whale_event_if_new(
            object(),  # type: ignore[arg-type]
            data=WhaleEventCreateData(
                coin_id="bitcoin",
                network="btc",
                transaction_hash="0xnew",
                amount=Decimal("0"),
                amount_usd=Decimal("1500000"),
            ),
        )


@pytest.mark.asyncio
async def test_get_latest_whale_events_page_loads_one_extra_row(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Pagination should use one extra row to calculate has_more cheaply."""
    events = [
        _build_whale_event(transaction_hash="0x1"),
        _build_whale_event(transaction_hash="0x2"),
        _build_whale_event(transaction_hash="0x3"),
    ]

    async def fake_list_events(
        _session: object,
        *,
        limit: int,
        offset: int = 0,
    ) -> list[WhaleEvent]:
        assert limit == 3
        assert offset == 10
        return events

    async def fake_count_events(_session: object) -> int:
        return 19

    monkeypatch.setattr(
        "app.services.whales_service.count_whale_events",
        fake_count_events,
    )
    monkeypatch.setattr(
        "app.services.whales_service.list_latest_whale_events",
        fake_list_events,
    )

    page = await get_latest_whale_events_page(
        object(),  # type: ignore[arg-type]
        limit=2,
        offset=10,
    )

    assert page.items == events[:2]
    assert page.limit == 2
    assert page.offset == 10
    assert page.has_more is True
    assert page.total_count == 19
    assert page.total_pages == 10


def test_should_notify_user_about_whale_event_returns_true_for_matching_settings() -> (
    None
):
    """Enabled settings should match events above or equal to the threshold."""
    settings = _build_whale_settings(
        is_enabled=True,
        min_usd_value=Decimal("1000000"),
    )
    event = _build_whale_event(amount_usd=Decimal("1000000"))

    result = should_notify_user_about_whale_event(
        settings=settings,
        event=event,
    )

    assert result is True


def test_should_notify_user_about_whale_event_returns_false_when_disabled() -> None:
    """Disabled settings should never receive whale notifications."""
    settings = _build_whale_settings(
        is_enabled=False,
        min_usd_value=Decimal("1000000"),
    )
    event = _build_whale_event(amount_usd=Decimal("2000000"))

    result = should_notify_user_about_whale_event(
        settings=settings,
        event=event,
    )

    assert result is False


@pytest.mark.asyncio
async def test_create_whale_event_if_new_handles_integrity_error_race(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Concurrent inserts should return the existing event after IntegrityError."""
    existing_event = _build_whale_event(transaction_hash="0xrace")
    create_was_called = False

    async def fake_get_event(
        _session: object,
        *,
        transaction_hash: str,
    ) -> WhaleEvent | None:
        if create_was_called:
            return existing_event
        return None

    async def fake_create_event(
        _session: object,
        **_kwargs: Any,
    ) -> WhaleEvent:
        nonlocal create_was_called
        create_was_called = True
        raise IntegrityError("duplicate", {}, Exception())

    monkeypatch.setattr(
        "app.services.whales_service.get_whale_event_by_transaction_hash",
        fake_get_event,
    )
    monkeypatch.setattr(
        "app.services.whales_service.create_whale_event",
        fake_create_event,
    )

    class FakeSession:
        async def rollback(self) -> None:
            return None

    session = FakeSession()

    result = await create_whale_event_if_new(
        session,  # type: ignore[arg-type]
        data=WhaleEventCreateData(
            coin_id="bitcoin",
            network="btc",
            transaction_hash="0xrace",
            amount=Decimal("15"),
            amount_usd=Decimal("1500000"),
        ),
    )

    assert result.event is existing_event
    assert result.was_created is False


@pytest.mark.asyncio
async def test_create_whale_event_if_new_rejects_unsupported_coin(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Unsupported coin ids should return a readable validation error."""

    async def fake_get_event(
        _session: object,
        *,
        transaction_hash: str,
    ) -> WhaleEvent | None:
        return None

    monkeypatch.setattr(
        "app.services.whales_service.get_whale_event_by_transaction_hash",
        fake_get_event,
    )

    with pytest.raises(ValidationError, match="Unsupported coin id"):
        await create_whale_event_if_new(
            object(),  # type: ignore[arg-type]
            data=WhaleEventCreateData(
                coin_id="dogecoin",
                network="doge",
                transaction_hash="0xnew",
                amount=Decimal("15"),
                amount_usd=Decimal("1500000"),
            ),
        )


def test_should_notify_user_about_whale_event_returns_false_below_threshold() -> None:
    """Events below the user threshold should not trigger notifications."""
    settings = _build_whale_settings(
        is_enabled=True,
        min_usd_value=Decimal("1000000"),
    )
    event = _build_whale_event(amount_usd=Decimal("999999.99"))

    result = should_notify_user_about_whale_event(
        settings=settings,
        event=event,
    )

    assert result is False
