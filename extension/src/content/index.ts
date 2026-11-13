/**
 * Point d'entrée Content Script LinguaPay — Orchestration DOM, Bouclier,
 * MutationObserver temps réel et Overlay Shadow DOM.
 */

import { AudioPlayer, AudioSequenceResponse } from "./audio-player";
import { DOMSnapshotManager, ScannedSegment } from "./dom-walker";
import { EntityShield, ShieldedText } from "./entity-shield";
import { MutationWatcher } from "./mutation-watcher";
import { GlossaryBundle, OfflineMatcher } from "./offline-matcher";
import { InspectorEntry, OverlayState, ShadowOverlay } from "./shadow-overlay";

interface BatchApiItemResult {
  id: string;
  translated_masked_text: string;
  tier_used: string;
  integrity_passed: boolean;
  fallback_triggered: boolean;
}

const domManager = new DOMSnapshotManager();
const offlineMatcher = new OfflineMatcher();
const audioPlayer = new AudioPlayer();

const state: OverlayState = {
  enabled: false,
  targetLang: "ewondo",
  bilingualMode: true,
  largeFont: false,
  highContrast: false,
  apiOnline: false,
  protectedEntitiesCount: 0,
  inspectorEntries: [],
};

const watcher = new MutationWatcher((roots) => {
  if (!state.enabled) return;
  for (const root of roots) {
    if (root.isConnected) {
      void translateRoot(root);
    }
  }
});

const overlay = new ShadowOverlay({
  onToggleEnabled: (enabled) => {
    state.enabled = enabled;
    chrome.storage?.local.set({ linguapayEnabled: enabled });
    if (enabled) {
      void activateTranslation();
    } else {
      deactivateTranslation();
    }
  },
  onChangeLang: (lang) => {
    state.targetLang = lang;
    chrome.storage?.local.set({ targetLang: lang });
    if (state.enabled) {
      deactivateTranslation();
      state.enabled = true;
      void activateTranslation();
    } else {
      overlay.render(state);
    }
  },
  onToggleBilingual: (bilingual) => {
    state.bilingualMode = bilingual;
    chrome.storage?.local.set({ bilingualMode: bilingual });
    if (state.enabled) {
      deactivateTranslation();
      state.enabled = true;
      void activateTranslation();
    } else {
      overlay.render(state);
    }
  },
  onToggleLargeFont: (large) => {
    state.largeFont = large;
    applyAccessibilityClasses();
    overlay.render(state);
  },
  onToggleHighContrast: (hc) => {
    state.highContrast = hc;
    applyAccessibilityClasses();
    overlay.render(state);
  },
  onSpeakSummary: () => {
    // Collect active financial summary sentence from DOM
    let summaryText = "";
    const modalSummary = document.getElementById("modal-summary-sentence");
    if (modalSummary && modalSummary.textContent?.trim()) {
      summaryText = modalSummary.textContent.trim();
    } else {
      const balanceEl = document.getElementById("account-balance");
      summaryText = balanceEl ? `Solde disponible : ${balanceEl.textContent?.trim()}` : "Solde disponible : 145 750 FCFA";
    }

    sendBgMessage<AudioSequenceResponse>({
      type: "LINGUAPAY_GET_TTS_SEQUENCE",
      payload: {
        target_lang: state.targetLang,
        text: summaryText,
      },
    }).then((resp) => {
      if (resp.ok && resp.data?.items) {
        void audioPlayer.playSequence(resp.data.items);
      }
    });
  },
});

function applyAccessibilityClasses(): void {
  const styleId = "linguapay-a11y-style";
  let styleEl = document.getElementById(styleId);
  if (!state.largeFont && !state.highContrast) {
    styleEl?.remove();
    return;
  }
  if (!styleEl) {
    styleEl = document.createElement("style");
    styleEl.id = styleId;
    document.head.appendChild(styleEl);
  }
  const rules: string[] = [];
  if (state.largeFont) {
    rules.push("body { font-size: 120% !important; }");
  }
  if (state.highContrast) {
    rules.push("[data-linguapay-translated='1'] { text-decoration: underline dotted #0b6e4f; }");
  }
  styleEl.textContent = rules.join("\n");
}

function sendBgMessage<T>(msg: unknown): Promise<{ ok: boolean; data?: T; error?: string }> {
  return new Promise((resolve) => {
    if (!chrome?.runtime?.sendMessage) {
      resolve({ ok: false, error: "No extension runtime" });
      return;
    }
    chrome.runtime.sendMessage(msg, (resp) => {
      if (chrome.runtime.lastError) {
        resolve({ ok: false, error: chrome.runtime.lastError.message });
      } else {
        resolve(resp ?? { ok: false, error: "Empty response" });
      }
    });
  });
}

async function ensureGlossaryLoaded(lang: string): Promise<void> {
  if (offlineMatcher.hasLanguage(lang)) return;
  const resp = await sendBgMessage<GlossaryBundle>({
    type: "LINGUAPAY_GET_GLOSSARY",
    lang,
  });
  if (resp.ok && resp.data) {
    offlineMatcher.loadBundle(resp.data);
    state.apiOnline = true;
    chrome.storage?.local.set({ [`glossary_${lang}`]: resp.data });
    return;
  }
  // Fallback to cached Indexed/chrome.storage glossary if offline
  const stored = await chrome.storage?.local.get(`glossary_${lang}`);
  const cachedBundle = stored?.[`glossary_${lang}`] as GlossaryBundle | undefined;
  if (cachedBundle) {
    offlineMatcher.loadBundle(cachedBundle);
  }
}

async function translateRoot(root: Node): Promise<void> {
  const segments = domManager.scan(root);
  if (segments.length === 0) return;

  const shieldedMap = new Map<string, { seg: ScannedSegment; shielded: ShieldedText }>();
  const apiItems: Array<{
    id: string;
    masked_text: string;
    entity_types: Record<string, string>;
    criticality: string;
  }> = [];

  for (const seg of segments) {
    const shielded = EntityShield.lock(seg.originalTrimmed);
    shieldedMap.set(seg.id, { seg, shielded });
    state.protectedEntitiesCount += Object.keys(shielded.entities).length;

    // Fast path: check API or fallback to offline matcher
    apiItems.push({
      id: seg.id,
      masked_text: shielded.maskedText,
      entity_types: shielded.entityTypes,
      criticality: seg.criticality,
    });
  }

  let results: BatchApiItemResult[] = [];
  const apiResp = await sendBgMessage<{ results: BatchApiItemResult[] }>({
    type: "LINGUAPAY_TRANSLATE_BATCH",
    payload: {
      target_lang: state.targetLang,
      source_lang: "auto",
      items: apiItems,
    },
  });

  if (apiResp.ok && apiResp.data?.results) {
    state.apiOnline = true;
    results = apiResp.data.results;
  } else {
    state.apiOnline = false;
    // Offline fail-safe using cached glossary
    results = apiItems.map((it) => {
      const hit = offlineMatcher.match(it.masked_text, state.targetLang);
      if (hit) {
        return {
          id: it.id,
          translated_masked_text: hit.translatedMasked,
          tier_used: `${hit.tier}_OFFLINE`,
          integrity_passed: true,
          fallback_triggered: false,
        };
      }
      return {
        id: it.id,
        translated_masked_text: it.masked_text,
        tier_used: "OFFLINE_ORIGINAL",
        integrity_passed: true,
        fallback_triggered: true,
      };
    });
  }

  const newEntries: InspectorEntry[] = [];
  watcher.runMuted(() => {
    for (const res of results) {
      const pair = shieldedMap.get(res.id);
      if (!pair) continue;
      const { seg, shielded } = pair;

      // Client-side defense-in-depth invariant check
      const clientValid =
        res.integrity_passed &&
        EntityShield.verifyClientIntegrity(shielded.maskedText, res.translated_masked_text);

      const finalMasked = clientValid ? res.translated_masked_text : shielded.maskedText;
      const finalTier = clientValid ? res.tier_used : "CLIENT_CIRCUIT_BREAKER";
      const restored = EntityShield.unlock(finalMasked, shielded.entities);

      if (!res.fallback_triggered && clientValid && restored !== seg.originalTrimmed) {
        domManager.applyTranslation(seg, restored, state.bilingualMode, finalTier);
      }

      newEntries.push({
        tierUsed: finalTier,
        integrityPassed: clientValid,
        entitiesCount: Object.keys(shielded.entities).length,
        previewMasked: shielded.maskedText,
      });
    }
  });

  state.inspectorEntries = [...newEntries.slice(0, 8), ...state.inspectorEntries].slice(0, 12);
  overlay.render(state);
}

async function activateTranslation(): Promise<void> {
  state.protectedEntitiesCount = 0;
  state.inspectorEntries = [];
  await ensureGlossaryLoaded(state.targetLang);
  await translateRoot(document.body);
  watcher.start(document.body);
  overlay.render(state);
}

function deactivateTranslation(): void {
  watcher.stop();
  watcher.runMuted(() => {
    domManager.restoreAll();
    domManager.clearTracking();
  });
  state.protectedEntitiesCount = 0;
  overlay.render(state);
}

async function bootstrap(): Promise<void> {
  const health = await sendBgMessage({ type: "LINGUAPAY_HEALTH" });
  state.apiOnline = health.ok;

  const saved = await chrome.storage?.local.get([
    "linguapayEnabled",
    "targetLang",
    "bilingualMode",
    "largeFont",
    "highContrast",
  ]);
  if (saved) {
    state.enabled = Boolean(saved.linguapayEnabled);
    state.targetLang = (saved.targetLang as string) || "ewondo";
    state.bilingualMode = saved.bilingualMode !== undefined ? Boolean(saved.bilingualMode) : true;
    state.largeFont = Boolean(saved.largeFont);
    state.highContrast = Boolean(saved.highContrast);
  }

  overlay.mount(state);
  applyAccessibilityClasses();

  if (state.enabled) {
    await activateTranslation();
  }

  chrome.storage?.onChanged.addListener((changes, area) => {
    if (area !== "local") return;
    if (changes.targetLang && changes.targetLang.newValue !== state.targetLang) {
      state.targetLang = String(changes.targetLang.newValue);
      if (state.enabled) {
        deactivateTranslation();
        state.enabled = true;
        void activateTranslation();
      } else {
        overlay.render(state);
      }
    }
    if (changes.linguapayEnabled && changes.linguapayEnabled.newValue !== state.enabled) {
      state.enabled = Boolean(changes.linguapayEnabled.newValue);
      if (state.enabled) {
        void activateTranslation();
      } else {
        deactivateTranslation();
      }
    }
  });
}

void bootstrap();
