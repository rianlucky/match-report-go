function toggleFontSize() {
    const checkbox = document.getElementById("fontToggle");
    const root = document.documentElement;

    if (checkbox.checked) {
        root.style.setProperty("--font-scale", "1.25");
        localStorage.setItem("fontSizeLarge", "true");
    } else {
        root.style.setProperty("--font-scale", "1");
        localStorage.removeItem("fontSizeLarge");
    }
    applyFontScaling();
}

function applyFontScaling() {
    const scale = getComputedStyle(document.documentElement).getPropertyValue("--font-scale") || "1";
    document.querySelectorAll("body *").forEach(el => {
        if (!["SCRIPT", "STYLE"].includes(el.tagName)) {
            el.style.fontSize = `calc(${scale} * 1rem)`;
        }
    });
}

window.addEventListener("DOMContentLoaded", () => {
    const toggle = document.getElementById("fontToggle");
    if (!toggle) return;

    if (localStorage.getItem("fontSizeLarge")) {
        toggle.checked = true;
        document.documentElement.style.setProperty("--font-scale", "1.25");
    } else {
        document.documentElement.style.setProperty("--font-scale", "1");
    }

    toggle.addEventListener("change", toggleFontSize);
    applyFontScaling();
});
