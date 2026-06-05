/** Feature-aware navigation between Mini App tabs and alert modes. */

import { loadAlerts } from "../features/alerts.js";
import { ensureWhaleScreenLoaded } from "../features/whales.js";
import { updateAlertsModeUi } from "./alerts_mode.js";
import {
    ALERTS_MODE_ACTIVE,
    ALERTS_MODE_HISTORY,
    state,
} from "./state.js";
import { setActiveViewDom } from "./views.js";

/** Switch the active tab and load tab-specific data when required. */
export async function setActiveView(viewName) {
    if (!viewName) {
        return;
    }

    setActiveViewDom(viewName);

    if (viewName === "alerts") {
        await loadAlerts();
    }

    if (viewName === "whales") {
        await ensureWhaleScreenLoaded();
    }
}

/** Switch the alerts panel between active alerts and history. */
export async function setAlertsMode(mode) {
    if (![ALERTS_MODE_ACTIVE, ALERTS_MODE_HISTORY].includes(mode)) {
        return;
    }

    state.alertsMode = mode;
    updateAlertsModeUi();

    await loadAlerts();
}
