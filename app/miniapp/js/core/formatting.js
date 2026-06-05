/** Shared formatting helpers for Mini App UI rendering. */

import { DEFAULT_WHALE_MIN_USD_VALUE } from "./state.js";

/** Format USD-style numbers while preserving useful precision for small prices. */
export function formatPrice(value) {
    const numberValue = Number(value);

    if (!Number.isFinite(numberValue)) {
        return String(value);
    }

    if (numberValue >= 1) {
        return numberValue.toLocaleString("en-US", {
            maximumFractionDigits: 2,
        });
    }

    return numberValue.toLocaleString("en-US", {
        maximumFractionDigits: 8,
    });
}

/** Format decimal values for text inputs without trailing zero noise. */
export function formatPlainDecimal(value) {
    if (value === null || value === undefined) {
        return DEFAULT_WHALE_MIN_USD_VALUE;
    }

    return String(value).replace(/\.?0+$/, "");
}

/** Format API timestamps for compact card metadata. */
export function formatDateTime(value) {
    if (!value) {
        return "";
    }

    const date = new Date(value);

    if (Number.isNaN(date.getTime())) {
        return String(value);
    }

    return date.toLocaleString("en-US", {
        month: "short",
        day: "2-digit",
        hour: "2-digit",
        minute: "2-digit",
    });
}

/** Replace named template placeholders with display values. */
export function formatTemplate(template, values) {
    return Object.entries(values).reduce((result, [key, value]) => {
        return result.replaceAll(`{${key}}`, String(value));
    }, template);
}

/** Escape user/API-provided values before interpolating them into HTML strings. */
export function escapeHtml(value) {
    return String(value)
        .replaceAll("&", "&amp;")
        .replaceAll("<", "&lt;")
        .replaceAll(">", "&gt;")
        .replaceAll('"', "&quot;")
        .replaceAll("'", "&#039;");
}
