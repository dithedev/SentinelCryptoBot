/** Rendering helpers for the active/history alerts mode switcher. */

import { TEXTS } from "../texts.js";
import { ALERTS_MODE_HISTORY, state } from "./state.js";
import { elements } from "./dom.js";

/** Synchronize alerts headings and segmented controls with current mode. */
export function updateAlertsModeUi() {
    const isHistoryMode = state.alertsMode === ALERTS_MODE_HISTORY;

    elements.alertsTitle.textContent = isHistoryMode
        ? TEXTS.alertHistoryTitle
        : TEXTS.activeAlertsTitle;

    elements.alertsDescription.textContent = isHistoryMode
        ? TEXTS.alertHistoryDescription
        : TEXTS.activeAlertsDescription;

    elements.alertsModeButtons.forEach((button) => {
        button.classList.toggle("active", button.dataset.alertsMode === state.alertsMode);
    });
}
