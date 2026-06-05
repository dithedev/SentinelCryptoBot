"""Repository helpers for stored whale events.

Repository functions should not decide whether an event is important or who
should receive notifications. They only read and write whale event rows.
"""

from datetime import datetime
from decimal import Decimal
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models.whale import WhaleEvent, WhaleEventType


async def create_whale_event(
    session: AsyncSession,
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
    """Store a new whale event."""
    whale_event = WhaleEvent(
        coin_id=coin_id,
        symbol=symbol,
        network=network,
        transaction_hash=transaction_hash,
        from_address=from_address,
        to_address=to_address,
        amount=amount,
        amount_usd=amount_usd,
        event_type=event_type,
        detected_at=detected_at,
        raw_payload=raw_payload,
    )

    session.add(whale_event)
    await session.flush()

    return whale_event


async def get_whale_event_by_transaction_hash(
    session: AsyncSession,
    *,
    transaction_hash: str,
) -> WhaleEvent | None:
    """Return an existing whale event by unique transaction hash."""
    result = await session.execute(
        select(WhaleEvent).where(
            WhaleEvent.transaction_hash == transaction_hash,
        ),
    )
    return result.scalar_one_or_none()


async def count_whale_events(session: AsyncSession) -> int:
    """Count stored whale events for pagination."""
    result = await session.execute(select(func.count(WhaleEvent.id)))
    return int(result.scalar_one())


async def list_latest_whale_events(
    session: AsyncSession,
    *,
    limit: int,
    offset: int = 0,
) -> list[WhaleEvent]:
    """Return latest whale events ordered from newest to oldest."""
    query = (
        select(WhaleEvent)
        .order_by(
            WhaleEvent.detected_at.desc(),
            WhaleEvent.id.desc(),
        )
        .offset(offset)
        .limit(limit)
    )

    result = await session.execute(query)
    return list(result.scalars().all())
