from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models.token_check import RiskLevel, TokenCheck


async def create_token_check(
    session: AsyncSession,
    *,
    user_id: int,
    chain: str,
    contract_address: str,
    risk_level: RiskLevel,
    flags: dict[str, Any],
    raw_response: dict[str, Any],
) -> TokenCheck:
    """Store token risk check result."""
    token_check = TokenCheck(
        user_id=user_id,
        chain=chain,
        contract_address=contract_address,
        risk_level=risk_level,
        flags=flags,
        raw_response=raw_response,
    )

    session.add(token_check)
    await session.flush()

    return token_check


async def get_token_check_by_id(
    session: AsyncSession,
    *,
    token_check_id: int,
) -> TokenCheck | None:
    """Return stored token check by id."""
    result = await session.execute(
        select(TokenCheck).where(TokenCheck.id == token_check_id),
    )
    return result.scalar_one_or_none()


async def list_user_token_checks(
    session: AsyncSession,
    *,
    user_id: int,
    limit: int = 10,
) -> list[TokenCheck]:
    """Return latest token checks for a user."""
    result = await session.execute(
        select(TokenCheck)
        .where(TokenCheck.user_id == user_id)
        .order_by(TokenCheck.created_at.desc())
        .limit(limit),
    )
    return list(result.scalars().all())


async def get_latest_token_check(
    session: AsyncSession,
    *,
    chain: str,
    contract_address: str,
) -> TokenCheck | None:
    """Return latest check for the same chain and contract.

    This can be used later for lightweight caching if we decide not to call the
    security API on every repeated check.
    """
    result = await session.execute(
        select(TokenCheck)
        .where(
            TokenCheck.chain == chain,
            TokenCheck.contract_address == contract_address,
        )
        .order_by(TokenCheck.created_at.desc())
        .limit(1),
    )
    return result.scalar_one_or_none()
