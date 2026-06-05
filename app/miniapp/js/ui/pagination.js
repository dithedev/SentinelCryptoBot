/** Shared load-more pagination helpers for list screens. */

import { escapeHtml } from "../core/formatting.js";

/**
 * Render a secondary load-more button for paginated lists.
 * @param {object} options
 * @param {string} options.dataAttribute - Data attribute name without brackets.
 * @param {string} options.buttonText - Label when idle.
 * @param {string} options.loadingText - Label while loading.
 * @param {boolean} options.isLoading - Whether another page is loading.
 */
export function renderLoadMoreButton({
    dataAttribute,
    buttonText,
    loadingText,
    isLoading,
}) {
    const label = isLoading ? loadingText : buttonText;

    return `
        <button
            class="secondary-button load-more-button"
            type="button"
            data-${dataAttribute}
            ${isLoading ? "disabled" : ""}
        >
            ${escapeHtml(label)}
        </button>
    `;
}

/**
 * Bind one delegated click handler for load-more buttons inside a list root.
 * @param {HTMLElement|null} listRoot
 * @param {string} dataAttribute - Data attribute name without brackets.
 * @param {() => void | Promise<void>} onLoadMore
 */
export function bindLoadMoreHandler(listRoot, dataAttribute, onLoadMore) {
    if (!listRoot || listRoot.dataset.loadMoreBound === "true") {
        return;
    }

    listRoot.dataset.loadMoreBound = "true";
    listRoot.addEventListener("click", (event) => {
        const button = event.target.closest(`[data-${dataAttribute}]`);

        if (!button || button.disabled || !listRoot.contains(button)) {
            return;
        }

        void onLoadMore();
    });
}
