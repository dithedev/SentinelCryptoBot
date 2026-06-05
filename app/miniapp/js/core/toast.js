/** Toast notifications for Mini App actions. */

import { elements } from "./dom.js";

/** Show a short-lived toast message. */
export function showToast(message) {
    elements.toast.textContent = message;
    elements.toast.hidden = false;

    window.clearTimeout(showToast.timeoutId);
    showToast.timeoutId = window.setTimeout(() => {
        elements.toast.hidden = true;
    }, 2800);
}
