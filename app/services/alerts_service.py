"""Price alert domain service.

This module owns alert use cases:
- create alert
- list user alerts
- disable or delete alert
- check whether an alert should trigger

No user-facing text should live here.
"""

from dataclasses import dataclass
from decimal import Decimal

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.constants import (
    DEFAULT_ALERT_HISTORY_LIMIT,
    MAX_ALERT_HISTORY_LIMIT,
)
from app.core.exceptions import AlertNotFoundError
from app.database.models.alert import Alert, AlertCondition, AlertStatus
from app.repositories.alerts import (
    count_user_alerts,
    create_alert,
    delete_alert,
    disable_alert,
    get_user_alert_by_id,
    list_active_alerts,
    list_active_alerts_by_coin_ids,
    list_user_alerts,
    mark_alert_triggered,
)
from app.utils.coins import get_coin_symbol
from app.utils.money import validate_alert_price
from app.utils.validators import normalize_coin_id


@dataclass(frozen=True)
class AlertCreateData:
    """Validated data required to create a price alert."""

    user_id: int
    coin_id: str
    target_price: Decimal
    condition: AlertCondition


@dataclass(frozen=True)
class AlertHistoryPage:
    """A single page of user alerts."""

    items: list[Alert]
    limit: int
    offset: int
    has_more: bool
    total_count: int = 0
    total_pages: int = 1


def _normalize_history_limit(limit: int) -> int:
    """Clamp history page size to a safe range."""
    if limit <= 0:
        return DEFAULT_ALERT_HISTORY_LIMIT

    return min(limit, MAX_ALERT_HISTORY_LIMIT)


def _normalize_history_offset(offset: int) -> int:
    """Normalize history offset to a non-negative integer."""
    return max(offset, 0)


def _calculate_total_pages(*, total_count: int, limit: int) -> int:
    """Return total pages for Telegram pagination.

    Empty lists still have one visual page, so the keyboard can show 1/1.
    """
    if total_count <= 0:
        return 1

    return max(1, (total_count + limit - 1) // limit)


def should_trigger_alert(
    *,
    alert: Alert,
    current_price: Decimal,
) -> bool:
    """Return True if the current price satisfies the alert condition."""
    if alert.status != AlertStatus.ACTIVE:
        return False

    if alert.condition == AlertCondition.ABOVE:
        return current_price >= alert.target_price

    if alert.condition == AlertCondition.BELOW:
        return current_price <= alert.target_price

    return False


async def create_price_alert(
    session: AsyncSession,
    *,
    data: AlertCreateData,
) -> Alert:
    """Validate and create a new price alert."""
    coin_id = normalize_coin_id(data.coin_id)
    target_price = validate_alert_price(data.target_price)
    symbol = get_coin_symbol(coin_id)

    return await create_alert(
        session,
        user_id=data.user_id,
        coin_id=coin_id,
        symbol=symbol,
        target_price=target_price,
        condition=data.condition,
    )


async def get_user_alert_or_raise(
    session: AsyncSession,
    *,
    user_id: int,
    alert_id: int,
) -> Alert:
    """Return a user alert or raise a domain error."""
    alert = await get_user_alert_by_id(
        session,
        user_id=user_id,
        alert_id=alert_id,
    )

    if alert is None:
        raise AlertNotFoundError

    return alert


async def get_active_user_alerts(
    session: AsyncSession,
    *,
    user_id: int,
) -> list[Alert]:
    """Return only active alerts for a selected user."""
    return await list_user_alerts(
        session,
        user_id=user_id,
        include_inactive=False,
    )


async def get_user_alert_history(
    session: AsyncSession,
    *,
    user_id: int,
) -> list[Alert]:
    """Return all user alerts including disabled and triggered ones.

    This helper is kept for the public API and tests. Mini App history uses
    get_user_alert_history_page to avoid loading an unlimited list.
    """
    return await list_user_alerts(
        session,
        user_id=user_id,
        include_inactive=True,
    )


async def get_user_alert_history_page(
    session: AsyncSession,
    *,
    user_id: int,
    limit: int = DEFAULT_ALERT_HISTORY_LIMIT,
    offset: int = 0,
) -> AlertHistoryPage:
    """Return one paginated page of user alert history."""
    return await get_user_alerts_page(
        session,
        user_id=user_id,
        status_filter=None,
        limit=limit,
        offset=offset,
    )


async def get_user_alerts_page(
    session: AsyncSession,
    *,
    user_id: int,
    status_filter: AlertStatus | None,
    limit: int = DEFAULT_ALERT_HISTORY_LIMIT,
    offset: int = 0,
) -> AlertHistoryPage:
    """Return one paginated page of user alerts.

    status_filter=None means full history. A concrete status returns only
    alerts with that lifecycle status.
    """
    normalized_limit = _normalize_history_limit(limit)
    normalized_offset = _normalize_history_offset(offset)

    total_count = await count_user_alerts(
        session,
        user_id=user_id,
        include_inactive=True,
        status_filter=status_filter,
    )
    total_pages = _calculate_total_pages(
        total_count=total_count,
        limit=normalized_limit,
    )

    rows = await list_user_alerts(
        session,
        user_id=user_id,
        include_inactive=True,
        status_filter=status_filter,
        limit=normalized_limit + 1,
        offset=normalized_offset,
    )

    has_more = len(rows) > normalized_limit
    items = rows[:normalized_limit]

    return AlertHistoryPage(
        items=items,
        limit=normalized_limit,
        offset=normalized_offset,
        has_more=has_more,
        total_count=total_count,
        total_pages=total_pages,
    )


async def get_all_active_alerts(
    session: AsyncSession,
) -> list[Alert]:
    """Return all active alerts for background workers."""
    return await list_active_alerts(session)


async def get_active_alerts_for_coins(
    session: AsyncSession,
    *,
    coin_ids: set[str],
) -> list[Alert]:
    """Return active alerts for selected coin ids."""
    normalized_coin_ids = {normalize_coin_id(coin_id) for coin_id in coin_ids}

    return await list_active_alerts_by_coin_ids(
        session,
        coin_ids=normalized_coin_ids,
    )


async def disable_user_alert(
    session: AsyncSession,
    *,
    user_id: int,
    alert_id: int,
) -> Alert:
    """Disable a user alert without deleting historical data."""
    alert = await get_user_alert_or_raise(
        session,
        user_id=user_id,
        alert_id=alert_id,
    )

    return await disable_alert(session, alert=alert)


async def delete_user_alert(
    session: AsyncSession,
    *,
    user_id: int,
    alert_id: int,
) -> None:
    """Delete a user alert permanently."""
    alert = await get_user_alert_or_raise(
        session,
        user_id=user_id,
        alert_id=alert_id,
    )

    await delete_alert(session, alert=alert)


async def trigger_alert(
    session: AsyncSession,
    *,
    alert: Alert,
) -> Alert:
    """Mark an active alert as triggered."""
    return await mark_alert_triggered(session, alert=alert)
