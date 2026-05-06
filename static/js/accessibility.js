const FONT_PREF_KEY = "mrgFontSizeLarge";

function applyFontPreference(enabled) {
    document.documentElement.style.setProperty("--font-scale", enabled ? "1.18" : "1");
    document.querySelector(".accessibility-toggle-button")?.classList.toggle("active", enabled);
}

function createAccessibilityButton() {
    if (document.querySelector(".accessibility-control")) return;

    const wrapper = document.createElement("div");
    wrapper.className = "accessibility-control";

    const button = document.createElement("button");
    button.type = "button";
    button.className = "accessibility-toggle-button";
    button.setAttribute("aria-label", "Aumentar fonte");
    button.setAttribute("title", "Aumentar fonte");
    button.innerHTML = "<span>Aa</span>";

    button.addEventListener("click", () => {
        const enabled = localStorage.getItem(FONT_PREF_KEY) !== "true";
        if (enabled) {
            localStorage.setItem(FONT_PREF_KEY, "true");
        } else {
            localStorage.removeItem(FONT_PREF_KEY);
        }
        applyFontPreference(enabled);
    });

    wrapper.appendChild(button);
    document.body.appendChild(wrapper);
}

window.addEventListener("DOMContentLoaded", () => {
    createAccessibilityButton();
    applyFontPreference(localStorage.getItem(FONT_PREF_KEY) === "true");
});
