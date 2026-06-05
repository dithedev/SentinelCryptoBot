"""Pydantic schemas for Mini App token risk checks."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

from app.database.models.token_check import RiskLevel


class TokenRiskCheckRequest(BaseModel):
    """Payload for checking a token contract from the Mini App."""

    chain: str = Field(..., min_length=1)
    contract_address: str = Field(..., min_length=1)


class TokenRiskCheckResponse(BaseModel):
    """Token risk check response returned to the Mini App."""

    id: int
    chain: str
    contract_address: str
    risk_level: RiskLevel
    flags: dict[str, Any]
    created_at: datetime
