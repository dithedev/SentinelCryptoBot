/** Telegram authentication state and status pill rendering. */

import { getMe } from "../api.js";
import { TEXTS } from "../texts.js";
import { getTelegramInitData } from "../telegram.js";
import { showToast } from "./toast.js";
import { setTelegramOnlyFormState } from "./telegram_gate.js";
import { elements } from "./dom.js";
import { state } from "./state.js";

/** Update the top-level authentication status pill. */
export function setAuthStatus(text, statusClass = "") {
    elements.authStatus.textContent = text;
    elements.authStatus.classList.remove("ready", "error");

    if (statusClass) {
        elements.authStatus.classList.add(statusClass);
    }
}

/** Authenticate the Mini App user using Telegram init data. */
export async function authenticateTelegramUser() {
    if (!getTelegramInitData()) {
        state.isTelegramAuthenticated = false;
        setAuthStatus(TEXTS.browserPreview, "error");
        return;
    }

    try {
        state.user = await getMe();
        state.isTelegramAuthenticated = true;
        setTelegramOnlyFormState(false);
        setAuthStatus(TEXTS.ready, "ready");
    } catch (error) {
        state.isTelegramAuthenticated = false;
        setAuthStatus(TEXTS.authError, "error");
        showToast(error.message || TEXTS.authError);
    }
}
