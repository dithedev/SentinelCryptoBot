"""Schemas and parsing helpers for GoPlus responses."""

from typing import Any

from app.core.error_messages import (
    GOPLUS_INVALID_RESPONSE_ERROR,
    GOPLUS_TOKEN_DATA_NOT_FOUND_ERROR,
)
from app.core.exceptions import SecurityProviderError


def parse_token_security_response(
    payload: dict[str, Any],
    *,
    contract_address: str,
) -> dict[str, Any]:
    """Extract one token security result from a GoPlus response.

    Expected provider shape:

    {
        "code": 1,
        "message": "OK",
        "result": {
            "0x...": {...token security data...}
        }
    }
    """
    result = payload.get("result")

    if not isinstance(result, dict):
        raise SecurityProviderError(GOPLUS_INVALID_RESPONSE_ERROR)

    token_data = result.get(contract_address)

    if token_data is None:
        token_data = result.get(contract_address.lower())

    if token_data is None:
        raise SecurityProviderError(GOPLUS_TOKEN_DATA_NOT_FOUND_ERROR)

    if not isinstance(token_data, dict):
        raise SecurityProviderError(GOPLUS_INVALID_RESPONSE_ERROR)

    return token_data
