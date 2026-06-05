/** Shared presentational helpers for Mini App screens. */

import { TEXTS } from "../texts.js";
import { escapeHtml } from "../core/formatting.js";

/** Render a shared loading card used by async feature sections. */
export function renderLoadingCard() {
    return `
        <article class="data-card">
            <p class="card-meta">${TEXTS.loading}</p>
        </article>
    `;
}

/** Render a shared empty-state message. */
export function renderEmptyText(text) {
    return `<div class="empty-text">${escapeHtml(text)}</div>`;
}
