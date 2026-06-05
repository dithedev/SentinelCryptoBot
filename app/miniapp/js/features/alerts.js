/** Alerts screen creation form, active list, and history pagination. */

import {
    createAlert,
    disableAlert,
    getAlertHistory,
    getAlerts,
} from "../api.js";
import { TEXTS, UI_LIMITS } from "../texts.js";
import { elements } from "../core/dom.js";
import {
    ALERTS_MODE_ACTIVE,
    ALERTS_MODE_HISTORY,
    TARGET_PRICE_DECIMALS,
    TARGET_PRICE_SCALE,
    state,
} from "../core/state.js";
import {
    escapeHtml,
    formatDateTime,
    formatPrice,
    formatTemplate,
} from "../core/formatting.js";
import { showToast } from "../core/toast.js";
import { setActiveViewDom } from "../core/views.js";
import { updateAlertsModeUi } from "../core/alerts_mode.js";
import { renderEmptyText, renderLoadingCard } from "../ui/common.js";
import { bindLoadMoreHandler, renderLoadMoreButton } from "../ui/pagination.js";
import {
    closeAllCustomSelects,
    renderCustomSelectEmpty,
} from "../ui/custom_select.js";
import { confirmAlertDisable } from "../ui/modal.js";
import {
    getAlertStatusClass,
    getAlertStatusLabel,
    getCompactConditionLabel,
    getConditionLabel,
} from "./alert_labels.js";

const MAX_TARGET_PRICE_UNITS =
    BigInt(UI_LIMITS.maxTargetPriceUsd) * TARGET_PRICE_SCALE;

/** Load alerts for the current active/history mode. */
export async function loadAlerts() {
    if (!state.isTelegramAuthenticated) {
        elements.alertsList.innerHTML = renderEmptyText(TEXTS.telegramOnlyFeature);
        return;
    }

    if (state.alertsMode === ALERTS_MODE_HISTORY) {
        await loadAlertHistoryFirstPage();
        return;
    }

    await loadActiveAlerts();
}

async function loadActiveAlerts() {
    elements.alertsList.innerHTML = renderLoadingCard();

    try {
        state.activeAlerts = await getAlerts();
        renderAlerts(state.activeAlerts);
    } catch (error) {
        elements.alertsList.innerHTML = renderEmptyText(TEXTS.alertsLoadFailed);
        showToast(error.message || TEXTS.alertsLoadFailed);
    }
}

async function loadAlertHistoryFirstPage() {
    elements.alertsList.innerHTML = renderLoadingCard();
    state.alertHistoryItems = [];
    state.alertHistoryOffset = 0;
    state.alertHistoryHasMore = false;

    try {
        const page = await getAlertHistory({
            limit: UI_LIMITS.alertHistoryPageSize,
            offset: 0,
        });

        state.alertHistoryItems = page.items;
        state.alertHistoryOffset = page.offset + page.items.length;
        state.alertHistoryHasMore = page.has_more;

        renderAlertHistory();
    } catch (error) {
        elements.alertsList.innerHTML = renderEmptyText(TEXTS.alertHistoryLoadFailed);
        showToast(error.message || TEXTS.alertHistoryLoadFailed);
    }
}

async function loadMoreAlertHistory() {
    if (state.isAlertHistoryLoadingMore || !state.alertHistoryHasMore) {
        return;
    }

    state.isAlertHistoryLoadingMore = true;
    renderAlertHistory();

    try {
        const page = await getAlertHistory({
            limit: UI_LIMITS.alertHistoryPageSize,
            offset: state.alertHistoryOffset,
        });

        state.alertHistoryItems = [...state.alertHistoryItems, ...page.items];
        state.alertHistoryOffset = page.offset + page.items.length;
        state.alertHistoryHasMore = page.has_more;
    } catch (error) {
        showToast(error.message || TEXTS.alertHistoryLoadFailed);
    } finally {
        state.isAlertHistoryLoadingMore = false;
        renderAlertHistory();
    }
}

function renderAlerts(alerts) {
    if (!alerts.length) {
        elements.alertsList.innerHTML = renderEmptyText(TEXTS.emptyActiveAlerts);
        return;
    }

    elements.alertsList.innerHTML = alerts.map(renderAlertCard).join("");
    bindAlertListButtons();
}

function renderAlertHistory() {
    if (!state.alertHistoryItems.length) {
        elements.alertsList.innerHTML = renderEmptyText(TEXTS.emptyAlertHistory);
        return;
    }

    const cardsHtml = state.alertHistoryItems.map(renderAlertCard).join("");
    const loadMoreHtml = state.alertHistoryHasMore
        ? renderLoadMoreButton({
              dataAttribute: "load-more-history",
              buttonText: TEXTS.loadMoreHistoryButton,
              loadingText: TEXTS.loadingMoreHistoryButton,
              isLoading: state.isAlertHistoryLoadingMore,
          })
        : "";

    elements.alertsList.innerHTML = `${cardsHtml}${loadMoreHtml}`;
    bindAlertListButtons();
    bindLoadMoreHandler(
        elements.alertsList,
        "load-more-history",
        loadMoreAlertHistory,
    );
}

function bindAlertListButtons() {
    elements.alertsList.querySelectorAll("[data-disable-alert-id]").forEach((button) => {
        button.addEventListener("click", async () => {
            const alertId = Number(button.dataset.disableAlertId);
            await handleDisableAlert(alertId, button);
        });
    });

}

function renderAlertCard(alert) {
    const statusLabel = getAlertStatusLabel(alert.status);
    const statusClass = getAlertStatusClass(alert.status);
    const conditionLabel = getCompactConditionLabel(alert.condition);
    const canDisable = alert.status === "active";

    return `
        <article class="data-card alert-card">
            <div class="alert-card-body">
                <div class="alert-card-heading">
                    <h3 class="card-title">
                        ${escapeHtml(alert.symbol)} ${escapeHtml(conditionLabel)}
                        $${formatPrice(alert.target_price)}
                    </h3>
                    <span class="status-badge ${statusClass}">
                        ${escapeHtml(statusLabel)}
                    </span>
                </div>

                ${renderAlertTimestamps(alert)}
            </div>

            ${canDisable ? renderDisableButton(alert.id) : ""}
        </article>
    `;
}

function renderAlertTimestamps(alert) {
    const timestampRows = [
        `
            <span>
                ${escapeHtml(TEXTS.createdAtLabel)}:
                ${escapeHtml(formatDateTime(alert.created_at))}
            </span>
        `,
    ];

    if (alert.triggered_at) {
        timestampRows.push(`
            <span>
                ${escapeHtml(TEXTS.triggeredAtLabel)}:
                ${escapeHtml(formatDateTime(alert.triggered_at))}
            </span>
        `);
    }

    return `
        <div class="timestamp-list">
            ${timestampRows.join("")}
        </div>
    `;
}

function renderDisableButton(alertId) {
    return `
        <button
            class="danger-button"
            type="button"
            data-disable-alert-id="${alertId}"
        >
            ${escapeHtml(TEXTS.disableButton)}
        </button>
    `;
}

/** Render coin options for the create-alert custom select. */
export function renderCoinOptions(coins) {
    state.selectedCoin = null;
    elements.coinSelect.value = "";
    elements.coinSelectButtonText.textContent = TEXTS.chooseCoinPlaceholder;

    if (!coins.length) {
        elements.coinSelectList.innerHTML = renderCustomSelectEmpty(
            TEXTS.noCoinsAvailable,
        );
        return;
    }

    elements.coinSelectList.innerHTML = coins
        .map((coin) => {
            return `
                <button
                    class="custom-select-option"
                    type="button"
                    role="option"
                    aria-selected="false"
                    data-coin-id="${escapeHtml(coin.coin_id)}"
                >
                    <span>
                        <span class="custom-select-option-main">
                            ${escapeHtml(coin.symbol)}
                        </span>
                        <span class="custom-select-option-meta">
                            ${escapeHtml(coin.name)}
                        </span>
                    </span>
                </button>
            `;
        })
        .join("");

    elements.coinSelectList.querySelectorAll("[data-coin-id]").forEach((button) => {
        button.addEventListener("click", () => {
            const coin = coins.find((item) => item.coin_id === button.dataset.coinId);

            if (coin) {
                selectCoin(coin);
            }
        });
    });

    selectCoin(coins[0]);
}

/** Render condition options for the create-alert custom select. */
export function renderConditionOptions(conditions) {
    const safeConditions = conditions.length ? conditions : ["above", "below"];

    state.selectedCondition = null;
    elements.conditionSelect.value = "";
    elements.conditionSelectButtonText.textContent = TEXTS.chooseConditionPlaceholder;

    elements.conditionSelectList.innerHTML = safeConditions
        .map((condition) => {
            const label = getConditionLabel(condition);

            return `
                <button
                    class="custom-select-option"
                    type="button"
                    role="option"
                    aria-selected="false"
                    data-condition="${escapeHtml(condition)}"
                >
                    <span>
                        <span class="custom-select-option-main">
                            ${escapeHtml(label)}
                        </span>
                    </span>
                </button>
            `;
        })
        .join("");

    elements.conditionSelectList
        .querySelectorAll("[data-condition]")
        .forEach((button) => {
            button.addEventListener("click", () => {
                const condition = button.dataset.condition;

                if (condition) {
                    selectCondition(condition);
                }
            });
        });

    selectCondition(safeConditions[0]);
}

function selectCoin(coin) {
    state.selectedCoin = coin;
    elements.coinSelect.value = coin.coin_id;
    elements.coinSelectButtonText.textContent = `${coin.symbol} - ${coin.name}`;

    elements.coinSelectList.querySelectorAll("[data-coin-id]").forEach((button) => {
        const isSelected = button.dataset.coinId === coin.coin_id;

        button.classList.toggle("selected", isSelected);
        button.setAttribute("aria-selected", String(isSelected));
    });

    closeAllCustomSelects();
}

function selectCondition(condition) {
    state.selectedCondition = condition;
    elements.conditionSelect.value = condition;
    elements.conditionSelectButtonText.textContent = getConditionLabel(condition);

    elements.conditionSelectList
        .querySelectorAll("[data-condition]")
        .forEach((button) => {
            const isSelected = button.dataset.condition === condition;

            button.classList.toggle("selected", isSelected);
            button.setAttribute("aria-selected", String(isSelected));
        });

    closeAllCustomSelects();
}

/** Move target price input by a context-sensitive step. */
export function changeTargetPriceStep(direction) {
    const currentUnits = parseTargetPriceToUnits(elements.targetPriceInput.value) ?? 0n;
    const stepUnits = getTargetPriceStepUnits(currentUnits);
    const directionMultiplier = BigInt(direction);

    const nextUnits = clampTargetPriceUnits(
        currentUnits + stepUnits * directionMultiplier,
    );

    elements.targetPriceInput.value = formatTargetPriceUnits(nextUnits);
    elements.targetPriceInput.focus();
}

function parseTargetPriceToUnits(value) {
    const normalizedValue = String(value).trim().replace(",", ".");

    if (!normalizedValue) {
        return null;
    }

    if (!/^\d+(\.\d*)?$|^\.\d+$/.test(normalizedValue)) {
        return null;
    }

    const [rawIntegerPart, rawFractionPart = ""] = normalizedValue.split(".");
    const integerPart = rawIntegerPart || "0";
    const fractionPart = rawFractionPart
        .slice(0, TARGET_PRICE_DECIMALS)
        .padEnd(TARGET_PRICE_DECIMALS, "0");

    try {
        return BigInt(integerPart) * TARGET_PRICE_SCALE + BigInt(fractionPart);
    } catch {
        return null;
    }
}

function getTargetPriceStepUnits(currentUnits) {
    if (currentUnits >= decimalToUnits("1000")) {
        return decimalToUnits("100");
    }

    if (currentUnits >= decimalToUnits("100")) {
        return decimalToUnits("10");
    }

    if (currentUnits >= decimalToUnits("10")) {
        return decimalToUnits("1");
    }

    if (currentUnits >= decimalToUnits("1")) {
        return decimalToUnits("0.1");
    }

    return decimalToUnits("0.00000001");
}

function decimalToUnits(value) {
    const units = parseTargetPriceToUnits(value);

    if (units === null) {
        return 0n;
    }

    return units;
}

function clampTargetPriceUnits(units) {
    if (units < 0n) {
        return 0n;
    }

    if (units > MAX_TARGET_PRICE_UNITS) {
        return MAX_TARGET_PRICE_UNITS;
    }

    return units;
}

function formatTargetPriceUnits(units) {
    const safeUnits = clampTargetPriceUnits(units);
    const integerPart = safeUnits / TARGET_PRICE_SCALE;
    const fractionUnits = safeUnits % TARGET_PRICE_SCALE;

    if (fractionUnits === 0n) {
        return integerPart.toString();
    }

    const fractionPart = fractionUnits
        .toString()
        .padStart(TARGET_PRICE_DECIMALS, "0")
        .replace(/0+$/, "");

    return `${integerPart.toString()}.${fractionPart}`;
}

function validateTargetPriceInput() {
    const targetPriceUnits = parseTargetPriceToUnits(elements.targetPriceInput.value);

    if (targetPriceUnits === null) {
        showToast(TEXTS.targetPriceInvalid);
        return null;
    }

    if (targetPriceUnits <= 0n) {
        showToast(TEXTS.targetPriceRequired);
        return null;
    }

    if (targetPriceUnits > MAX_TARGET_PRICE_UNITS) {
        showToast(
            formatTemplate(TEXTS.targetPriceTooHighTemplate, {
                maxPrice: UI_LIMITS.maxTargetPriceUsd,
            }),
        );
        return null;
    }

    const normalizedPrice = formatTargetPriceUnits(targetPriceUnits);
    elements.targetPriceInput.value = normalizedPrice;

    return normalizedPrice;
}

/** Validate the create-alert form and submit a new price alert. */
export async function handleCreateAlert() {
    if (!state.isTelegramAuthenticated) {
        showToast(TEXTS.telegramOnlyFeature);
        return;
    }

    const coinId = elements.coinSelect.value;
    const condition = elements.conditionSelect.value;
    const targetPrice = validateTargetPriceInput();

    if (!coinId) {
        showToast(TEXTS.coinRequired);
        return;
    }

    if (!condition) {
        showToast(TEXTS.conditionRequired);
        return;
    }

    if (targetPrice === null) {
        return;
    }

    try {
        await createAlert({
            coinId,
            condition,
            targetPrice,
        });

        elements.targetPriceInput.value = "";
        showToast(TEXTS.alertCreated);

        state.alertsMode = ALERTS_MODE_ACTIVE;
        updateAlertsModeUi();

        await loadAlerts();
        setActiveViewDom("alerts");
    } catch (error) {
        showToast(error.message || TEXTS.alertCreateFailed);
    }
}

/** Confirm and disable an alert, then reload the current alerts mode. */
export async function handleDisableAlert(alertId, triggerElement = null) {
    if (!state.isTelegramAuthenticated) {
        showToast(TEXTS.telegramOnlyFeature);
        return;
    }

    const alert = findAlertById(alertId);
    const shouldDisable = await confirmAlertDisable(alert, triggerElement);

    if (!shouldDisable) {
        return;
    }

    try {
        await disableAlert(alertId);
        showToast(TEXTS.alertDisabled);
        await loadAlerts();
    } catch (error) {
        showToast(error.message || TEXTS.alertDisableFailed);
    }
}

function findAlertById(alertId) {
    const allVisibleAlerts = [
        ...state.activeAlerts,
        ...state.alertHistoryItems,
    ];

    return allVisibleAlerts.find((alert) => Number(alert.id) === Number(alertId)) ?? null;
}
