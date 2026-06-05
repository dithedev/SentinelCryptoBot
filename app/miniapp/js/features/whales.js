/** Whales screen settings, event pagination, and summary rendering. */

import { getWhaleEvents, getWhaleSettings, updateWhaleSettings } from "../api.js";
import { TEXTS, UI_LIMITS } from "../texts.js";
import { elements } from "../core/dom.js";
import { DEFAULT_WHALE_MIN_USD_VALUE, state } from "../core/state.js";
import {
    escapeHtml,
    formatDateTime,
    formatPlainDecimal,
    formatPrice,
    formatTemplate,
} from "../core/formatting.js";
import { showToast } from "../core/toast.js";
import { renderTelegramOnlyScreens } from "../core/telegram_gate.js";
import { renderEmptyText, renderLoadingCard } from "../ui/common.js";
import { bindLoadMoreHandler, renderLoadMoreButton } from "../ui/pagination.js";

const MIN_WHALE_MIN_USD_VALUE = UI_LIMITS.minWhaleUsd;
const MAX_WHALE_MIN_USD_VALUE = UI_LIMITS.maxWhaleUsd;

/** Load whale settings/events the first time the Whales tab is opened. */
export async function ensureWhaleScreenLoaded() {
    if (!state.isTelegramAuthenticated) {
        renderTelegramOnlyScreens();
        return;
    }

    renderWhaleTrackingSummary();

    await loadWhaleSettings();

    if (!state.whaleEvents.length) {
        await loadWhaleEventsFirstPage();
    }
}

/** Reload whale settings and the first page of events. */
export async function refreshWhaleScreen() {
    if (!state.isTelegramAuthenticated) {
        renderTelegramOnlyScreens();
        return;
    }

    await loadWhaleSettings();
    await loadWhaleEventsFirstPage();
}

/** Refresh whale settings while preserving the current event list. */
export async function refreshWhaleSettings() {
    await loadWhaleSettings();
}

async function loadWhaleSettings() {
    if (!state.isTelegramAuthenticated) {
        setWhaleSettingsStatus(TEXTS.telegramOnlyFeature);
        return;
    }

    setWhaleSettingsStatus(TEXTS.loading);

    try {
        const settings = await getWhaleSettings();

        state.whaleSettings = settings;
        state.syncingWhaleSettingsUi = true;
        elements.whaleAlertsEnabledInput.checked = Boolean(settings.is_enabled);
        elements.whaleMinUsdInput.value = formatPlainDecimal(settings.min_usd_value);
        state.syncingWhaleSettingsUi = false;

        setWhaleSettingsStatus(getWhaleSettingsStatusText(settings));
    } catch (error) {
        setWhaleSettingsStatus(TEXTS.whaleSettingsLoadFailed);
        showToast(error.message || TEXTS.whaleSettingsLoadFailed);
    }
}

/** Save only the whale alerts enabled toggle. */
export async function saveWhaleAlertsEnabled(isEnabled) {
    if (!state.isTelegramAuthenticated) {
        showToast(TEXTS.telegramOnlyFeature);
        return;
    }

    if (state.whaleSettingsSaving) {
        return;
    }

    state.whaleSettingsSaving = true;
    setWhaleSettingsStatus(TEXTS.saving ?? "Saving");
    elements.whaleAlertsEnabledInput.disabled = true;

    try {
        const settings = await updateWhaleSettings({ isEnabled });

        applyWhaleSettingsToForm(settings);
        setWhaleSettingsStatus(getWhaleSettingsStatusText(settings));
        showToast(TEXTS.whaleSettingsSaved);
    } catch (error) {
        state.syncingWhaleSettingsUi = true;
        elements.whaleAlertsEnabledInput.checked = Boolean(state.whaleSettings?.is_enabled);
        state.syncingWhaleSettingsUi = false;
        setWhaleSettingsStatus(TEXTS.whaleSettingsSaveFailed);
        showToast(error.message || TEXTS.whaleSettingsSaveFailed);
    } finally {
        elements.whaleAlertsEnabledInput.disabled = false;
        state.whaleSettingsSaving = false;
    }
}

/** Save the full whale settings form. */
export async function saveWhaleSettings() {
    if (!state.isTelegramAuthenticated) {
        showToast(TEXTS.telegramOnlyFeature);
        return;
    }

    const minUsdValue = validateWhaleMinUsdInput();

    if (minUsdValue === null) {
        return;
    }

    if (state.whaleSettingsSaving) {
        return;
    }

    state.whaleSettingsSaving = true;
    setWhaleSettingsStatus(TEXTS.saving ?? "Saving");
    elements.whaleSettingsSubmitButton.disabled = true;

    try {
        const settings = await updateWhaleSettings({
            isEnabled: Boolean(elements.whaleAlertsEnabledInput.checked),
            minUsdValue,
        });

        applyWhaleSettingsToForm(settings);
        setWhaleSettingsStatus(getWhaleSettingsStatusText(settings));
        showToast(TEXTS.whaleSettingsSaved);
    } catch (error) {
        setWhaleSettingsStatus(TEXTS.whaleSettingsSaveFailed);
        showToast(error.message || TEXTS.whaleSettingsSaveFailed);
    } finally {
        elements.whaleSettingsSubmitButton.disabled = false;
        state.whaleSettingsSaving = false;
    }
}

function applyWhaleSettingsToForm(settings) {
    state.whaleSettings = settings;
    state.syncingWhaleSettingsUi = true;
    elements.whaleAlertsEnabledInput.checked = Boolean(settings.is_enabled);
    elements.whaleMinUsdInput.value = formatPlainDecimal(settings.min_usd_value);
    state.syncingWhaleSettingsUi = false;
}

function validateWhaleMinUsdInput() {
    const value = elements.whaleMinUsdInput.value.trim().replace(",", ".");

    if (!value) {
        showToast(TEXTS.whaleMinUsdRequired);
        return null;
    }

    if (!/^\d+(\.\d*)?$|^\.\d+$/.test(value)) {
        showToast(TEXTS.whaleMinUsdInvalid);
        return null;
    }

    const numberValue = Number(value);

    if (!Number.isFinite(numberValue) || numberValue <= 0) {
        showToast(TEXTS.whaleMinUsdInvalid);
        return null;
    }

    if (numberValue < MIN_WHALE_MIN_USD_VALUE) {
        showToast(
            formatTemplate(TEXTS.whaleMinUsdTooLowTemplate, {
                minValue: MIN_WHALE_MIN_USD_VALUE,
            }),
        );
        return null;
    }

    if (numberValue > MAX_WHALE_MIN_USD_VALUE) {
        showToast(
            formatTemplate(TEXTS.whaleMinUsdTooHighTemplate, {
                maxValue: MAX_WHALE_MIN_USD_VALUE,
            }),
        );
        return null;
    }

    return value;
}

function getWhaleSettingsStatusText(settings) {
    if (settings.is_enabled) {
        return TEXTS.whaleAlertsEnabledStatus;
    }

    return TEXTS.whaleAlertsDisabledStatus;
}

/** Apply static whale form labels from TEXTS. */
export function applyWhaleFormLabels() {
    if (elements.whaleSettingsSubmitButton) {
        elements.whaleSettingsSubmitButton.textContent = TEXTS.saveWhaleSettingsButton;
    }
}

/** Update the whale settings status text. */
export function setWhaleSettingsStatus(text) {
    if (elements.whaleSettingsStatus) {
        elements.whaleSettingsStatus.textContent = text;
    }
}

async function loadWhaleEventsFirstPage() {
    if (!state.isTelegramAuthenticated) {
        elements.whaleEventsList.innerHTML = renderEmptyText(TEXTS.telegramOnlyFeature);
        return;
    }

    elements.whaleEventsList.innerHTML = renderLoadingCard();

    state.whaleEvents = [];
    state.whaleEventsOffset = 0;
    state.whaleEventsHasMore = false;

    try {
        const page = await getWhaleEvents({
            limit: UI_LIMITS.whaleEventsPageSize,
            offset: 0,
        });

        state.whaleEvents = page.items;
        state.whaleEventsOffset = page.offset + page.items.length;
        state.whaleEventsHasMore = page.has_more;

        renderWhaleEvents();
    } catch (error) {
        elements.whaleEventsList.innerHTML = renderEmptyText(TEXTS.whaleEventsLoadFailed);
        showToast(error.message || TEXTS.whaleEventsLoadFailed);
    }
}

async function loadMoreWhaleEvents() {
    if (state.isWhaleEventsLoadingMore || !state.whaleEventsHasMore) {
        return;
    }

    state.isWhaleEventsLoadingMore = true;
    renderWhaleEvents();

    try {
        const page = await getWhaleEvents({
            limit: UI_LIMITS.whaleEventsPageSize,
            offset: state.whaleEventsOffset,
        });

        state.whaleEvents = [...state.whaleEvents, ...page.items];
        state.whaleEventsOffset = page.offset + page.items.length;
        state.whaleEventsHasMore = page.has_more;
    } catch (error) {
        showToast(error.message || TEXTS.whaleEventsLoadFailed);
    } finally {
        state.isWhaleEventsLoadingMore = false;
        renderWhaleEvents();
    }
}

function renderWhaleEvents() {
    if (!state.whaleEvents.length) {
        elements.whaleEventsList.innerHTML = renderEmptyText(TEXTS.emptyWhaleEvents);
        return;
    }

    const cardsHtml = state.whaleEvents.map(renderWhaleEventCard).join("");
    const loadMoreHtml = state.whaleEventsHasMore
        ? renderLoadMoreButton({
              dataAttribute: "load-more-whales",
              buttonText: TEXTS.loadMoreWhaleEventsButton,
              loadingText: TEXTS.loadingMoreWhaleEventsButton,
              isLoading: state.isWhaleEventsLoadingMore,
          })
        : "";

    elements.whaleEventsList.innerHTML = `${cardsHtml}${loadMoreHtml}`;
    bindLoadMoreHandler(
        elements.whaleEventsList,
        "load-more-whales",
        loadMoreWhaleEvents,
    );
}

function renderWhaleEventCard(event) {
    return `
        <article class="data-card whale-card">
            <div class="whale-card-body">
                <div class="whale-card-heading">
                    <h3 class="card-title">
                        ${escapeHtml(event.symbol)} - $${formatPrice(event.amount_usd)}
                    </h3>
                    <span class="whale-badge">
                        ${escapeHtml(getWhaleEventTypeLabel(event.event_type))}
                    </span>
                </div>

                <p class="card-meta">
                    ${escapeHtml(formatPrice(event.amount))}
                    ${escapeHtml(event.symbol)}
                    on ${escapeHtml(String(event.network ?? "").toUpperCase())}
                </p>

                <div class="detail-list">
                    <span>
                        ${escapeHtml(TEXTS.detectedAtLabel ?? "Detected")}:
                        ${escapeHtml(formatDateTime(event.detected_at))}
                    </span>
                    <span>
                        ${escapeHtml(TEXTS.transactionLabel ?? "Transaction")}:
                        <span class="hash-value">
                            ${escapeHtml(event.transaction_hash)}
                        </span>
                    </span>
                </div>
            </div>
        </article>
    `;
}

function getWhaleEventTypeLabel(eventType) {
    return TEXTS.whaleEventTypeLabels?.[eventType] ?? eventType;
}

/** Render tracked assets, event types, and provider warning copy. */
export function renderWhaleTrackingSummary() {
    const trackedAssets = (state.config?.supported_coins ?? [])
        .map((coin) => coin.symbol)
        .join(", ");

    const eventTypes = Object.values(TEXTS.whaleEventTypeLabels ?? {})
        .filter((label) => label !== TEXTS.whaleEventTypeLabels.unknown)
        .join(", ");
    const trackedAssetsLabel = TEXTS.whaleTrackedAssetsLabel;
    const trackedAssetsFallback = TEXTS.whaleTrackedAssetsFallback;
    const eventTypesLabel = TEXTS.whaleEventTypesLabel;
    const providerWarning = TEXTS.whaleSimulatedProviderWarning;

    if (elements.whaleTrackedAssets) {
        elements.whaleTrackedAssets.textContent = `${trackedAssetsLabel}: ${
            trackedAssets || trackedAssetsFallback
        }`;
    }

    if (elements.whaleEventTypes) {
        elements.whaleEventTypes.textContent = `${eventTypesLabel}: ${eventTypes}`;
    }

    if (elements.whaleProviderWarning) {
        elements.whaleProviderWarning.textContent = providerWarning;
    }
}
