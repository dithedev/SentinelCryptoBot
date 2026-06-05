"""Unit tests for token risk check message rendering."""

from datetime import UTC, datetime

from app.bot.text_builders.risk_check import build_token_check_result_text
from app.bot.texts import NO_NORMALIZED_RISK_FLAGS_TEXT
from app.database.models.token_check import RiskLevel, TokenCheck

UNKNOWN_ADDRESS = "0x0000000000000000000000000000000000000000"


def build_token_check(
    *,
    risk_level: RiskLevel = RiskLevel.MEDIUM,
    flags: dict[str, object] | None = None,
) -> TokenCheck:
    """Build a deterministic TokenCheck object for text tests."""
    return TokenCheck(
        id=1,
        user_id=1,
        chain="eth",
        contract_address=UNKNOWN_ADDRESS,
        risk_level=risk_level,
        flags=flags or {},
        raw_response={},
        created_at=datetime(2026, 5, 18, 10, 0, tzinfo=UTC),
    )


def test_build_token_check_result_text_formats_detected_signals() -> None:
    """Text should show readable signals without exposing scoring internals."""
    token_check = build_token_check(
        flags={
            "slippage_modifiable": True,
            "buy_tax": 15.0,
        },
    )

    text = build_token_check_result_text(token_check)

    assert "Risk level: <b>⚠️ Medium risk</b>" in text
    assert "Sell tax can be changed: detected" in text
    assert "Buy tax: 15%" in text

    assert "score" not in text.lower()
    assert "penalty" not in text.lower()
    assert "points" not in text.lower()


def test_build_token_check_result_text_handles_empty_flags() -> None:
    """Text should show a friendly empty state when no signals were detected."""
    token_check = build_token_check(
        risk_level=RiskLevel.LOW,
        flags={},
    )

    text = build_token_check_result_text(token_check)

    assert "Risk level: <b>✅ Low risk</b>" in text
    assert NO_NORMALIZED_RISK_FLAGS_TEXT in text
