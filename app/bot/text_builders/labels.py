"""Helpers for reading user-facing labels."""

from app.bot.texts.labels import (
    ALERT_CONDITION_LABELS,
    ALERT_STATUS_EMOJIS,
    ALERT_STATUS_LABELS,
    RISK_LEVEL_LABELS,
)
from app.database.models.alert import AlertCondition, AlertStatus
from app.database.models.token_check import RiskLevel


def get_alert_condition_label(condition: AlertCondition) -> str:
    """Return a user-facing alert condition label."""
    return ALERT_CONDITION_LABELS[condition]


def get_alert_status_label(status: AlertStatus) -> str:
    """Return a user-facing alert status label."""
    return ALERT_STATUS_LABELS[status]


def get_alert_status_emoji(status: AlertStatus) -> str:
    """Return a compact status emoji for alert buttons."""
    return ALERT_STATUS_EMOJIS[status]


def get_risk_level_label(risk_level: RiskLevel) -> str:
    """Return a user-facing token risk label."""
    return RISK_LEVEL_LABELS[risk_level]
