"""Repository helpers for whale notification delivery tracking."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models.whale import (
    WhaleNotificationDelivery,
    WhaleNotificationDeliveryStatus,
)


async def get_whale_notification_delivery(
    session: AsyncSession,
    *,
    whale_event_id: int,
    user_id: int,
) -> WhaleNotificationDelivery | None:
    """Return delivery row for one event and user."""
    result = await session.execute(
        select(WhaleNotificationDelivery).where(
            WhaleNotificationDelivery.whale_event_id == whale_event_id,
            WhaleNotificationDelivery.user_id == user_id,
        ),
    )
    return result.scalar_one_or_none()


async def get_or_create_whale_notification_delivery(
    session: AsyncSession,
    *,
    whale_event_id: int,
    user_id: int,
) -> WhaleNotificationDelivery:
    """Return an existing delivery row or create a pending one."""
    delivery = await get_whale_notification_delivery(
        session,
        whale_event_id=whale_event_id,
        user_id=user_id,
    )

    if delivery is not None:
        return delivery

    delivery = WhaleNotificationDelivery(
        whale_event_id=whale_event_id,
        user_id=user_id,
        status=WhaleNotificationDeliveryStatus.PENDING,
        attempts=0,
    )
    session.add(delivery)
    await session.flush()
    await session.refresh(delivery)

    return delivery


async def mark_whale_notification_delivery_sent(
    session: AsyncSession,
    *,
    delivery: WhaleNotificationDelivery,
) -> WhaleNotificationDelivery:
    """Mark a whale notification as successfully delivered."""
    delivery.status = WhaleNotificationDeliveryStatus.SENT
    delivery.attempts += 1
    delivery.last_error = None

    await session.flush()
    await session.refresh(delivery)

    return delivery


async def mark_whale_notification_delivery_failed(
    session: AsyncSession,
    *,
    delivery: WhaleNotificationDelivery,
    error_message: str | None = None,
) -> WhaleNotificationDelivery:
    """Mark a failed whale notification attempt."""
    delivery.status = WhaleNotificationDeliveryStatus.FAILED
    delivery.attempts += 1
    delivery.last_error = (error_message or "")[:500] or None

    await session.flush()
    await session.refresh(delivery)

    return delivery
