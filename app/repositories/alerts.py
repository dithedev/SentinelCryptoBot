from datetime import UTC, datetime
from decimal import Decimal

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database.models.alert import Alert, AlertCondition, AlertStatus
from app.database.models.user import User


async def create_alert(
    session: AsyncSession,
    *,
    user_id: int,
    coin_id: str,
    symbol: str,
    target_price: Decimal,
    condition: AlertCondition,
) -> Alert:
    """Create a new active price alert."""
    alert = Alert(
        user_id=user_id,
        coin_id=coin_id,
        symbol=symbol,
        target_price=target_price,
        condition=condition,
        status=AlertStatus.ACTIVE,
    )

    session.add(alert)
    await session.flush()

    return alert


async def get_alert_by_id(
    session: AsyncSession,
    *,
    alert_id: int,
) -> Alert | None:
    """Return alert by id."""
    result = await session.execute(
        select(Alert).where(Alert.id == alert_id),
    )
    return result.scalar_one_or_none()


async def get_user_alert_by_id(
    session: AsyncSession,
    *,
    user_id: int,
    alert_id: int,
) -> Alert | None:
    """Return alert only if it belongs to the selected user."""
    result = await session.execute(
        select(Alert).where(
            Alert.id == alert_id,
            Alert.user_id == user_id,
        ),
    )
    return result.scalar_one_or_none()


async def count_user_alerts(
    session: AsyncSession,
    *,
    user_id: int,
    include_inactive: bool = False,
    status_filter: AlertStatus | None = None,
) -> int:
    """Count user alerts for pagination.

    status_filter takes priority over include_inactive. This mirrors
    list_user_alerts and keeps page counts consistent with loaded rows.
    """
    query = select(func.count(Alert.id)).where(Alert.user_id == user_id)

    if status_filter is not None:
        query = query.where(Alert.status == status_filter)
    elif not include_inactive:
        query = query.where(Alert.status == AlertStatus.ACTIVE)

    result = await session.execute(query)
    return int(result.scalar_one())


async def list_user_alerts(
    session: AsyncSession,
    *,
    user_id: int,
    include_inactive: bool = False,
    status_filter: AlertStatus | None = None,
    limit: int | None = None,
    offset: int = 0,
) -> list[Alert]:
    """Return user alerts ordered from newest to oldest.

    status_filter takes priority over include_inactive. This lets the same
    repository helper support active lists, full history, and filtered history.
    """
    query = select(Alert).where(Alert.user_id == user_id)

    if status_filter is not None:
        query = query.where(Alert.status == status_filter)
    elif not include_inactive:
        query = query.where(Alert.status == AlertStatus.ACTIVE)

    query = query.order_by(Alert.created_at.desc(), Alert.id.desc())

    if offset > 0:
        query = query.offset(offset)

    if limit is not None:
        query = query.limit(limit)

    result = await session.execute(query)
    return list(result.scalars().all())


async def list_active_alerts(
    session: AsyncSession,
) -> list[Alert]:
    """Return all active alerts for the worker."""
    result = await session.execute(
        select(Alert)
        .options(selectinload(Alert.user))
        .join(User, Alert.user_id == User.id)
        .where(
            Alert.status == AlertStatus.ACTIVE,
            User.is_active.is_(True),
        )
        .order_by(Alert.created_at.asc()),
    )
    return list(result.scalars().all())


async def list_active_alerts_by_coin_ids(
    session: AsyncSession,
    *,
    coin_ids: set[str],
) -> list[Alert]:
    """Return active alerts for selected CoinGecko ids."""
    if not coin_ids:
        return []

    result = await session.execute(
        select(Alert)
        .options(selectinload(Alert.user))
        .join(User, Alert.user_id == User.id)
        .where(
            Alert.status == AlertStatus.ACTIVE,
            Alert.coin_id.in_(coin_ids),
            User.is_active.is_(True),
        )
        .order_by(Alert.created_at.asc()),
    )
    return list(result.scalars().all())


async def disable_alert(
    session: AsyncSession,
    *,
    alert: Alert,
) -> Alert:
    """Disable an alert without deleting it."""
    alert.status = AlertStatus.DISABLED
    await session.flush()

    return alert


async def try_claim_alert_trigger(
    session: AsyncSession,
    *,
    alert_id: int,
) -> Alert | None:
    """Atomically mark one active alert as triggered.

    Returns the updated alert when the claim succeeds. Returns None when the
    alert was already triggered or is no longer active.
    """
    result = await session.execute(
        update(Alert)
        .where(
            Alert.id == alert_id,
            Alert.status == AlertStatus.ACTIVE,
        )
        .values(
            status=AlertStatus.TRIGGERED,
            triggered_at=datetime.now(UTC),
        )
        .returning(Alert),
    )
    return result.scalar_one_or_none()


async def mark_alert_triggered(
    session: AsyncSession,
    *,
    alert: Alert,
) -> Alert:
    """Mark an alert as triggered.

    Triggered alerts are kept for history and are not checked again.
    """
    alert.status = AlertStatus.TRIGGERED
    alert.triggered_at = datetime.now(UTC)

    await session.flush()

    return alert


async def delete_alert(
    session: AsyncSession,
    *,
    alert: Alert,
) -> None:
    """Delete an alert permanently.

    For user actions we usually prefer disabling, but permanent deletion is
    useful for Mini App delete buttons and tests.
    """
    await session.delete(alert)
    await session.flush()
