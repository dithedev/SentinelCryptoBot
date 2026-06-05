"""Whale alerts domain service.

This module owns whale alert use cases and keeps business logic outside API
routes, bot routers, worker entrypoints, and UI code.
"""

from dataclasses import dataclass, field
from datetime import UTC, datetime
from decimal import Decimal
from typing import Any

from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.constants import (
    DEFAULT_WHALE_EVENTS_LIMIT,
    DEFAULT_WHALE_MIN_USD_VALUE,
    MAX_WHALE_EVENTS_LIMIT,
    MAX_WHALE_MIN_USD_VALUE,
    MIN_WHALE_MIN_USD_VALUE,
)
from app.core.error_messages import (
    WHALE_AMOUNT_TOO_LOW_ERROR,
    WHALE_AMOUNT_USD_TOO_LOW_ERROR,
    WHALE_MIN_USD_VALUE_TOO_HIGH_ERROR_TEMPLATE,
    WHALE_MIN_USD_VALUE_TOO_LOW_ERROR_TEMPLATE,
    WHALE_NETWORK_EMPTY_ERROR,
    WHALE_TRANSACTION_HASH_EMPTY_ERROR,
)
from app.core.exceptions import UserNotFoundError, ValidationError
from app.database.models.whale import WhaleAlertSettings, WhaleEvent, WhaleEventType
from app.repositories.whale_alert_settings import (
    create_whale_alert_settings,
    get_user_id_and_whale_alert_settings_by_telegram_id,
    get_whale_alert_settings_by_user_id,
    list_enabled_whale_alert_settings_for_amount,
    update_whale_alert_settings,
)
from app.repositories.whale_events import (
    count_whale_events,
    create_whale_event,
    get_whale_event_by_transaction_hash,
    list_latest_whale_events,
)
from app.utils.coins import get_coin_symbol
from app.utils.validators import normalize_coin_id

USD_QUANT = Decimal("0.01")
TOKEN_AMOUNT_QUANT = Decimal("0.000000000000000001")


@dataclass(frozen=True)
class WhaleSettingsUpdateData:
    """Input data for updating user whale alert settings."""

    user_id: int
    is_enabled: bool | None = None
    min_usd_value: Decimal | None = None


@dataclass(frozen=True)
class UserWhaleSettings:
    """Whale settings together with the owning internal user id."""

    user_id: int
    settings: WhaleAlertSettings


@dataclass(frozen=True)
class WhaleEventCreateData:
    """Input data required to create a whale movement event."""

    coin_id: str
    network: str
    transaction_hash: str
    amount: Decimal
    amount_usd: Decimal
    event_type: WhaleEventType = WhaleEventType.UNKNOWN
    from_address: str | None = None
    to_address: str | None = None
    detected_at: datetime | None = None
    raw_payload: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class WhaleEventsPage:
    """A single paginated page of whale events."""

    items: list[WhaleEvent]
    limit: int
    offset: int
    has_more: bool
    total_count: int = 0
    total_pages: int = 1


@dataclass(frozen=True)
class WhaleEventCreateResult:
    """Result of idempotent whale event creation."""

    event: WhaleEvent
    was_created: bool


def _normalize_events_limit(limit: int) -> int:
    """Clamp whale event page size to a safe range."""
    if limit <= 0:
        return DEFAULT_WHALE_EVENTS_LIMIT

    return min(limit, MAX_WHALE_EVENTS_LIMIT)


def _normalize_events_offset(offset: int) -> int:
    """Normalize whale event offset to a non-negative integer."""
    return max(offset, 0)


def _calculate_total_pages(*, total_count: int, limit: int) -> int:
    """Return total pages for whale event pagination."""
    if total_count <= 0:
        return 1

    return max(1, (total_count + limit - 1) // limit)


def _validate_min_usd_value(value: Decimal) -> Decimal:
    """Validate and normalize a user whale alert threshold."""
    if value < MIN_WHALE_MIN_USD_VALUE:
        message = WHALE_MIN_USD_VALUE_TOO_LOW_ERROR_TEMPLATE.format(
            min_value=MIN_WHALE_MIN_USD_VALUE,
        )
        raise ValidationError(message)

    if value > MAX_WHALE_MIN_USD_VALUE:
        message = WHALE_MIN_USD_VALUE_TOO_HIGH_ERROR_TEMPLATE.format(
            max_value=MAX_WHALE_MIN_USD_VALUE,
        )
        raise ValidationError(message)

    return value.quantize(USD_QUANT)


def _validate_amount(value: Decimal) -> Decimal:
    """Validate and normalize whale token amount."""
    if value <= 0:
        raise ValidationError(WHALE_AMOUNT_TOO_LOW_ERROR)

    return value.quantize(TOKEN_AMOUNT_QUANT)


def _validate_amount_usd(value: Decimal) -> Decimal:
    """Validate and normalize whale event USD value."""
    if value <= 0:
        raise ValidationError(WHALE_AMOUNT_USD_TOO_LOW_ERROR)

    return value.quantize(USD_QUANT)


def _normalize_network(network: str) -> str:
    """Normalize a whale event network label."""
    normalized_network = network.strip().lower()

    if not normalized_network:
        raise ValidationError(WHALE_NETWORK_EMPTY_ERROR)

    return normalized_network


def _normalize_transaction_hash(transaction_hash: str) -> str:
    """Normalize and validate a unique whale event transaction id."""
    normalized_hash = transaction_hash.strip()

    if not normalized_hash:
        raise ValidationError(WHALE_TRANSACTION_HASH_EMPTY_ERROR)

    return normalized_hash


def _normalize_optional_address(address: str | None) -> str | None:
    """Normalize optional blockchain address fields."""
    if address is None:
        return None

    normalized_address = address.strip()
    return normalized_address or None


async def get_or_create_user_whale_settings(
    session: AsyncSession,
    *,
    user_id: int,
) -> WhaleAlertSettings:
    """Return user whale settings or create defaults.

    New users start with whale alerts disabled. This avoids surprise
    notifications until the user explicitly enables them.
    """
    settings = await get_whale_alert_settings_by_user_id(
        session,
        user_id=user_id,
    )

    if settings is not None:
        return settings

    return await create_whale_alert_settings(
        session,
        user_id=user_id,
        is_enabled=False,
        min_usd_value=DEFAULT_WHALE_MIN_USD_VALUE,
    )


async def get_or_create_user_whale_settings_by_telegram_id(
    session: AsyncSession,
    *,
    telegram_id: int,
) -> UserWhaleSettings:
    """Return a Telegram user's whale settings with one read query.

    Bot flows know the Telegram id first, so this avoids loading the User row
    and the settings row separately on every callback.
    """
    user_settings = await get_user_id_and_whale_alert_settings_by_telegram_id(
        session,
        telegram_id=telegram_id,
    )

    if user_settings is None:
        raise UserNotFoundError

    user_id, settings = user_settings

    if settings is None:
        settings = await create_whale_alert_settings(
            session,
            user_id=user_id,
            is_enabled=False,
            min_usd_value=DEFAULT_WHALE_MIN_USD_VALUE,
        )

    return UserWhaleSettings(
        user_id=user_id,
        settings=settings,
    )


async def update_user_whale_settings(
    session: AsyncSession,
    *,
    data: WhaleSettingsUpdateData,
) -> WhaleAlertSettings:
    """Update whale alert settings for one user."""
    settings = await get_or_create_user_whale_settings(
        session,
        user_id=data.user_id,
    )

    return await update_loaded_user_whale_settings(
        session,
        settings=settings,
        is_enabled=data.is_enabled,
        min_usd_value=data.min_usd_value,
    )


async def update_loaded_user_whale_settings(
    session: AsyncSession,
    *,
    settings: WhaleAlertSettings,
    is_enabled: bool | None = None,
    min_usd_value: Decimal | None = None,
) -> WhaleAlertSettings:
    """Update already-loaded whale settings without re-reading them."""
    normalized_min_usd_value = None

    if min_usd_value is not None:
        normalized_min_usd_value = _validate_min_usd_value(min_usd_value)

    return await update_whale_alert_settings(
        session,
        settings=settings,
        is_enabled=is_enabled,
        min_usd_value=normalized_min_usd_value,
    )


async def get_latest_whale_events_page(
    session: AsyncSession,
    *,
    limit: int = DEFAULT_WHALE_EVENTS_LIMIT,
    offset: int = 0,
) -> WhaleEventsPage:
    """Return a paginated list of latest whale events."""
    normalized_limit = _normalize_events_limit(limit)
    normalized_offset = _normalize_events_offset(offset)

    total_count = await count_whale_events(session)
    total_pages = _calculate_total_pages(
        total_count=total_count,
        limit=normalized_limit,
    )

    rows = await list_latest_whale_events(
        session,
        limit=normalized_limit + 1,
        offset=normalized_offset,
    )

    has_more = len(rows) > normalized_limit
    items = rows[:normalized_limit]

    return WhaleEventsPage(
        items=items,
        limit=normalized_limit,
        offset=normalized_offset,
        has_more=has_more,
        total_count=total_count,
        total_pages=total_pages,
    )


async def create_whale_event_if_new(
    session: AsyncSession,
    *,
    data: WhaleEventCreateData,
) -> WhaleEventCreateResult:
    """Create a whale event only if its transaction hash is new.

    This idempotent helper prevents the worker from saving and notifying about
    the same provider event multiple times.
    """
    transaction_hash = _normalize_transaction_hash(data.transaction_hash)

    existing_event = await get_whale_event_by_transaction_hash(
        session,
        transaction_hash=transaction_hash,
    )

    if existing_event is not None:
        return WhaleEventCreateResult(
            event=existing_event,
            was_created=False,
        )

    coin_id = normalize_coin_id(data.coin_id)
    symbol = get_coin_symbol(coin_id)
    network = _normalize_network(data.network)
    amount = _validate_amount(data.amount)
    amount_usd = _validate_amount_usd(data.amount_usd)
    detected_at = data.detected_at or datetime.now(UTC)

    try:
        event = await create_whale_event(
            session,
            coin_id=coin_id,
            symbol=symbol,
            network=network,
            transaction_hash=transaction_hash,
            from_address=_normalize_optional_address(data.from_address),
            to_address=_normalize_optional_address(data.to_address),
            amount=amount,
            amount_usd=amount_usd,
            event_type=data.event_type,
            detected_at=detected_at,
            raw_payload=data.raw_payload,
        )
    except IntegrityError:
        await session.rollback()

        raced_event = await get_whale_event_by_transaction_hash(
            session,
            transaction_hash=transaction_hash,
        )

        if raced_event is None:
            raise

        return WhaleEventCreateResult(
            event=raced_event,
            was_created=False,
        )

    return WhaleEventCreateResult(
        event=event,
        was_created=True,
    )


def should_notify_user_about_whale_event(
    *,
    settings: WhaleAlertSettings,
    event: WhaleEvent,
) -> bool:
    """Return True when a whale event matches user settings."""
    if not settings.is_enabled:
        return False

    return event.amount_usd >= settings.min_usd_value


async def get_matching_whale_settings(
    session: AsyncSession,
    *,
    event: WhaleEvent,
) -> list[WhaleAlertSettings]:
    """Return enabled user settings that match one whale event."""
    return await list_enabled_whale_alert_settings_for_amount(
        session,
        amount_usd=event.amount_usd,
    )
