"""Async GoPlus API client."""

from typing import Any

import httpx

from app.core.config import get_settings
from app.core.error_messages import (
    GOPLUS_INVALID_RESPONSE_ERROR,
    GOPLUS_REQUEST_FAILED_ERROR,
)
from app.core.exceptions import SecurityProviderError
from app.integrations.goplus.constants import (
    GOPLUS_CHAIN_IDS_BY_ALIAS,
    GOPLUS_REQUEST_TIMEOUT_SECONDS,
    GOPLUS_TOKEN_SECURITY_PATH_TEMPLATE,
)
from app.integrations.goplus.schemas import parse_token_security_response
from app.utils.validators import normalize_chain, validate_evm_address


class GoPlusClient:
    """Small provider client for token security checks."""

    def __init__(
        self,
        *,
        base_url: str | None = None,
        timeout_seconds: float = GOPLUS_REQUEST_TIMEOUT_SECONDS,
    ) -> None:
        settings = get_settings()

        self._base_url = (base_url or settings.goplus_base_url).rstrip("/")
        self._timeout_seconds = timeout_seconds

    async def get_token_security_data(
        self,
        *,
        chain: str,
        contract_address: str,
    ) -> dict[str, Any]:
        """Return raw token security data for one contract."""
        normalized_chain = normalize_chain(chain)
        normalized_address = validate_evm_address(contract_address)
        chain_id = GOPLUS_CHAIN_IDS_BY_ALIAS[normalized_chain]

        payload = await self._get_token_security_payload(
            chain_id=chain_id,
            contract_address=normalized_address,
        )

        return parse_token_security_response(
            payload,
            contract_address=normalized_address,
        )

    async def _get_token_security_payload(
        self,
        *,
        chain_id: str,
        contract_address: str,
    ) -> dict[str, Any]:
        """Fetch raw token security payload from GoPlus."""
        path = GOPLUS_TOKEN_SECURITY_PATH_TEMPLATE.format(chain_id=chain_id)
        url = f"{self._base_url}{path}"

        params = {
            "contract_addresses": contract_address,
        }

        try:
            async with httpx.AsyncClient(
                timeout=self._timeout_seconds,
            ) as client:
                response = await client.get(url, params=params)
                response.raise_for_status()
        except httpx.HTTPError as exc:
            raise SecurityProviderError(GOPLUS_REQUEST_FAILED_ERROR) from exc

        payload = response.json()

        if not isinstance(payload, dict):
            raise SecurityProviderError(GOPLUS_INVALID_RESPONSE_ERROR)

        return payload
