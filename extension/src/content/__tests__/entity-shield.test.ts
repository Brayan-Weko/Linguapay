import { describe, expect, it } from "vitest";
import { EntityShield } from "../entity-shield";
import { OfflineMatcher } from "../offline-matcher";

describe("TypeScript EntityShield", () => {
  it("locks and restores amounts, phones, accounts, refs, and beneficiaries", () => {
    const input =
      "Référence TX-2026-9941 : Vous allez transférer 50 000 FCFA à Jean-Paul Mballa (+237 699 45 12 88) depuis **** 4821. Frais : 1 500 FCFA (3,00 %).";
    const shielded = EntityShield.lock(input);
    const values = Object.values(shielded.entities);

    expect(values).toContain("TX-2026-9941");
    expect(values).toContain("50 000 FCFA");
    expect(values).toContain("Jean-Paul Mballa");
    expect(values).toContain("+237 699 45 12 88");
    expect(values).toContain("**** 4821");
    expect(values).toContain("1 500 FCFA");
    expect(values).toContain("3,00 %");

    const outside = shielded.maskedText.replace(/\{\{[A-Z]+_\d+\}\}/g, "");
    expect(/\d/.test(outside)).toBe(false);
    expect(EntityShield.unlock(shielded.maskedText, shielded.entities)).toBe(input);
  });

  it("rejects corrupted translations in client integrity check", () => {
    const src = "Wa zu lôm {{AMT_1}} e be {{BEN_1}}.";
    expect(EntityShield.verifyClientIntegrity(src, "Wa zu lôm {{AMT_1}} e be {{BEN_1}}.")).toBe(true);
    expect(EntityShield.verifyClientIntegrity(src, "Wa zu lôm {{AMT_1}}.")).toBe(false);
    expect(EntityShield.verifyClientIntegrity(src, "Wa zu lôm 500 {{AMT_1}} e be {{BEN_1}}.")).toBe(false);
  });
});

describe("OfflineMatcher", () => {
  it("matches glossary entries and Label : {{TOKEN}} offline", () => {
    const matcher = new OfflineMatcher();
    matcher.loadBundle({
      language: "ewondo",
      entries: [
        {
          id: "FIN_BAL_001",
          criticality: "L2_TRANSACTION_CORE",
          fr: ["Solde disponible"],
          en: ["Available balance"],
          translation: "Moni woe a ne tebe",
        },
      ],
    });

    const hit = matcher.match("Solde disponible : {{AMT_1}}", "ewondo");
    expect(hit).not.toBeNull();
    expect(hit?.translatedMasked).toBe("Moni woe a ne tebe : {{AMT_1}}");
  });
});

