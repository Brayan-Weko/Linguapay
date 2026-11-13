/**
 * Background Service Worker (MV3) — Passerelle HTTPS/REST isolée du CSP de la cible.
 */

export const API_BASE_URL = "http://localhost:8000/api/v1";

chrome.runtime.onInstalled.addListener(() => {
  chrome.storage.local.set({
    linguapayEnabled: false,
    targetLang: "ewondo",
    bilingualMode: true,
    largeFont: false,
    highContrast: false,
  });
});

chrome.runtime.onMessage.addListener((message, _sender, sendResponse) => {
  if (!message || typeof message.type !== "string") return false;

  if (message.type === "LINGUAPAY_HEALTH") {
    fetch(`${API_BASE_URL}/health`)
      .then((r) => r.json())
      .then((data) => sendResponse({ ok: true, data }))
      .catch((err) => sendResponse({ ok: false, error: String(err) }));
    return true;
  }

  if (message.type === "LINGUAPAY_GET_GLOSSARY") {
    const lang = encodeURIComponent(message.lang || "ewondo");
    fetch(`${API_BASE_URL}/glossary/${lang}`)
      .then((r) => {
        if (!r.ok) throw new Error(`HTTP ${r.status}`);
        return r.json();
      })
      .then((data) => sendResponse({ ok: true, data }))
      .catch((err) => sendResponse({ ok: false, error: String(err) }));
    return true;
  }

  if (message.type === "LINGUAPAY_TRANSLATE_BATCH") {
    fetch(`${API_BASE_URL}/translate/batch`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(message.payload),
    })
      .then((r) => {
        if (!r.ok) throw new Error(`HTTP ${r.status}`);
        return r.json();
      })
      .then((data) => sendResponse({ ok: true, data }))
      .catch((err) => sendResponse({ ok: false, error: String(err) }));
    return true;
  }

  if (message.type === "LINGUAPAY_GET_TTS_SEQUENCE") {
    fetch(`${API_BASE_URL}/tts/sequence`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(message.payload),
    })
      .then((r) => {
        if (!r.ok) throw new Error(`HTTP ${r.status}`);
        return r.json();
      })
      .then((data) => sendResponse({ ok: true, data }))
      .catch((err) => sendResponse({ ok: false, error: String(err) }));
    return true;
  }

  return false;
});
