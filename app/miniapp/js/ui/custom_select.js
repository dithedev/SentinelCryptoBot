/** Custom select menu behavior shared by form controls. */

import { escapeHtml } from "../core/formatting.js";

/** Toggle a named custom select and close any other open select. */
export function toggleCustomSelect(selectName) {
    const selectElement = document.querySelector(`[data-select="${selectName}"]`);
    const triggerElement = selectElement?.querySelector(".custom-select-trigger");

    if (!selectElement || !triggerElement) {
        return;
    }

    const shouldOpen = !selectElement.classList.contains("open");

    closeAllCustomSelects();

    selectElement.classList.toggle("open", shouldOpen);
    triggerElement.setAttribute("aria-expanded", String(shouldOpen));
}

/** Close every custom select menu on the page. */
export function closeAllCustomSelects() {
    document.querySelectorAll(".custom-select").forEach((selectElement) => {
        selectElement.classList.remove("open");
    });

    document.querySelectorAll(".custom-select-trigger").forEach((triggerElement) => {
        triggerElement.setAttribute("aria-expanded", "false");
    });
}

/** Render an empty custom-select menu state. */
export function renderCustomSelectEmpty(text) {
    return `<div class="custom-select-empty">${escapeHtml(text)}</div>`;
}
