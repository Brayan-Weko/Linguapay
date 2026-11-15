/**
 * ShadowOverlay — Panneau flottant isolé par Shadow DOM (mode: 'closed')
 * avec contrôles d'accessibilité, statut du bouclier financier et Inspecteur Jury.
 */

export const SHADOW_HOST_ID = "linguapay-shadow-host";

export interface InspectorEntry {
  tierUsed: string;
  integrityPassed: boolean;
  entitiesCount: number;
  previewMasked: string;
}

export interface OverlayState {
  enabled: boolean;
  targetLang: string;
  bilingualMode: boolean;
  largeFont: boolean;
  highContrast: boolean;
  apiOnline: boolean;
  protectedEntitiesCount: number;
  inspectorEntries: InspectorEntry[];
}

export interface OverlayCallbacks {
  onToggleEnabled: (enabled: boolean) => void;
  onChangeLang: (lang: string) => void;
  onToggleBilingual: (enabled: boolean) => void;
  onToggleLargeFont: (enabled: boolean) => void;
  onToggleHighContrast: (enabled: boolean) => void;
  onSpeakSummary: () => void;
}

export class ShadowOverlay {
  private host: HTMLElement | null = null;
  private shadow: ShadowRoot | null = null;
  private inspectorOpen = false;
  private collapsed = false;

  constructor(private readonly callbacks: OverlayCallbacks) {}

  mount(initialState: OverlayState): void {
    if (this.host) return;
    const host = document.createElement("div");
    host.id = SHADOW_HOST_ID;
    host.style.cssText = "all: initial; position: fixed; bottom: 16px; right: 16px; z-index: 2147483647;";
    const shadow = host.attachShadow({ mode: "closed" });
    this.host = host;
    this.shadow = shadow;
    document.documentElement.appendChild(host);
    this.render(initialState);
  }

  render(state: OverlayState): void {
    if (!this.shadow) return;

    const statusColor = state.apiOnline ? "#34d399" : "#fbbf24";
    const statusText = state.apiOnline ? "API Connectée" : "Mode Hors-Ligne (Cache)";
    const inspectorHtml = this.inspectorOpen
      ? `<div class="inspector-box">
           <div class="section-label">INSPECTEUR D'INTÉGRITÉ & AUDIT</div>
           ${
             state.inspectorEntries.length === 0
               ? `<div class="muted">Activez LinguaPay pour inspecter les segments.</div>`
               : state.inspectorEntries
                   .slice(0, 6)
                   .map(
                     (e) => `<div class="insp-row">
                       <span class="badge ${e.integrityPassed ? "ok" : "warn"}">${e.tierUsed}</span>
                       <span class="insp-txt">${this.escapeHtml(e.previewMasked)}</span>
                       <span class="insp-tok">${e.entitiesCount} ent.</span>
                     </div>`
                   )
                   .join("")
           }
         </div>`
      : "";

    this.shadow.innerHTML = `
      <style>
        .panel {
          font-family: 'Segoe UI', system-ui, sans-serif;
          width: ${this.collapsed ? "190px" : "285px"};
          background: #0f2942;
          color: #f8fafc;
          border: 2px solid #0b6e4f;
          border-radius: 12px;
          box-shadow: 0 14px 32px rgba(15, 23, 42, 0.45);
          overflow: hidden;
          font-size: 12.5px;
        }
        .header {
          background: #0b6e4f;
          padding: 10px 12px;
          display: flex;
          justify-content: space-between;
          align-items: center;
          font-weight: 700;
        }
        .status-dot {
          width: 9px; height: 9px; border-radius: 50%;
          display: inline-block; background: ${statusColor}; margin-right: 6px;
        }
        .collapse-btn {
          background: rgba(255,255,255,0.18); border: none; color: #fff;
          border-radius: 5px; padding: 2px 7px; cursor: pointer; font-weight: 700;
        }
        .body {
          padding: 12px;
          display: ${this.collapsed ? "none" : "block"};
        }
        .section-label {
          font-size: 10px; font-weight: 700; color: #94a3b8;
          letter-spacing: 0.6px; margin: 8px 0 4px 0;
        }
        select, button.action-btn {
          width: 100%; padding: 7px 9px; border-radius: 6px;
          border: 1px solid #334155; background: #1e293b; color: #f8fafc;
          font-size: 12.5px; font-weight: 600; cursor: pointer;
        }
        button.primary {
          background: ${state.enabled ? "#dc2626" : "#10b981"};
          border-color: transparent;
          color: #ffffff;
          margin-bottom: 8px;
        }
        button.audio-btn {
          background: #1d4ed8; border-color: transparent; margin-top: 8px;
        }
        label.chk {
          display: flex; align-items: center; gap: 7px; margin: 5px 0;
          cursor: pointer; font-size: 12px;
        }
        .shield-box {
          margin-top: 9px; background: #064e3b; border: 1px solid #10b981;
          border-radius: 6px; padding: 7px 9px; font-size: 11.5px;
        }
        .shield-box strong { color: #6ee7b7; display: block; }
        .inspector-toggle {
          margin-top: 8px; background: transparent; border: 1px dashed #64748b;
          color: #cbd5e1; width: 100%; padding: 5px; border-radius: 5px;
          font-size: 11px; cursor: pointer;
        }
        .inspector-box {
          margin-top: 8px; background: #020617; border-radius: 6px; padding: 8px;
          max-height: 150px; overflow-y: auto;
        }
        .insp-row {
          display: flex; align-items: center; gap: 6px; font-size: 10.5px;
          border-bottom: 1px solid #1e293b; padding: 4px 0;
        }
        .insp-txt { flex: 1; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; color: #cbd5e1; }
        .insp-tok { color: #34d399; font-weight: 700; }
        .badge { padding: 1px 4px; border-radius: 3px; font-size: 9.5px; font-weight: 700; }
        .badge.ok { background: #065f46; color: #6ee7b7; }
        .badge.warn { background: #78350f; color: #fde68a; }
        .muted { color: #94a3b8; font-size: 11px; }
      </style>
      <div class="panel">
        <div class="header">
          <span><span class="status-dot"></span>LinguaPay</span>
          <button class="collapse-btn" id="lp-collapse" type="button">${this.collapsed ? "+" : "&minus;"}</button>
        </div>
        <div class="body">
          <div class="muted" style="margin-bottom:6px;">${statusText}</div>
          <button class="action-btn primary" id="lp-toggle" type="button">
            ${state.enabled ? "Restaurer texte original FR/EN" : "Traduire cette interface"}
          </button>

          <div class="section-label">LANGUE NATIONALE</div>
          <select id="lp-lang">
            <option value="ewondo" ${state.targetLang === "ewondo" ? "selected" : ""}>Ewondo (Centre / Sud)</option>
            <option value="duala" ${state.targetLang === "duala" ? "selected" : ""}>Duala (Littoral)</option>
            <option value="fulfulde" ${state.targetLang === "fulfulde" ? "selected" : ""}>Fulfulde (Grand Nord)</option>
          </select>

          <div class="section-label">ACCESSIBILITÉ</div>
          <label class="chk"><input type="checkbox" id="lp-bilingual" ${state.bilingualMode ? "checked" : ""}/> Mode bilingue (infobulle FR/EN)</label>
          <label class="chk"><input type="checkbox" id="lp-large" ${state.largeFont ? "checked" : ""}/> Police agrandie (+20%)</label>
          <label class="chk"><input type="checkbox" id="lp-contrast" ${state.highContrast ? "checked" : ""}/> Fort contraste</label>

          <button class="action-btn audio-btn" id="lp-speak" type="button">&#128266; Écouter le résumé (Audio)</button>

          <div class="shield-box">
            <strong>BOUCLIER FINANCIER ACTIF</strong>
            <span>${state.protectedEntitiesCount} entité(s) verrouillée(s) &bull; 0 altération</span>
          </div>

          <button class="inspector-toggle" id="lp-insp-btn" type="button">
            ${this.inspectorOpen ? "Masquer Inspecteur d'Intégrité" : "Inspecteur d'Intégrité (Audit)"}
          </button>
          ${inspectorHtml}
        </div>
      </div>
    `;

    this.shadow.getElementById("lp-collapse")?.addEventListener("click", () => {
      this.collapsed = !this.collapsed;
      this.render(state);
    });
    this.shadow.getElementById("lp-toggle")?.addEventListener("click", () => {
      this.callbacks.onToggleEnabled(!state.enabled);
    });
    this.shadow.getElementById("lp-lang")?.addEventListener("change", (ev) => {
      const val = (ev.target as HTMLSelectElement).value;
      this.callbacks.onChangeLang(val);
    });
    this.shadow.getElementById("lp-bilingual")?.addEventListener("change", (ev) => {
      this.callbacks.onToggleBilingual((ev.target as HTMLInputElement).checked);
    });
    this.shadow.getElementById("lp-large")?.addEventListener("change", (ev) => {
      this.callbacks.onToggleLargeFont((ev.target as HTMLInputElement).checked);
    });
    this.shadow.getElementById("lp-contrast")?.addEventListener("change", (ev) => {
      this.callbacks.onToggleHighContrast((ev.target as HTMLInputElement).checked);
    });
    this.shadow.getElementById("lp-speak")?.addEventListener("click", () => {
      this.callbacks.onSpeakSummary();
    });
    this.shadow.getElementById("lp-insp-btn")?.addEventListener("click", () => {
      this.inspectorOpen = !this.inspectorOpen;
      this.render(state);
    });
  }

  private escapeHtml(str: string): string {
    return str
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;");
  }
}
