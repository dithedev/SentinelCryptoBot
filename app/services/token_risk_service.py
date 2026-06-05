"""Token risk check use case service.

This service owns the reusable token risk check flow:
- validate chain and contract address through the provider client
- call the token security provider
- analyze raw provider data
- store the result

Bot handlers and API routes should call this service instead of duplicating
provider, analyzer, and repository logic.
"""

from dataclasses import dataclass
from typing import Any, Protocol

from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models.token_check import TokenCheck
from app.integrations.goplus import GoPlusClient
from app.repositories.token_checks import create_token_check
from app.services.risk_analyzer_service import analyze_token_security_data


class TokenSecurityProvider(Protocol):
    """Protocol for token security providers."""

    async def get_token_security_data(
        self,
        *,
        chain: str,
        contract_address: str,
    ) -> dict[str, Any]:
        """Return raw token security data for one contract."""


@dataclass(frozen=True)
class TokenRiskCheckData:
    """Input data required to check one token contract."""

    user_id: int
    chain: str
    contract_address: str


async def check_token_risk(
    session: AsyncSession,
    *,
    data: TokenRiskCheckData,
    provider: TokenSecurityProvider | None = None,
) -> TokenCheck:
    """Check token risk, store result, and return the saved check."""
    security_provider = provider or GoPlusClient()

    raw_data = await security_provider.get_token_security_data(
        chain=data.chain,
        contract_address=data.contract_address,
    )

    analysis = analyze_token_security_data(
        raw_data,
        chain=data.chain,
        contract_address=data.contract_address,
    )

    return await create_token_check(
        session,
        user_id=data.user_id,
        chain=data.chain.strip().lower(),
        contract_address=data.contract_address.strip(),
        risk_level=analysis.risk_level,
        flags=analysis.flags,
        raw_response=raw_data,
    )
