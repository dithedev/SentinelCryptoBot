"""Load token risk scoring configuration.

The analyzer is code-driven, but the exact scoring weights and trusted token
list live in JSON files. This makes risk tuning easy without changing domain
logic.
"""

import json
from dataclasses import dataclass
from functools import lru_cache
from importlib.resources import files
from typing import Any

CONFIG_PACKAGE = "app.risk.config"
RISK_WEIGHTS_FILE = "risk_weights.json"
TRUSTED_TOKENS_FILE = "trusted_tokens.json"


@dataclass(frozen=True)
class TaxRiskRule:
    """Scoring rule for buy or sell tax fields."""

    medium_threshold: float
    high_threshold: float
    medium_penalty: int
    high_penalty: int


@dataclass(frozen=True)
class RiskScoringConfig:
    """Parsed risk scoring configuration."""

    base_score: int
    low_min_score: int
    medium_min_score: int
    boolean_penalties: dict[str, int]
    tax_rules: dict[str, TaxRiskRule]


@dataclass(frozen=True)
class TrustedToken:
    """One trusted contract from the whitelist."""

    chain: str
    contract_address: str
    symbol: str
    name: str


@dataclass(frozen=True)
class TrustedTokenRegistry:
    """Case-insensitive lookup for trusted token contracts."""

    tokens_by_chain: dict[str, dict[str, TrustedToken]]

    def get_token(
        self,
        *,
        chain: str,
        contract_address: str,
    ) -> TrustedToken | None:
        """Return trusted token metadata or None when token is unknown."""
        normalized_chain = chain.strip().lower()
        normalized_address = contract_address.strip().lower()

        chain_tokens = self.tokens_by_chain.get(normalized_chain)

        if chain_tokens is None:
            return None

        return chain_tokens.get(normalized_address)


@lru_cache
def get_risk_scoring_config() -> RiskScoringConfig:
    """Return cached risk scoring config from bundled JSON."""
    payload = _load_json_file(RISK_WEIGHTS_FILE)

    risk_levels = _read_dict(payload, "risk_levels")
    boolean_penalties = _read_int_map(payload, "boolean_penalties")
    tax_rules = _read_tax_rules(payload)

    return RiskScoringConfig(
        base_score=_read_int(payload, "base_score"),
        low_min_score=_read_int(risk_levels, "low_min_score"),
        medium_min_score=_read_int(risk_levels, "medium_min_score"),
        boolean_penalties=boolean_penalties,
        tax_rules=tax_rules,
    )


@lru_cache
def get_trusted_token_registry() -> TrustedTokenRegistry:
    """Return cached trusted token registry from bundled JSON."""
    payload = _load_json_file(TRUSTED_TOKENS_FILE)
    tokens_by_chain: dict[str, dict[str, TrustedToken]] = {}

    for raw_chain, raw_tokens in payload.items():
        if not isinstance(raw_chain, str) or not isinstance(raw_tokens, dict):
            continue

        chain = raw_chain.strip().lower()
        tokens_by_chain[chain] = {}

        for raw_address, raw_metadata in raw_tokens.items():
            if not isinstance(raw_address, str) or not isinstance(raw_metadata, dict):
                continue

            address = raw_address.strip().lower()
            symbol = _read_optional_str(raw_metadata, "symbol") or "UNKNOWN"
            name = _read_optional_str(raw_metadata, "name") or symbol

            tokens_by_chain[chain][address] = TrustedToken(
                chain=chain,
                contract_address=address,
                symbol=symbol,
                name=name,
            )

    return TrustedTokenRegistry(tokens_by_chain=tokens_by_chain)


def _load_json_file(file_name: str) -> dict[str, Any]:
    """Load one bundled JSON config file."""
    resource = files(CONFIG_PACKAGE).joinpath(file_name)
    payload = json.loads(resource.read_text(encoding="utf-8"))

    if not isinstance(payload, dict):
        return {}

    return payload


def _read_tax_rules(payload: dict[str, Any]) -> dict[str, TaxRiskRule]:
    """Read tax scoring rules from raw config payload."""
    raw_tax_rules = _read_dict(payload, "tax_rules")
    tax_rules: dict[str, TaxRiskRule] = {}

    for field_name, raw_rule in raw_tax_rules.items():
        if not isinstance(field_name, str) or not isinstance(raw_rule, dict):
            continue

        tax_rules[field_name] = TaxRiskRule(
            medium_threshold=_read_float(raw_rule, "medium_threshold"),
            high_threshold=_read_float(raw_rule, "high_threshold"),
            medium_penalty=_read_int(raw_rule, "medium_penalty"),
            high_penalty=_read_int(raw_rule, "high_penalty"),
        )

    return tax_rules


def _read_int_map(payload: dict[str, Any], key: str) -> dict[str, int]:
    """Read a string to int mapping from config payload."""
    raw_mapping = _read_dict(payload, key)
    result: dict[str, int] = {}

    for raw_key, raw_value in raw_mapping.items():
        if not isinstance(raw_key, str):
            continue

        if isinstance(raw_value, bool):
            continue

        if isinstance(raw_value, int):
            result[raw_key] = raw_value

    return result


def _read_dict(payload: dict[str, Any], key: str) -> dict[str, Any]:
    """Read a nested dictionary with a safe empty fallback."""
    value = payload.get(key)

    if isinstance(value, dict):
        return value

    return {}


def _read_int(payload: dict[str, Any], key: str) -> int:
    """Read an integer from config payload."""
    value = payload.get(key)

    if isinstance(value, bool):
        return 0

    if isinstance(value, int):
        return value

    return 0


def _read_float(payload: dict[str, Any], key: str) -> float:
    """Read a float-compatible value from config payload."""
    value = payload.get(key)

    if isinstance(value, bool):
        return 0.0

    if isinstance(value, int | float):
        return float(value)

    return 0.0


def _read_optional_str(payload: dict[str, Any], key: str) -> str | None:
    """Read optional string metadata from config payload."""
    value = payload.get(key)

    if not isinstance(value, str):
        return None

    cleaned_value = value.strip()
    return cleaned_value or None
