"""Unit tests for token risk scoring.

These tests use an explicit test config instead of the bundled JSON config.
That keeps the analyzer tests deterministic and independent from future tuning
of production risk weights.
"""

from collections.abc import Iterator
from typing import Any

import pytest
from app.database.models.token_check import RiskLevel
from app.risk.config_loader import RiskScoringConfig, TaxRiskRule, TrustedToken
from app.services import risk_analyzer_service as analyzer
from app.services.risk_analyzer_service import RiskAnalysisResult

UNKNOWN_ADDRESS = "0x0000000000000000000000000000000000000000"
TRUSTED_ADDRESS = "0xdAC17F958D2ee523a2206206994597C13D831ec7"


TEST_CONFIG = RiskScoringConfig(
    base_score=100,
    low_min_score=75,
    medium_min_score=40,
    boolean_penalties={
        "is_honeypot": 100,
        "cannot_sell_all": 80,
        "hidden_owner": 50,
        "slippage_modifiable": 35,
        "is_mintable": 20,
        "external_call": 10,
    },
    tax_rules={
        "buy_tax": TaxRiskRule(
            medium_threshold=10.0,
            high_threshold=30.0,
            medium_penalty=35,
            high_penalty=70,
        ),
        "sell_tax": TaxRiskRule(
            medium_threshold=10.0,
            high_threshold=30.0,
            medium_penalty=35,
            high_penalty=70,
        ),
    },
)


class EmptyTrustedTokenRegistry:
    """Trusted token registry that never returns trusted tokens."""

    def get_token(
        self,
        *,
        chain: str,
        contract_address: str,
    ) -> TrustedToken | None:
        """Return no trusted token for deterministic tests."""
        return None


class SingleTrustedTokenRegistry:
    """Trusted token registry with one deterministic trusted contract."""

    def get_token(
        self,
        *,
        chain: str,
        contract_address: str,
    ) -> TrustedToken | None:
        """Return USDT only for the configured ETH contract."""
        if chain.strip().lower() != "eth":
            return None

        if contract_address.strip().lower() != TRUSTED_ADDRESS.lower():
            return None

        return TrustedToken(
            chain="eth",
            contract_address=TRUSTED_ADDRESS.lower(),
            symbol="USDT",
            name="Tether USD",
        )


@pytest.fixture(autouse=True)
def empty_trusted_registry(
    monkeypatch: pytest.MonkeyPatch,
) -> Iterator[None]:
    """Disable bundled trusted tokens by default.

    Individual tests can override this fixture with their own registry.
    """
    monkeypatch.setattr(
        analyzer,
        "get_trusted_token_registry",
        lambda: EmptyTrustedTokenRegistry(),
    )

    yield


def analyze(raw_data: dict[str, Any]) -> RiskAnalysisResult:
    """Analyze raw data with deterministic test config."""
    return analyzer.analyze_token_security_data(
        raw_data,
        chain="eth",
        contract_address=UNKNOWN_ADDRESS,
        config=TEST_CONFIG,
    )


def test_analyze_token_security_data_returns_low_risk_for_empty_data() -> None:
    """Empty provider data should produce a clean Low risk result."""
    result = analyze({})

    assert result.risk_level == RiskLevel.LOW
    assert result.flags == {}
    assert result.score == 100
    assert result.is_trusted is False
    assert result.trusted_token is None


def test_analyze_token_security_data_bypasses_penalties_for_trusted_token(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Trusted contracts should stay Low risk even with provider flags."""
    monkeypatch.setattr(
        analyzer,
        "get_trusted_token_registry",
        lambda: SingleTrustedTokenRegistry(),
    )

    result = analyzer.analyze_token_security_data(
        {
            "is_honeypot": "1",
            "cannot_sell_all": "1",
            "slippage_modifiable": "1",
            "buy_tax": "99",
        },
        chain="ETH",
        contract_address=TRUSTED_ADDRESS,
        config=TEST_CONFIG,
    )

    assert result.risk_level == RiskLevel.LOW
    assert result.flags == {}
    assert result.score == 100
    assert result.is_trusted is True
    assert result.trusted_token is not None
    assert result.trusted_token.symbol == "USDT"


@pytest.mark.parametrize(
    "value",
    [
        True,
        1,
        "1",
        "true",
        "TRUE",
        " yes ",
    ],
)
def test_analyze_token_security_data_detects_truthy_boolean_values(
    value: object,
) -> None:
    """Provider truthy values should be normalized to True."""
    result = analyze({"external_call": value})

    assert result.risk_level == RiskLevel.LOW
    assert result.flags == {"external_call": True}
    assert result.score == 90


@pytest.mark.parametrize(
    "value",
    [
        False,
        0,
        2,
        "0",
        "false",
        "enabled",
        "",
        " ",
        None,
        [],
        {},
    ],
)
def test_analyze_token_security_data_ignores_false_like_boolean_values(
    value: object,
) -> None:
    """Only explicit truthy provider values should create risk flags."""
    result = analyze({"external_call": value})

    assert result.risk_level == RiskLevel.LOW
    assert result.flags == {}
    assert result.score == 100


def test_analyze_token_security_data_returns_medium_for_strong_single_flag() -> None:
    """A strong configurable flag should move score into Medium risk."""
    result = analyze({"slippage_modifiable": "true"})

    assert result.risk_level == RiskLevel.MEDIUM
    assert result.flags == {"slippage_modifiable": True}
    assert result.score == 65


def test_analyze_token_security_data_keeps_low_for_minor_single_flag() -> None:
    """A minor signal can be shown while the final risk remains Low."""
    result = analyze({"external_call": "true"})

    assert result.risk_level == RiskLevel.LOW
    assert result.flags == {"external_call": True}
    assert result.score == 90


def test_analyze_token_security_data_returns_high_for_honeypot() -> None:
    """Honeypot behavior should be enough for High risk."""
    result = analyze({"is_honeypot": "1"})

    assert result.risk_level == RiskLevel.HIGH
    assert result.flags == {"is_honeypot": True}
    assert result.score == 0


def test_analyze_token_security_data_returns_high_for_combined_medium_flags() -> None:
    """Several medium or minor signals can combine into High risk."""
    result = analyze(
        {
            "slippage_modifiable": "1",
            "is_mintable": "1",
            "external_call": "1",
        },
    )

    assert result.risk_level == RiskLevel.HIGH
    assert result.flags == {
        "slippage_modifiable": True,
        "is_mintable": True,
        "external_call": True,
    }
    assert result.score == 35


def test_analyze_token_security_data_ignores_tax_below_medium_threshold() -> None:
    """Tax below the configured threshold should not be shown as a signal."""
    result = analyze(
        {
            "buy_tax": "9.99",
            "sell_tax": "0",
        },
    )

    assert result.risk_level == RiskLevel.LOW
    assert result.flags == {}
    assert result.score == 100


def test_analyze_token_security_data_returns_medium_for_medium_tax() -> None:
    """Tax at or above the medium threshold should be detected."""
    result = analyze({"buy_tax": "15"})

    assert result.risk_level == RiskLevel.MEDIUM
    assert result.flags == {"buy_tax": 15.0}
    assert result.score == 65


def test_analyze_token_security_data_returns_high_for_high_tax() -> None:
    """Tax at or above the high threshold should strongly reduce score."""
    result = analyze({"sell_tax": "30"})

    assert result.risk_level == RiskLevel.HIGH
    assert result.flags == {"sell_tax": 30.0}
    assert result.score == 30


def test_analyze_token_security_data_converts_fraction_tax_to_percent() -> None:
    """Provider tax fractions should be converted to percentages."""
    result = analyze({"sell_tax": "0.15"})

    assert result.risk_level == RiskLevel.MEDIUM
    assert result.flags == {"sell_tax": 15.0}
    assert result.score == 65


@pytest.mark.parametrize(
    "value",
    [
        "-1",
        "",
        "not-a-number",
        None,
        [],
        {},
    ],
)
def test_analyze_token_security_data_ignores_invalid_tax_values(
    value: object,
) -> None:
    """Invalid tax values should not crash scoring or create signals."""
    result = analyze({"buy_tax": value})

    assert result.risk_level == RiskLevel.LOW
    assert result.flags == {}
    assert result.score == 100


def test_analyze_token_security_data_combines_boolean_and_tax_penalties() -> None:
    """Boolean and tax penalties should be added together."""
    result = analyze(
        {
            "slippage_modifiable": "1",
            "buy_tax": "15",
        },
    )

    assert result.risk_level == RiskLevel.HIGH
    assert result.flags == {
        "slippage_modifiable": True,
        "buy_tax": 15.0,
    }
    assert result.score == 30


@pytest.mark.parametrize(
    ("penalty", "expected_level", "expected_score"),
    [
        (25, RiskLevel.LOW, 75),
        (60, RiskLevel.MEDIUM, 40),
        (61, RiskLevel.HIGH, 39),
    ],
)
def test_analyze_token_security_data_respects_risk_level_boundaries(
    penalty: int,
    expected_level: RiskLevel,
    expected_score: int,
) -> None:
    """Boundary scores should map to the expected risk level."""
    config = RiskScoringConfig(
        base_score=100,
        low_min_score=75,
        medium_min_score=40,
        boolean_penalties={"external_call": penalty},
        tax_rules={},
    )

    result = analyzer.analyze_token_security_data(
        {"external_call": "1"},
        chain="eth",
        contract_address=UNKNOWN_ADDRESS,
        config=config,
    )

    assert result.risk_level == expected_level
    assert result.score == expected_score


def test_analyze_token_security_data_clamps_score_to_zero() -> None:
    """Very large penalties should not produce negative scores."""
    result = analyze(
        {
            "is_honeypot": "1",
            "cannot_sell_all": "1",
            "hidden_owner": "1",
            "sell_tax": "99",
        },
    )

    assert result.risk_level == RiskLevel.HIGH
    assert result.score == 0


def test_analyze_token_security_data_clamps_score_to_base_score() -> None:
    """Negative penalties from a bad config should not exceed base score."""
    config = RiskScoringConfig(
        base_score=100,
        low_min_score=75,
        medium_min_score=40,
        boolean_penalties={"external_call": -50},
        tax_rules={},
    )

    result = analyzer.analyze_token_security_data(
        {"external_call": "1"},
        chain="eth",
        contract_address=UNKNOWN_ADDRESS,
        config=config,
    )

    assert result.risk_level == RiskLevel.LOW
    assert result.flags == {"external_call": True}
    assert result.score == 100
