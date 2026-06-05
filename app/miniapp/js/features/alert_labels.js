/** Label helpers for alert conditions and statuses. */

import { TEXTS } from "../texts.js";

/** Return a user-facing status label for an alert status key. */
export function getAlertStatusLabel(status) {
    return TEXTS.alertStatusLabels?.[status] ?? status;
}

/** Return the CSS class for an alert status badge. */
export function getAlertStatusClass(status) {
    return `status-${String(status).toLowerCase()}`;
}

/** Return the full user-facing label for an alert condition. */
export function getConditionLabel(condition) {
    return TEXTS.conditionLabels?.[condition] ?? condition;
}

/** Return a compact condition label for alert cards and confirmations. */
export function getCompactConditionLabel(condition) {
    return TEXTS.compactConditionLabels?.[condition] ?? condition;
}
