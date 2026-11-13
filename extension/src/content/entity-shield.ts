/**
 * EntityShield Client — Extraction, verrouillage et vérification d'invariance
 * des montants, pourcentages, téléphones CM, comptes, références et bénéficiaires.
 */

export type EntityType =
  | "AMOUNT"
  | "FEE"
  | "PERCENT"
  | "PHONE_CM"
  | "ACCOUNT"
  | "REF"
  | "DATE"
  | "TIME"
  | "BENEFICIARY"
  | "NUMBER";

export interface ShieldedText {
  maskedText: string;
  entities: Record<string, string>;
  entityTypes: Record<string, EntityType>;
}

const TOKEN_SPLIT_RE = /(\{\{[A-Z]+_\d+\}\})/;
const TOKEN_FIND_RE = /\{\{[A-Z]+_\d+\}\}/g;

const REF_RE = /\b(?:TX|REF|ID|OP)-[A-Z0-9-]{4,}\b/g;
const AMOUNT_RE =
  /(?:(?<!\w)[+-]\s?)?\b\d{1,3}(?:[\s\u00A0.,]\d{3})*(?:[.,]\d{1,2})?\s?(?:FCFA|F\s?CFA|XAF|CFA|EUR|USD|\$|€)(?=\b|[\s.,;:!?)]|$)/gi;
const PERCENT_RE = /\b\d+(?:[.,]\d+)?\s?%/g;
const PHONE_CM_RE = /(?:\+?237[\s.-]?)?6[\d*]{2}(?:[\s.-]?[\d*]{2}){2,3}\b/g;
const ACCOUNT_RE = /(?:\*{2,4}[\s-]?){1,3}\d{2,4}\b/g;
const DATE_RE = /\b\d{2}\/\d{2}\/\d{2,4}\b/g;
const TIME_RE = /\b(?:[01]?\d|2[0-3])[h:][0-5]\d\b/gi;
const RESIDUAL_NUM_RE = /\b\d+(?:[.,]\d+)?\b/g;

const BEN_LABEL_RE =
  /((?:Bénéficiaire|Destinataire|Beneficiary|Recipient)\s*:\s*)([A-ZÀ-Ÿ][A-Za-zÀ-Ÿà-ÿ'’-]+(?:\s+[A-ZÀ-Ÿ][A-Za-zÀ-Ÿà-ÿ'’-]+){0,3})/g;
const BEN_TRANSFER_RE =
  /((?:transférer|envoyer|transfer|send)\s+\{\{AMT_\d+\}\}\s+(?:à|to)\s+)([A-ZÀ-Ÿ][A-Za-zÀ-Ÿà-ÿ'’-]+(?:\s+[A-ZÀ-Ÿ][A-Za-zÀ-Ÿà-ÿ'’-]+){0,3})(?=\s*\(|\s*\.|\s*,|$)/gi;

function replaceOutsideTokens(
  text: string,
  pattern: RegExp,
  prefix: string,
  entityType: EntityType,
  entities: Record<string, string>,
  entityTypes: Record<string, EntityType>,
  counters: Record<string, number>
): string {
  const parts = text.split(TOKEN_SPLIT_RE);
  return parts
    .map((part) => {
      if (!part) return "";
      if (/^\{\{[A-Z]+_\d+\}\}$/.test(part)) return part;
      return part.replace(pattern, (matched) => {
        const nextIdx = (counters[prefix] ?? 0) + 1;
        counters[prefix] = nextIdx;
        const key = `${prefix}_${nextIdx}`;
        const token = `{{${key}}}`;
        entities[token] = matched;
        entityTypes[key] = entityType;
        return token;
      });
    })
    .join("");
}

export class EntityShield {
  static lock(text: string, knownBeneficiaries: string[] = []): ShieldedText {
    const entities: Record<string, string> = {};
    const entityTypes: Record<string, EntityType> = {};
    const counters: Record<string, number> = {};

    let masked = text;

    if (knownBeneficiaries.length > 0) {
      const sorted = [...knownBeneficiaries]
        .map((n) => n.trim())
        .filter(Boolean)
        .sort((a, b) => b.length - a.length);
      for (const name of sorted) {
        const escaped = name.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
        const re = new RegExp(`\\b${escaped}\\b`, "g");
        masked = replaceOutsideTokens(masked, re, "BEN", "BENEFICIARY", entities, entityTypes, counters);
      }
    }

    const orderedRules: Array<[RegExp, string, EntityType]> = [
      [REF_RE, "REF", "REF"],
      [AMOUNT_RE, "AMT", "AMOUNT"],
      [PERCENT_RE, "PCT", "PERCENT"],
      [PHONE_CM_RE, "PHONE", "PHONE_CM"],
      [ACCOUNT_RE, "ACC", "ACCOUNT"],
      [DATE_RE, "DATE", "DATE"],
      [TIME_RE, "TIME", "TIME"],
    ];

    for (const [regex, prefix, etype] of orderedRules) {
      masked = replaceOutsideTokens(masked, regex, prefix, etype, entities, entityTypes, counters);
    }

    for (const benRegex of [BEN_LABEL_RE, BEN_TRANSFER_RE]) {
      masked = masked.replace(benRegex, (full, p1: string, p2: string) => {
        if (p2.includes("{{") || p2.includes("}}")) return full;
        const nextIdx = (counters.BEN ?? 0) + 1;
        counters.BEN = nextIdx;
        const key = `BEN_${nextIdx}`;
        const token = `{{${key}}}`;
        entities[token] = p2;
        entityTypes[key] = "BENEFICIARY";
        return `${p1}${token}`;
      });
    }

    masked = replaceOutsideTokens(
      masked,
      RESIDUAL_NUM_RE,
      "NUM",
      "NUMBER",
      entities,
      entityTypes,
      counters
    );

    return { maskedText: masked, entities, entityTypes };
  }

  static unlock(translatedMasked: string, entities: Record<string, string>): string {
    let out = translatedMasked;
    for (const [token, original] of Object.entries(entities)) {
      out = out.split(token).join(original);
    }
    return out;
  }

  static verifyClientIntegrity(sourceMasked: string, targetMasked: string): boolean {
    if (!targetMasked || !targetMasked.trim()) return false;
    const srcTokens = (sourceMasked.match(TOKEN_FIND_RE) ?? []).sort();
    const tgtTokens = (targetMasked.match(TOKEN_FIND_RE) ?? []).sort();
    if (srcTokens.length !== tgtTokens.length) return false;
    for (let i = 0; i < srcTokens.length; i += 1) {
      if (srcTokens[i] !== tgtTokens[i]) return false;
    }
    const outsideDigits = targetMasked.replace(TOKEN_FIND_RE, "");
    return !/\d/.test(outsideDigits);
  }
}
