/** Shared Mini App state and feature constants. */

/** Alert list mode for currently monitored alerts. */
export const ALERTS_MODE_ACTIVE = "active";
/** Alert list mode for triggered and disabled alert history. */
export const ALERTS_MODE_HISTORY = "history";

/** Risk analyzer signal names that should be displayed as percentages. */
export const TAX_SIGNAL_NAMES = new Set(["buy_tax", "sell_tax"]);

/** Integer scale used to edit target prices without floating-point drift. */
export const TARGET_PRICE_SCALE = 100000000n;
/** Maximum number of decimal places supported by target prices. */
export const TARGET_PRICE_DECIMALS = 8;

/** Default whale alert minimum value used when API data is absent. */
export const DEFAULT_WHALE_MIN_USD_VALUE = "1000000";

/** Mutable client-side state shared by feature modules. */
export const state = {
    config: null,
    user: null,
    isTelegramAuthenticated: false,

    alertsMode: ALERTS_MODE_ACTIVE,
    activeAlerts: [],
    alertHistoryItems: [],
    alertHistoryOffset: 0,
    alertHistoryHasMore: false,
    isAlertHistoryLoadingMore: false,

    activeView: "prices",
    whaleSettings: null,
    whaleEvents: [],
    whaleEventsOffset: 0,
    whaleEventsHasMore: false,
    isWhaleEventsLoadingMore: false,
    whaleSettingsSaving: false,
    syncingWhaleSettingsUi: false,

    pricesRefreshAvailableAt: 0,
    pricesRefreshCooldownTimerId: null,

    selectedCoin: null,
    selectedCondition: null,
    selectedChain: null,
    isRiskCheckLoading: false,

    disableConfirmResolve: null,
    disableConfirmReturnFocusElement: null,
};
