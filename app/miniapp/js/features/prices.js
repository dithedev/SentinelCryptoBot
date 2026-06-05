/** Prices screen data loading and refresh cooldown behavior. */

import { getPrices } from "../api.js";
import { TEXTS, UI_LIMITS } from "../texts.js";
import { elements } from "../core/dom.js";
import { state } from "../core/state.js";
import {
    escapeHtml,
    formatPrice,
    formatTemplate,
} from "../core/formatting.js";
import { showToast } from "../core/toast.js";
import { renderEmptyText, renderLoadingCard } from "../ui/common.js";

/** Handle manual market price refresh clicks with cooldown feedback. */
export async function handlePricesRefreshClick() {
    const remainingSeconds = getPricesRefreshCooldownRemainingSeconds();

    if (remainingSeconds > 0) {
        showToast(
            formatTemplate(TEXTS.refreshPricesCooldownToastTemplate, {
                seconds: remainingSeconds,
            }),
        );
        return;
    }

    await loadPrices({ applyCooldown: true });
}

/**
 * Load market prices and render the prices list.
 * @param {object} [options]
 * @param {boolean} [options.applyCooldown=false] - Start refresh cooldown after load.
 */
export async function loadPrices({ applyCooldown = false } = {}) {
    if (applyCooldown) {
        startPricesRefreshCooldown();
    }
    elements.pricesList.innerHTML = renderLoadingCard();

    try {
        const prices = await getPrices();
        renderPrices(prices);
    } catch (error) {
        elements.pricesList.innerHTML = renderEmptyText(TEXTS.pricesLoadFailed);
        showToast(error.message || TEXTS.pricesLoadFailed);
    }
}

function startPricesRefreshCooldown() {
    state.pricesRefreshAvailableAt =
        Date.now() + UI_LIMITS.pricesRefreshCooldownSeconds * 1000;

    updatePricesRefreshButton();

    window.clearInterval(state.pricesRefreshCooldownTimerId);
    state.pricesRefreshCooldownTimerId = window.setInterval(() => {
        updatePricesRefreshButton();
    }, 250);
}

function updatePricesRefreshButton() {
    const remainingSeconds = getPricesRefreshCooldownRemainingSeconds();

    if (remainingSeconds <= 0) {
        window.clearInterval(state.pricesRefreshCooldownTimerId);
        state.pricesRefreshCooldownTimerId = null;

        elements.refreshPricesButton.disabled = false;
        elements.refreshPricesButton.textContent = TEXTS.refreshPricesButton;
        return;
    }

    elements.refreshPricesButton.disabled = true;
    elements.refreshPricesButton.textContent = formatTemplate(
        TEXTS.refreshPricesCooldownTemplate,
        {
            seconds: remainingSeconds,
        },
    );
}

function getPricesRefreshCooldownRemainingSeconds() {
    const remainingMilliseconds = state.pricesRefreshAvailableAt - Date.now();

    if (remainingMilliseconds <= 0) {
        return 0;
    }

    return Math.ceil(remainingMilliseconds / 1000);
}

function renderPrices(prices) {
    if (!prices.length) {
        elements.pricesList.innerHTML = renderEmptyText(TEXTS.emptyPrices);
        return;
    }

    elements.pricesList.innerHTML = prices
        .map((price) => {
            return `
                <article class="data-card">
                    <div>
                        <h3 class="card-title">${escapeHtml(price.symbol)}</h3>
                        <p class="card-meta">${escapeHtml(price.name)}</p>
                    </div>
                    <div class="price-value">$${formatPrice(price.price_usd)}</div>
                </article>
            `;
        })
        .join("");
}
