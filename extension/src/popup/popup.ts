/**
 * Popup rapide de l'extension LinguaPay — synchronisé avec chrome.storage.local.
 */

const langSelect = document.getElementById("lang-select") as HTMLSelectElement | null;
const toggleBtn = document.getElementById("toggle-btn") as HTMLButtonElement | null;
const statusEl = document.getElementById("api-status");

function refreshLabel(enabled: boolean): void {
  if (toggleBtn) {
    toggleBtn.textContent = enabled ? "Désactiver sur cet onglet" : "Activer sur cet onglet";
    toggleBtn.style.background = enabled ? "#dc2626" : "#0b6e4f";
  }
}

chrome.storage.local.get(["linguapayEnabled", "targetLang"], (res) => {
  const enabled = Boolean(res.linguapayEnabled);
  if (langSelect && res.targetLang) {
    langSelect.value = String(res.targetLang);
  }
  refreshLabel(enabled);
});

chrome.runtime.sendMessage({ type: "LINGUAPAY_HEALTH" }, (resp) => {
  if (statusEl) {
    statusEl.textContent = resp?.ok ? "Core API : En ligne (port 8000)" : "Core API : Mode Hors-Ligne";
  }
});

langSelect?.addEventListener("change", () => {
  chrome.storage.local.set({ targetLang: langSelect.value });
});

toggleBtn?.addEventListener("click", () => {
  chrome.storage.local.get(["linguapayEnabled"], (res) => {
    const next = !Boolean(res.linguapayEnabled);
    chrome.storage.local.set({
      targetLang: langSelect?.value ?? "ewondo",
      linguapayEnabled: next,
    });
    refreshLabel(next);
  });
});
