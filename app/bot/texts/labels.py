"""Short user-facing labels and emoji markers for messages and buttons."""

from app.database.models.alert import AlertCondition, AlertStatus
from app.database.models.token_check import RiskLevel

ALERT_CONDITION_LABELS: dict[AlertCondition, str] = {
    AlertCondition.ABOVE: "above",
    AlertCondition.BELOW: "below",
}

ALERT_STATUS_LABELS: dict[AlertStatus, str] = {
    AlertStatus.ACTIVE: "Active",
    AlertStatus.TRIGGERED: "Triggered",
    AlertStatus.DISABLED: "Disabled",
}

ALERT_STATUS_ACTIVE_EMOJI = "✅"
ALERT_STATUS_TRIGGERED_EMOJI = "🚨"
ALERT_STATUS_DISABLED_EMOJI = "❌"

ALERT_STATUS_EMOJIS: dict[AlertStatus, str] = {
    AlertStatus.ACTIVE: ALERT_STATUS_ACTIVE_EMOJI,
    AlertStatus.TRIGGERED: ALERT_STATUS_TRIGGERED_EMOJI,
    AlertStatus.DISABLED: ALERT_STATUS_DISABLED_EMOJI,
}

RISK_LEVEL_LABELS: dict[RiskLevel, str] = {
    RiskLevel.LOW: "✅ Low risk",
    RiskLevel.MEDIUM: "⚠️ Medium risk",
    RiskLevel.HIGH: "❌ High risk",
    RiskLevel.UNKNOWN: "❔ Unknown risk",
}
