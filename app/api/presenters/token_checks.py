"""Token check API presenters."""

from app.api.schemas import TokenRiskCheckResponse
from app.database.models.token_check import TokenCheck


def to_token_risk_check_response(token_check: TokenCheck) -> TokenRiskCheckResponse:
    """Convert a TokenCheck ORM object into an API response schema."""
    return TokenRiskCheckResponse(
        id=token_check.id,
        chain=token_check.chain,
        contract_address=token_check.contract_address,
        risk_level=token_check.risk_level,
        flags=token_check.flags,
        created_at=token_check.created_at,
    )
