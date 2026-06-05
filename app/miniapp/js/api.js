/** HTTP client helpers for Mini App API routes. */

import { requireTelegramInitData } from "./telegram.js";

const API_BASE_URL = window.location.origin;

async function requestJson(path, options = {}) {
    const headers = new Headers(options.headers ?? {});

    headers.set("Content-Type", "application/json");
    headers.set("X-Telegram-Init-Data", requireTelegramInitData());

    const response = await fetch(`${API_BASE_URL}${path}`, {
        ...options,
        headers,
    });

    if (!response.ok) {
        const errorPayload = await readErrorPayload(response);
        throw new Error(errorPayload.detail ?? `Request failed: ${response.status}`);
    }

    if (response.status === 204) {
        return null;
    }

    return response.json();
}

async function publicRequestJson(path) {
    const response = await fetch(`${API_BASE_URL}${path}`);

    if (!response.ok) {
        const errorPayload = await readErrorPayload(response);
        throw new Error(errorPayload.detail ?? `Request failed: ${response.status}`);
    }

    return response.json();
}

async function readErrorPayload(response) {
    try {
        return await response.json();
    } catch {
        return {};
    }
}

/** Return the Telegram-authenticated Mini App user. */
export async function getMe() {
    return requestJson("/miniapp-api/me");
}

/** Return public Mini App options such as coins, chains, and UI limits. */
export async function getMiniAppConfig() {
    return publicRequestJson("/miniapp-api/config");
}

/** Return current market prices for supported coins. */
export async function getPrices() {
    return publicRequestJson("/prices");
}

/** Return active price alerts for the authenticated user. */
export async function getAlerts() {
    return requestJson("/miniapp-api/alerts");
}

/** Return a paginated alert history page. */
export async function getAlertHistory({ limit, offset }) {
    const searchParams = new URLSearchParams();

    searchParams.set("limit", String(limit));
    searchParams.set("offset", String(offset));

    return requestJson(`/miniapp-api/alerts/history?${searchParams.toString()}`);
}

/** Create a new price alert for the authenticated user. */
export async function createAlert({ coinId, targetPrice, condition }) {
    return requestJson("/miniapp-api/alerts", {
        method: "POST",
        body: JSON.stringify({
            coin_id: coinId,
            target_price: targetPrice,
            condition,
        }),
    });
}

/** Disable an active price alert. */
export async function disableAlert(alertId) {
    return requestJson(`/miniapp-api/alerts/${alertId}/disable`, {
        method: "PATCH",
    });
}

/** Run the token risk analyzer for a chain and contract address. */
export async function checkTokenRisk({ chain, contractAddress }) {
    return requestJson("/miniapp-api/risk-check", {
        method: "POST",
        body: JSON.stringify({
            chain,
            contract_address: contractAddress,
        }),
    });
}

/** Return whale alert settings for the authenticated user. */
export async function getWhaleSettings() {
    return requestJson("/miniapp-api/whales/settings");
}

/** Partially update whale alert settings. */
export async function updateWhaleSettings({ isEnabled, minUsdValue } = {}) {
    const payload = {};

    if (isEnabled !== undefined) {
        payload.is_enabled = isEnabled;
    }

    if (minUsdValue !== undefined) {
        payload.min_usd_value = minUsdValue;
    }

    return requestJson("/miniapp-api/whales/settings", {
        method: "PATCH",
        body: JSON.stringify(payload),
    });
}

/** Return a paginated whale event page. */
export async function getWhaleEvents({ limit, offset }) {
    const searchParams = new URLSearchParams();

    searchParams.set("limit", String(limit));
    searchParams.set("offset", String(offset));

    return requestJson(`/miniapp-api/whales/events?${searchParams.toString()}`);
}
