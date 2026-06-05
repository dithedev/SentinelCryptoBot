"""Message builders for token risk check texts."""

from typing import Any

from app.bot.text_builders.labels import get_risk_level_label
from app.bot.texts.risk_check import (
    NO_NORMALIZED_RISK_FLAGS_TEXT,
    TOKEN_CHECK_RESULT_TEMPLATE,
    TOKEN_RISK_BOOLEAN_VALUE_LABEL,
    TOKEN_RISK_PERCENT_VALUE_TEMPLATE,
    TOKEN_RISK_SIGNAL_LABELS,
    TOKEN_RISK_SIGNAL_TEMPLATE,
)
from app.database.models.token_check import TokenCheck

TAX_SIGNAL_NAMES = {"buy_tax", "sell_tax"}


def build_token_check_result_text(token_check: TokenCheck) -> str:
    """Build a readable token risk report."""
    if token_check.flags:
        signals = "\n".join(
            TOKEN_RISK_SIGNAL_TEMPLATE.format(
                name=_get_signal_label(key),
                value=_format_signal_value(
                    name=key,
                    value=value,
                ),
            )
            for key, value in token_check.flags.items()
        )
    else:
        signals = NO_NORMALIZED_RISK_FLAGS_TEXT

    return TOKEN_CHECK_RESULT_TEMPLATE.format(
        chain=token_check.chain.upper(),
        contract_address=token_check.contract_address,
        risk_level=get_risk_level_label(token_check.risk_level),
        signals=signals,
    )


def _get_signal_label(name: str) -> str:
    """Return a user-facing label for a normalized risk signal."""
    return TOKEN_RISK_SIGNAL_LABELS.get(name, name)


def _format_signal_value(
    *,
    name: str,
    value: Any,
) -> str:
    """Format risk signal value without exposing scoring penalties."""
    if isinstance(value, bool):
        return TOKEN_RISK_BOOLEAN_VALUE_LABEL

    if name in TAX_SIGNAL_NAMES and isinstance(value, int | float):
        return TOKEN_RISK_PERCENT_VALUE_TEMPLATE.format(value=f"{value:g}")

    return str(value)
