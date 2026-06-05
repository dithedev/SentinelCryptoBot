/** Telegram Web App SDK access helpers. */

import { TEXTS } from "./texts.js";

/** Return the Telegram Web App object when the page runs inside Telegram. */
export function getTelegramApp() {
    return window.Telegram?.WebApp ?? null;
}

/** Notify Telegram that the Mini App is ready and expand the viewport. */
export function initializeTelegramApp() {
    const tg = getTelegramApp();

    if (!tg) {
        return null;
    }

    tg.ready();
    tg.expand();

    return tg;
}

/** Return raw Telegram init data for backend authentication. */
export function getTelegramInitData() {
    const tg = getTelegramApp();
    return tg?.initData ?? "";
}

/** Return Telegram init data or throw when the page is opened outside Telegram. */
export function requireTelegramInitData() {
    const initData = getTelegramInitData();

    if (!initData) {
        throw new Error(TEXTS.authError);
    }

    return initData;
}
