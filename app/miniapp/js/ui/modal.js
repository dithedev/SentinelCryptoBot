/** Confirmation modal helpers for disabling active alerts. */

import { TEXTS } from "../texts.js";
import {
    escapeHtml,
    formatPrice,
    formatTemplate,
} from "../core/formatting.js";
import { elements } from "../core/dom.js";
import { state } from "../core/state.js";
import { getCompactConditionLabel } from "../features/alert_labels.js";

/** Open the disable-alert confirmation modal and resolve with the user choice. */
export function confirmAlertDisable(alert, triggerElement) {
    const fallbackAlert = {
        symbol: "Alert",
        condition: "active",
        target_price: "",
    };

    const safeAlert = alert ?? fallbackAlert;
    const description = formatTemplate(TEXTS.disableConfirmDescriptionTemplate, {
        symbol: safeAlert.symbol,
        condition: getCompactConditionLabel(safeAlert.condition),
        price: safeAlert.target_price ? formatPrice(safeAlert.target_price) : "",
    });

    elements.disableConfirmTitle.textContent = TEXTS.disableConfirmTitle;
    elements.disableConfirmDescription.textContent = description;
    elements.cancelDisableAlertButton.textContent = TEXTS.cancelDisableButton;
    elements.confirmDisableAlertButton.textContent = TEXTS.confirmDisableButton;

    state.disableConfirmReturnFocusElement = triggerElement;
    elements.disableConfirmModal.hidden = false;
    elements.confirmDisableAlertButton.focus();

    return new Promise((resolve) => {
        state.disableConfirmResolve = resolve;
    });
}

/** Close the disable-alert modal and restore focus to the triggering button. */
export function closeDisableConfirmModal(confirmed) {
    if (!isDisableConfirmModalOpen()) {
        return;
    }

    elements.disableConfirmModal.hidden = true;

    if (state.disableConfirmResolve) {
        state.disableConfirmResolve(confirmed);
        state.disableConfirmResolve = null;
    }

    if (state.disableConfirmReturnFocusElement) {
        state.disableConfirmReturnFocusElement.focus();
        state.disableConfirmReturnFocusElement = null;
    }
}

/** Return true when the disable-alert modal is visible. */
export function isDisableConfirmModalOpen() {
    return Boolean(elements.disableConfirmModal && !elements.disableConfirmModal.hidden);
}
