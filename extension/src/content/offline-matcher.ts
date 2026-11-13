/**
 * OfflineMatcher — Cache local des glossaires & templates (mode offline-ready).
 */

export interface GlossaryEntry {
  id: string;
  criticality: string;
  fr: string[];
  en: string[];
  translation: string;
  audio_clip?: string | null;
}

export interface GlossaryBundle {
  language: string;
  display_name?: string;
  etag?: string;
  entries: GlossaryEntry[];
}

export interface OfflineMatchResult {
  translatedMasked: string;
  tier: "GLOSSARY_L1" | "TEMPLATE_L2";
  criticality: string;
  audioClip?: string | null;
}

function normalizePhrase(text: string): string {
  return text
    .trim()
    .toLowerCase()
    .replace(/[\s\u00A0]+/g, " ")
    .replace(/^[\s.:;!?]+|[\s.:;!?]+$/g, "");
}

export class OfflineMatcher {
  private packs = new Map<string, Map<string, GlossaryEntry>>();

  loadBundle(bundle: GlossaryBundle): void {
    const index = new Map<string, GlossaryEntry>();
    for (const entry of bundle.entries ?? []) {
      for (const phrase of [...(entry.fr ?? []), ...(entry.en ?? [])]) {
        const norm = normalizePhrase(phrase);
        if (norm && !index.has(norm)) {
          index.set(norm, entry);
        }
      }
    }
    this.packs.set(bundle.language.toLowerCase(), index);
  }

  hasLanguage(lang: string): boolean {
    return this.packs.has(lang.toLowerCase());
  }

  match(maskedText: string, lang: string): OfflineMatchResult | null {
    const index = this.packs.get(lang.toLowerCase());
    if (!index) return null;

    const norm = normalizePhrase(maskedText);
    const direct = index.get(norm);
    if (direct) {
      return {
        translatedMasked: direct.translation,
        tier: "GLOSSARY_L1",
        criticality: direct.criticality,
        audioClip: direct.audio_clip,
      };
    }

    const colon = maskedText.match(/^\s*(.+?)\s*:\s*(\{\{[A-Z]+_\d+\}\})\s*$/);
    if (colon) {
      const hit = index.get(normalizePhrase(colon[1]));
      if (hit) {
        return {
          translatedMasked: `${hit.translation} : ${colon[2]}`,
          tier: "TEMPLATE_L2",
          criticality: hit.criticality,
          audioClip: hit.audio_clip,
        };
      }
    }

    return null;
  }
}
