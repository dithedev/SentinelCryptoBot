/** DOM references used across Mini App features. */

/** Cached DOM nodes for top-level screens, forms, and shared UI controls. */
export const elements = {
    authStatus: document.querySelector("#authStatus"),

    tabs: document.querySelectorAll(".tab-button"),
    views: document.querySelectorAll(".view"),

    pricesList: document.querySelector("#pricesList"),
    refreshPricesButton: document.querySelector("#refreshPricesButton"),

    alertsTitle: document.querySelector("#alertsTitle"),
    alertsDescription: document.querySelector("#alertsDescription"),
    alertsModeButtons: document.querySelectorAll("[data-alerts-mode]"),
    alertsList: document.querySelector("#alertsList"),
    refreshAlertsButton: document.querySelector("#refreshAlertsButton"),

    coinSelect: document.querySelector("#coinSelect"),
    coinSelectButton: document.querySelector("#coinSelectButton"),
    coinSelectButtonText: document.querySelector("#coinSelectButtonText"),
    coinSelectList: document.querySelector("#coinSelectList"),

    conditionSelect: document.querySelector("#conditionSelect"),
    conditionSelectButton: document.querySelector("#conditionSelectButton"),
    conditionSelectButtonText: document.querySelector("#conditionSelectButtonText"),
    conditionSelectList: document.querySelector("#conditionSelectList"),

    chainSelect: document.querySelector("#chainSelect"),
    chainSelectButton: document.querySelector("#chainSelectButton"),
    chainSelectButtonText: document.querySelector("#chainSelectButtonText"),
    chainSelectList: document.querySelector("#chainSelectList"),

    targetPriceInput: document.querySelector("#targetPriceInput"),
    increaseTargetPriceButton: document.querySelector("#increaseTargetPriceButton"),
    decreaseTargetPriceButton: document.querySelector("#decreaseTargetPriceButton"),
    createAlertForm: document.querySelector("#createAlertForm"),

    riskCheckForm: document.querySelector("#riskCheckForm"),
    contractAddressInput: document.querySelector("#contractAddressInput"),
    riskCheckSubmitButton: document.querySelector("#riskCheckSubmitButton"),
    riskCheckResult: document.querySelector("#riskCheckResult"),

    whaleSettingsForm: document.querySelector("#whaleSettingsForm"),
    whaleAlertsEnabledInput: document.querySelector("#whaleAlertsEnabledInput"),
    whaleMinUsdInput: document.querySelector("#whaleMinUsdInput"),
    whaleSettingsSubmitButton: document.querySelector("#whaleSettingsSubmitButton"),
    whaleSettingsStatus: document.querySelector("#whaleSettingsStatus"),
    refreshWhalesButton: document.querySelector("#refreshWhalesButton"),
    whaleTrackedAssets: document.querySelector("#whaleTrackedAssets"),
    whaleEventTypes: document.querySelector("#whaleEventTypes"),
    whaleProviderWarning: document.querySelector("#whaleProviderWarning"),
    whaleEventsList: document.querySelector("#whaleEventsList"),

    toast: document.querySelector("#toast"),

    disableConfirmModal: document.querySelector("#disableConfirmModal"),
    disableConfirmTitle: document.querySelector("#disableConfirmTitle"),
    disableConfirmDescription: document.querySelector("#disableConfirmDescription"),
    cancelDisableAlertButton: document.querySelector("#cancelDisableAlertButton"),
    confirmDisableAlertButton: document.querySelector("#confirmDisableAlertButton"),
};
