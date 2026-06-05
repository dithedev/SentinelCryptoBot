"""Token risk analysis service.

The external provider can return many raw fields. This service converts those
raw fields into a stable internal risk level and normalized technical flags.

Risk scoring is configurable:
- trusted contracts are loaded from JSON and bypass penalties
- boolean provider flags subtract points according to risk_weights.json
- tax fields use configurable thresholds and penalties

Only detected signals are returned in flags. Internal score is not shown to the
user and is not stored in the public response.
"""

from dataclasses import dataclass
from typing import Any

from app.database.models.token_check import RiskLevel
from app.risk.config_loader import (
    RiskScoringConfig,
    TrustedToken,
    get_risk_scoring_config,
    get_trusted_token_registry,
)


@dataclass(frozen=True)
class RiskAnalysisResult:
    """Normalized token risk analysis result."""

    risk_level: RiskLevel
    flags: dict[str, Any]
    score: int
    is_trusted: bool
    trusted_token: TrustedToken | None = None


def analyze_token_security_data(
    raw_data: dict[str, Any],
    *,
    chain: str,
    contract_address: str,
    config: RiskScoringConfig | None = None,
) -> RiskAnalysisResult:
    """Analyze provider data and return a normalized risk result.

    Trusted contracts return Low risk with no risk flags. This prevents known
    assets like USDT or USDC from being marked High risk only because their
    contracts include expected admin controls.
    """
    scoring_config = config or get_risk_scoring_config()
    trusted_token = get_trusted_token_registry().get_token(
        chain=chain,
        contract_address=contract_address,
    )

    if trusted_token is not None:
        return RiskAnalysisResult(
            risk_level=RiskLevel.LOW,
            flags={},
            score=scoring_config.base_score,
            is_trusted=True,
            trusted_token=trusted_token,
        )

    score = scoring_config.base_score
    flags: dict[str, Any] = {}

    boolean_flags = _collect_boolean_flags(
        raw_data=raw_data,
        penalties=scoring_config.boolean_penalties,
    )
    tax_flags = _collect_tax_flags(
        raw_data=raw_data,
        config=scoring_config,
    )

    flags.update(boolean_flags.detected_flags)
    flags.update(tax_flags.detected_flags)

    score -= boolean_flags.total_penalty
    score -= tax_flags.total_penalty
    score = _clamp_score(
        score=score,
        max_score=scoring_config.base_score,
    )

    return RiskAnalysisResult(
        risk_level=_resolve_risk_level(
            score=score,
            config=scoring_config,
        ),
        flags=flags,
        score=score,
        is_trusted=False,
    )


@dataclass(frozen=True)
class CollectedRiskFlags:
    """Detected flags plus their internal total penalty."""

    detected_flags: dict[str, Any]
    total_penalty: int


def _collect_boolean_flags(
    *,
    raw_data: dict[str, Any],
    penalties: dict[str, int],
) -> CollectedRiskFlags:
    """Collect enabled boolean provider flags and sum their penalties."""
    detected_flags: dict[str, Any] = {}
    total_penalty = 0

    for field_name, penalty in penalties.items():
        if not _is_truthy_provider_value(raw_data.get(field_name)):
            continue

        detected_flags[field_name] = True
        total_penalty += penalty

    return CollectedRiskFlags(
        detected_flags=detected_flags,
        total_penalty=total_penalty,
    )


def _collect_tax_flags(
    *,
    raw_data: dict[str, Any],
    config: RiskScoringConfig,
) -> CollectedRiskFlags:
    """Collect suspicious tax values and sum their penalties."""
    detected_flags: dict[str, Any] = {}
    total_penalty = 0

    for field_name, rule in config.tax_rules.items():
        tax_percent = _parse_percent(raw_data.get(field_name))

        if tax_percent is None:
            continue

        if tax_percent < rule.medium_threshold:
            continue

        detected_flags[field_name] = tax_percent

        if tax_percent >= rule.high_threshold:
            total_penalty += rule.high_penalty
        else:
            total_penalty += rule.medium_penalty

    return CollectedRiskFlags(
        detected_flags=detected_flags,
        total_penalty=total_penalty,
    )


def _resolve_risk_level(
    *,
    score: int,
    config: RiskScoringConfig,
) -> RiskLevel:
    """Resolve risk level from final internal score."""
    if score >= config.low_min_score:
        return RiskLevel.LOW

    if score >= config.medium_min_score:
        return RiskLevel.MEDIUM

    return RiskLevel.HIGH


def _clamp_score(
    *,
    score: int,
    max_score: int,
) -> int:
    """Keep internal score inside a safe range."""
    return min(max(score, 0), max_score)


def _is_truthy_provider_value(value: Any) -> bool:
    """Normalize boolean-like values returned by security providers."""
    if isinstance(value, bool):
        return value

    if isinstance(value, int):
        return value == 1

    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "yes"}

    return False


def _parse_percent(value: Any) -> float | None:
    """Parse provider tax values into percentages.

    Providers can return strings like 0.15, 15, or empty values. This helper
    keeps parsing defensive so the analyzer does not crash on unexpected data.
    """
    if value is None:
        return None

    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return None

    if parsed < 0:
        return None

    if parsed <= 1:
        return parsed * 100

    return parsed
