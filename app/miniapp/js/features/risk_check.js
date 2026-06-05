/** Risk check screen form controls, API flow, and result rendering. */

import { checkTokenRisk } from "../api.js";
import { TEXTS } from "../texts.js";
import { elements } from "../core/dom.js";
import { state, TAX_SIGNAL_NAMES } from "../core/state.js";
import { escapeHtml } from "../core/formatting.js";
import { showToast } from "../core/toast.js";
import { renderEmptyText, renderLoadingCard } from "../ui/common.js";
import {
    closeAllCustomSelects,
    renderCustomSelectEmpty,
} from "../ui/custom_select.js";

/** Render blockchain options for the risk check form. */
export function renderChainOptions(chains) {
    const safeChains = chains.length ? chains : [];

    state.selectedChain = null;
    elements.chainSelect.value = "";
    elements.chainSelectButtonText.textContent = TEXTS.chooseChainPlaceholder;

    if (!safeChains.length) {
        elements.chainSelectList.innerHTML = renderCustomSelectEmpty(
            TEXTS.noChainsAvailable,
        );
        return;
    }

    elements.chainSelectList.innerHTML = safeChains
        .map((chain) => {
            return `
                <button
                    class="custom-select-option"
                    type="button"
                    role="option"
                    aria-selected="false"
                    data-chain="${escapeHtml(chain)}"
                >
                    <span>
                        <span class="custom-select-option-main">
                            ${escapeHtml(chain.toUpperCase())}
                        </span>
                    </span>
                </button>
            `;
        })
        .join("");

    elements.chainSelectList.querySelectorAll("[data-chain]").forEach((button) => {
        button.addEventListener("click", () => {
            const chain = button.dataset.chain;

            if (chain) {
                selectChain(chain);
            }
        });
    });

    selectChain(safeChains[0]);
}

function selectChain(chain) {
    state.selectedChain = chain;
    elements.chainSelect.value = chain;
    elements.chainSelectButtonText.textContent = chain.toUpperCase();

    elements.chainSelectList.querySelectorAll("[data-chain]").forEach((button) => {
        const isSelected = button.dataset.chain === chain;

        button.classList.toggle("selected", isSelected);
        button.setAttribute("aria-selected", String(isSelected));
    });

    closeAllCustomSelects();
}

/** Validate and submit a token risk check request. */
export async function handleRiskCheck() {
    if (!state.isTelegramAuthenticated) {
        showToast(TEXTS.telegramOnlyFeature);
        return;
    }

    if (state.isRiskCheckLoading) {
        return;
    }

    const chain = elements.chainSelect.value;
    const contractAddress = elements.contractAddressInput.value.trim();

    if (!chain) {
        showToast(TEXTS.chainRequired);
        return;
    }

    if (!contractAddress) {
        showToast(TEXTS.contractAddressRequired);
        return;
    }

    state.isRiskCheckLoading = true;
    elements.riskCheckSubmitButton.disabled = true;
    elements.riskCheckSubmitButton.textContent = TEXTS.loading;
    elements.riskCheckResult.innerHTML = renderLoadingCard();

    try {
        const result = await checkTokenRisk({
            chain,
            contractAddress,
        });

        renderRiskCheckResult(result);
        showToast(TEXTS.tokenChecked);
    } catch {
        elements.riskCheckResult.innerHTML = renderEmptyText(TEXTS.riskCheckFailed);
        showToast(TEXTS.riskCheckFailed);
    } finally {
        state.isRiskCheckLoading = false;
        elements.riskCheckSubmitButton.disabled = false;
        elements.riskCheckSubmitButton.textContent = TEXTS.riskCheckSubmitButton;
    }
}

function renderRiskCheckResult(result) {
    const riskLevel = String(result.risk_level ?? "unknown");
    const riskLabel = getRiskLevelLabel(riskLevel);
    const riskClass = getRiskLevelClass(riskLevel);
    const flags = result.flags ?? {};
    const resultTitle = TEXTS.riskResultTitle ?? "Token risk report";
    const chainLabel = TEXTS.chainLabel ?? "Chain";
    const contractLabel = TEXTS.contractLabel ?? "Contract";
    const disclaimer =
        TEXTS.riskDisclaimer ??
        "This report is based on automated checks and does not guarantee that the token is safe.";

    elements.riskCheckResult.innerHTML = `
        <article class="data-card risk-result-card">
            <div class="risk-result-body">
                <div class="risk-result-heading">
                    <h3 class="card-title">
                        ${escapeHtml(resultTitle)}
                    </h3>
                    <span class="risk-badge ${riskClass}">
                        ${escapeHtml(riskLabel)}
                    </span>
                </div>

                <div class="risk-detail-list">
                    <p class="card-meta risk-detail-row">
                        <span class="risk-detail-label">${escapeHtml(chainLabel)}:</span>
                        <span>${escapeHtml(String(result.chain ?? "").toUpperCase())}</span>
                    </p>
                    <p class="card-meta risk-detail-row">
                        <span class="risk-detail-label">${escapeHtml(contractLabel)}:</span>
                        <span class="hash-value">
                            ${escapeHtml(result.contract_address ?? "")}
                        </span>
                    </p>
                </div>

                ${renderRiskSignals(flags, riskClass)}

                <p class="risk-disclaimer">
                    ${escapeHtml(disclaimer)}
                </p>
            </div>
        </article>
    `;
}

function renderRiskSignals(flags, riskClass) {
    const entries = Object.entries(flags);
    const signalsLabel =
        TEXTS.riskSignalsLabel ?? TEXTS.detectedSignalsLabel ?? "Detected signals";

    if (!entries.length) {
        return `
            <div class="risk-result-list">
                <p class="risk-signals-title">
                    ${escapeHtml(signalsLabel)}
                </p>
                <ul class="risk-signal-list">
                    <li class="risk-signal-empty ${riskClass}">
                        <span class="risk-signal-name">
                            ${escapeHtml(TEXTS.noRiskSignals)}
                        </span>
                    </li>
                </ul>
            </div>
        `;
    }

    return `
        <div class="risk-result-list">
            <p class="risk-signals-title">
                ${escapeHtml(signalsLabel)}
            </p>
            <ul class="risk-signal-list">
                ${entries
                    .map(([key, value]) => {
                        return `
                            <li class="${riskClass}">
                                <span class="risk-signal-name">
                                    ${escapeHtml(getRiskSignalLabel(key))}
                                </span>
                                <span class="risk-signal-value">
                                    ${escapeHtml(formatRiskSignalValue(key, value))}
                                </span>
                            </li>
                        `;
                    })
                    .join("")}
            </ul>
        </div>
    `;
}

function getRiskSignalLabel(signalName) {
    return TEXTS.riskSignalLabels?.[signalName] ?? signalName;
}

function formatRiskSignalValue(signalName, value) {
    if (value === true) {
        return TEXTS.riskSignalDetectedValue ?? "detected";
    }

    if (TAX_SIGNAL_NAMES.has(signalName) && typeof value === "number") {
        return `${Number(value).toLocaleString("en-US", {
            maximumFractionDigits: 4,
        })}%`;
    }

    return String(value);
}

function getRiskLevelLabel(riskLevel) {
    return (
        TEXTS.riskLevelLabels?.[riskLevel] ??
        TEXTS.riskStatusLabels?.[riskLevel] ??
        riskLevel
    );
}

function getRiskLevelClass(riskLevel) {
    return `risk-${String(riskLevel).toLowerCase()}`;
}
