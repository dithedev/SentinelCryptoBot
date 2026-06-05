/** Mini App browser entrypoint and event wiring. */

import { getMiniAppConfig } from "./api.js";
import { TEXTS } from "./texts.js";
import { initializeTelegramApp } from "./telegram.js";
import {
    authenticateTelegramUser,
    setAuthStatus,
} from "./core/auth.js";
import { elements } from "./core/dom.js";
import { state } from "./core/state.js";
import { showToast } from "./core/toast.js";
import { renderTelegramOnlyScreens } from "./core/telegram_gate.js";
import { setActiveView, setAlertsMode } from "./core/navigation.js";
import {
    changeTargetPriceStep,
    handleCreateAlert,
    loadAlerts,
    renderCoinOptions,
    renderConditionOptions,
} from "./features/alerts.js";
import { handlePricesRefreshClick, loadPrices } from "./features/prices.js";
import { handleRiskCheck, renderChainOptions } from "./features/risk_check.js";
import {
    refreshWhaleScreen,
    refreshWhaleSettings,
    applyWhaleFormLabels,
    renderWhaleTrackingSummary,
    saveWhaleAlertsEnabled,
    saveWhaleSettings,
} from "./features/whales.js";
import { closeAllCustomSelects, toggleCustomSelect } from "./ui/custom_select.js";
import {
    closeDisableConfirmModal,
    isDisableConfirmModalOpen,
} from "./ui/modal.js";

initializeTelegramApp();
bindEvents();
bootstrap();

/** Bind top-level DOM events to feature handlers. */
function bindEvents() {
    elements.tabs.forEach((button) => {
        button.addEventListener("click", async () => {
            await setActiveView(button.dataset.view);
        });
    });

    elements.alertsModeButtons.forEach((button) => {
        button.addEventListener("click", async () => {
            await setAlertsMode(button.dataset.alertsMode);
        });
    });

    elements.refreshPricesButton?.addEventListener("click", handlePricesRefreshClick);
    elements.refreshAlertsButton?.addEventListener("click", loadAlerts);
    elements.refreshWhalesButton?.addEventListener("click", refreshWhaleScreen);

    document.addEventListener("visibilitychange", () => {
        if (document.visibilityState === "visible" && state.activeView === "whales") {
            void refreshWhaleSettings();
        }
    });

    elements.coinSelectButton?.addEventListener("click", () => {
        toggleCustomSelect("coin");
    });

    elements.conditionSelectButton?.addEventListener("click", () => {
        toggleCustomSelect("condition");
    });

    elements.chainSelectButton?.addEventListener("click", () => {
        toggleCustomSelect("chain");
    });

    elements.increaseTargetPriceButton?.addEventListener("click", () => {
        changeTargetPriceStep(1);
    });

    elements.decreaseTargetPriceButton?.addEventListener("click", () => {
        changeTargetPriceStep(-1);
    });

    elements.createAlertForm?.addEventListener("submit", async (event) => {
        event.preventDefault();
        await handleCreateAlert();
    });

    elements.riskCheckForm?.addEventListener("submit", async (event) => {
        event.preventDefault();
        await handleRiskCheck();
    });

    elements.whaleSettingsForm?.addEventListener("submit", async (event) => {
        event.preventDefault();
        await saveWhaleSettings();
    });

    elements.whaleAlertsEnabledInput?.addEventListener("change", () => {
        if (state.syncingWhaleSettingsUi) {
            return;
        }

        void saveWhaleAlertsEnabled(Boolean(elements.whaleAlertsEnabledInput.checked));
    });

    elements.cancelDisableAlertButton?.addEventListener("click", () => {
        closeDisableConfirmModal(false);
    });

    elements.confirmDisableAlertButton?.addEventListener("click", () => {
        closeDisableConfirmModal(true);
    });

    elements.disableConfirmModal?.addEventListener("click", (event) => {
        if (event.target === elements.disableConfirmModal) {
            closeDisableConfirmModal(false);
        }
    });

    document.addEventListener("click", (event) => {
        if (!event.target.closest(".custom-select")) {
            closeAllCustomSelects();
        }
    });

    document.addEventListener("keydown", (event) => {
        if (event.key === "Escape" && isDisableConfirmModalOpen()) {
            closeDisableConfirmModal(false);
            return;
        }

        if (event.key === "Escape") {
            closeAllCustomSelects();
        }
    });
}

/** Load public data, authenticate Telegram user, and render initial screens. */
async function bootstrap() {
    setAuthStatus(TEXTS.loading);

    await loadPublicConfig();
    await loadPrices();
    await authenticateTelegramUser();

    if (!state.isTelegramAuthenticated) {
        renderTelegramOnlyScreens();
        return;
    }

    await loadAlerts();
}

/** Fetch Mini App config and hydrate selectors shared by multiple features. */
async function loadPublicConfig() {
    try {
        const config = await getMiniAppConfig();

        state.config = config;
        renderCoinOptions(config.supported_coins ?? []);
        renderConditionOptions(config.alert_conditions ?? []);
        renderChainOptions(config.supported_chains ?? []);
        applyWhaleFormLabels();
        renderWhaleTrackingSummary();
    } catch (error) {
        showToast(error.message || TEXTS.configLoadFailed);
    }
}
