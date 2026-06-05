"""Technical constants for the GoPlus integration."""

GOPLUS_TOKEN_SECURITY_PATH_TEMPLATE = "/token_security/{chain_id}"

GOPLUS_REQUEST_TIMEOUT_SECONDS = 10.0

GOPLUS_CHAIN_IDS_BY_ALIAS: dict[str, str] = {
    "eth": "1",
    "bsc": "56",
    "polygon": "137",
    "optimism": "10",
    "arbitrum": "42161",
    "base": "8453",
}
