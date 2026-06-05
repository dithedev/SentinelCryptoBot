"""Real PostgreSQL integration tests for repository contracts."""

from datetime import UTC, datetime
from decimal import Decimal

import pytest
from app.database.models.alert import AlertCondition, AlertStatus
from app.database.models.user import User
from app.database.models.whale import WhaleEventType, WhaleNotificationDeliveryStatus
from app.repositories.alerts import (
    create_alert,
    list_active_alerts,
    try_claim_alert_trigger,
)
from app.repositories.users import create_user
from app.repositories.whale_alert_settings import (
    create_whale_alert_settings,
    get_user_id_and_whale_alert_settings_by_telegram_id,
    list_enabled_whale_alert_settings_for_amount,
)
from app.repositories.whale_events import create_whale_event
from app.repositories.whale_notification_deliveries import (
    get_or_create_whale_notification_delivery,
    mark_whale_notification_delivery_failed,
    mark_whale_notification_delivery_sent,
)
from sqlalchemy.ext.asyncio import AsyncSession

pytestmark = [pytest.mark.db, pytest.mark.asyncio]


async def _create_user(
    session: AsyncSession,
    *,
    telegram_id: int,
    is_active: bool = True,
) -> User:
    """Create one test user."""
    user = await create_user(
        session,
        telegram_id=telegram_id,
        username=f"user_{telegram_id}",
        first_name="Test",
        last_name=None,
    )
    user.is_active = is_active
    await session.flush()
    return user


@pytest.mark.db
async def test_try_claim_alert_trigger_is_atomic(db_session: AsyncSession) -> None:
    """Only the first claim should mark an active alert as triggered."""
    user = await _create_user(db_session, telegram_id=910001)

    alert = await create_alert(
        db_session,
        user_id=user.id,
        coin_id="bitcoin",
        symbol="BTC",
        target_price=Decimal("50000"),
        condition=AlertCondition.ABOVE,
    )

    first_claim = await try_claim_alert_trigger(
        db_session,
        alert_id=alert.id,
    )
    second_claim = await try_claim_alert_trigger(
        db_session,
        alert_id=alert.id,
    )

    assert first_claim is not None
    assert first_claim.status == AlertStatus.TRIGGERED
    assert first_claim.triggered_at is not None
    assert second_claim is None


@pytest.mark.db
async def test_whale_notification_delivery_tracks_status_and_attempts(
    db_session: AsyncSession,
) -> None:
    """Whale delivery rows should move from pending to sent/failed."""
    user = await _create_user(db_session, telegram_id=910002)
    detected_at = datetime(2026, 5, 20, 10, 0, tzinfo=UTC)

    event = await create_whale_event(
        db_session,
        coin_id="bitcoin",
        symbol="BTC",
        network="btc",
        transaction_hash="db-test-whale-tx-1",
        from_address=None,
        to_address=None,
        amount=Decimal("10"),
        amount_usd=Decimal("1500000"),
        event_type=WhaleEventType.TRANSFER,
        detected_at=detected_at,
        raw_payload={"source": "db-test"},
    )

    delivery = await get_or_create_whale_notification_delivery(
        db_session,
        whale_event_id=event.id,
        user_id=user.id,
    )
    same_delivery = await get_or_create_whale_notification_delivery(
        db_session,
        whale_event_id=event.id,
        user_id=user.id,
    )

    assert delivery.id == same_delivery.id
    assert delivery.status == WhaleNotificationDeliveryStatus.PENDING

    sent_delivery = await mark_whale_notification_delivery_sent(
        db_session,
        delivery=delivery,
    )
    assert sent_delivery.status == WhaleNotificationDeliveryStatus.SENT
    assert sent_delivery.attempts == 1

    failed_delivery = await mark_whale_notification_delivery_failed(
        db_session,
        delivery=sent_delivery,
        error_message="temporary failure",
    )
    assert failed_delivery.status == WhaleNotificationDeliveryStatus.FAILED
    assert failed_delivery.attempts == 2
    assert failed_delivery.last_error == "temporary failure"


@pytest.mark.db
async def test_repository_queries_skip_inactive_users(db_session: AsyncSession) -> None:
    """Inactive users should not appear in worker-facing repository queries."""
    active_user = await _create_user(db_session, telegram_id=910003, is_active=True)
    inactive_user = await _create_user(
        db_session,
        telegram_id=910004,
        is_active=False,
    )

    await create_alert(
        db_session,
        user_id=active_user.id,
        coin_id="bitcoin",
        symbol="BTC",
        target_price=Decimal("60000"),
        condition=AlertCondition.ABOVE,
    )
    await create_alert(
        db_session,
        user_id=inactive_user.id,
        coin_id="ethereum",
        symbol="ETH",
        target_price=Decimal("3000"),
        condition=AlertCondition.BELOW,
    )

    await create_whale_alert_settings(
        db_session,
        user_id=active_user.id,
        is_enabled=True,
        min_usd_value=Decimal("1000000"),
    )
    await create_whale_alert_settings(
        db_session,
        user_id=inactive_user.id,
        is_enabled=True,
        min_usd_value=Decimal("1000000"),
    )

    active_alerts = await list_active_alerts(db_session)
    whale_settings = await list_enabled_whale_alert_settings_for_amount(
        db_session,
        amount_usd=Decimal("2000000"),
    )

    assert {alert.user_id for alert in active_alerts} == {active_user.id}
    assert {settings.user_id for settings in whale_settings} == {active_user.id}


@pytest.mark.db
async def test_whale_settings_lookup_by_telegram_id_returns_user_and_settings(
    db_session: AsyncSession,
) -> None:
    """Bot-facing whale settings lookup should join user and settings."""
    user = await _create_user(db_session, telegram_id=910005)
    settings = await create_whale_alert_settings(
        db_session,
        user_id=user.id,
        is_enabled=True,
        min_usd_value=Decimal("2500000"),
    )

    result = await get_user_id_and_whale_alert_settings_by_telegram_id(
        db_session,
        telegram_id=910005,
    )

    assert result is not None
    user_id, loaded_settings = result
    assert user_id == user.id
    assert loaded_settings is not None
    assert loaded_settings.id == settings.id


@pytest.mark.db
async def test_whale_settings_lookup_by_telegram_id_keeps_users_without_settings(
    db_session: AsyncSession,
) -> None:
    """Bot-facing lookup should distinguish missing settings from missing users."""
    user = await _create_user(db_session, telegram_id=910006)

    result = await get_user_id_and_whale_alert_settings_by_telegram_id(
        db_session,
        telegram_id=910006,
    )
    missing_user_result = await get_user_id_and_whale_alert_settings_by_telegram_id(
        db_session,
        telegram_id=999999,
    )

    assert result == (user.id, None)
    assert missing_user_result is None
