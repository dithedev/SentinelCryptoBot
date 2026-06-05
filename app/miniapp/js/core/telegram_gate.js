/** Fallback UI for screens that require Telegram authentication. */

import { TEXTS } from "../texts.js";
import { renderEmptyText } from "../ui/common.js";
import { elements } from "./dom.js";

/** Render Telegram-only placeholders across authenticated feature screens. */
export function renderTelegramOnlyScreens() {
    if (elements.alertsList) {
        elements.alertsList.innerHTML = renderEmptyText(TEXTS.telegramOnlyFeature);
    }

    if (elements.riskCheckResult) {
        elements.riskCheckResult.innerHTML = renderEmptyText(TEXTS.telegramOnlyFeature);
    }

    if (elements.whaleEventsList) {
        elements.whaleEventsList.innerHTML = renderEmptyText(TEXTS.telegramOnlyFeature);
    }

    if (elements.whaleSettingsStatus) {
        elements.whaleSettingsStatus.textContent = TEXTS.telegramOnlyFeature;
    }

    setTelegramOnlyFormState(true);
}

/**
 * Disable authenticated-only forms when the Mini App runs outside Telegram.
 * @param {boolean} disabled
 */
export function setTelegramOnlyFormState(disabled) {
    const forms = [
        elements.createAlertForm,
        elements.riskCheckForm,
        elements.whaleSettingsForm,
    ];

    forms.forEach((form) => {
        if (form) {
            form.querySelectorAll("input, button, select, textarea").forEach((control) => {
                control.disabled = disabled;
            });
        }
    });
}
