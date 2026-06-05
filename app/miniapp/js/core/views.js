/** Tab/view switching without loading feature data. */

import { state } from "./state.js";
import { elements } from "./dom.js";

/** Switch active view markup without triggering feature data loads. */
export function setActiveViewDom(viewName) {
    if (!viewName) {
        return;
    }

    state.activeView = viewName;

    elements.tabs.forEach((button) => {
        button.classList.toggle("active", button.dataset.view === viewName);
    });

    elements.views.forEach((view) => {
        view.classList.toggle("active", view.id === `${viewName}View`);
    });
}
