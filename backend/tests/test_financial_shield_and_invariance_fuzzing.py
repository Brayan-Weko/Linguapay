"""Sprint 2 tests: EntityShield, GlossaryEngine, TemplateEngine, IntegrityVerifier, Fuzzing & REST API."""

from __future__ import annotations

import json
import random
import sys
from pathlib import Path

from fastapi.testclient import TestClient

BACKEND_DIR = Path(__file__).resolve().parents[1]
REPO_ROOT = Path(__file__).resolve().parents[2]
for p in (str(BACKEND_DIR), str(REPO_ROOT)):
    if p not in sys.path:
        sys.path.insert(0, p)

from app.api.v1.glossary import audit_logger  # noqa: E402
from app.core.entity_shield import EntityShield  # noqa: E402
from app.core.glossary_engine import GlossaryEngine  # noqa: E402
from app.core.integrity_verifier import IntegrityVerifier  # noqa: E402
from app.core.template_engine import TemplateEngine  # noqa: E402
from app.main import app  # noqa: E402

client = TestClient(app)
PACKS_DIR = REPO_ROOT / "linguistics" / "packs"


# ---------------------------------------------------------------------------
# 1. EntityShield tests
# ---------------------------------------------------------------------------
def test_entity_shield_locks_all_financial_and_pii_types():
    sentence = (
        "Référence TX-2026-9941 le 10/11/2026 à 14h30 : "
        "Vous allez transférer 50 000 FCFA à Jean-Paul Mballa (+237 699 45 12 88) "
        "depuis Compte courant **** 4821. Frais : 1 500 FCFA (3,00 %)."
    )
    shielded = EntityShield.lock(sentence)

    # Zero unmasked digits should remain outside {{...}}
    import re
    outside_tokens = re.sub(r"\{\{[A-Z]+_\d+\}\}", "", shielded.masked_text)
    assert not re.search(r"\d", outside_tokens), f"Stray digits leaked: {outside_tokens}"

    # Verify exact values preserved
    values = set(shielded.entities.values())
    assert "TX-2026-9941" in values
    assert "10/11/2026" in values
    assert "14h30" in values
    assert "50 000 FCFA" in values
    assert "Jean-Paul Mballa" in values
    assert "+237 699 45 12 88" in values
    assert "**** 4821" in values
    assert "1 500 FCFA" in values
    assert "3,00 %" in values

    # Round-trip unlock must restore exact original text
    assert EntityShield.unlock(shielded.masked_text, shielded.entities) == sentence


def test_entity_shield_signed_amounts_and_masked_phones():
    text = "Mouvement -12 500 FCFA et dépôt +50 000 FCFA vers +237 6** ** 12."
    shielded = EntityShield.lock(text)
    assert "-12 500 FCFA" in shielded.entities.values()
    assert "+50 000 FCFA" in shielded.entities.values()
    assert "+237 6** ** 12" in shielded.entities.values()
    assert EntityShield.unlock(shielded.masked_text, shielded.entities) == text


# ---------------------------------------------------------------------------
# 2. GlossaryEngine & TemplateEngine tests
# ---------------------------------------------------------------------------
def test_glossary_exact_and_fuzzy_match():
    engine = GlossaryEngine(PACKS_DIR)
    assert engine.match("Solde disponible :", "ewondo") is not None
    assert engine.match("Available balance", "duala") is not None
    assert engine.match("Insufficient balance to complete this transaction.", "fulfulde") is not None

    # Minor typo (~95% similarity) should match via RapidFuzz
    fuzzy_hit = engine.match("Solde disponibl", "ewondo")
    assert fuzzy_hit is not None
    assert fuzzy_hit.confidence >= 0.92


def test_template_engine_simubank_summary_all_languages():
    g_engine = GlossaryEngine(PACKS_DIR)
    t_engine = TemplateEngine(g_engine)

    raw_fr = (
        "Vous allez transférer 50 000 FCFA à Jean-Paul Mballa (+237 699 45 12 88). "
        "Frais : 1 500 FCFA. Total à débiter : 51 500 FCFA."
    )
    shielded = EntityShield.lock(raw_fr)

    for lang in ("ewondo", "duala", "fulfulde"):
        m = t_engine.match(shielded.masked_text, lang)
        assert m is not None, f"Template failed to match for {lang}: {shielded.masked_text}"
        unlocked = EntityShield.unlock(m.translated_masked_text, shielded.entities)
        for must_keep in ("50 000 FCFA", "Jean-Paul Mballa", "+237 699 45 12 88", "1 500 FCFA", "51 500 FCFA"):
            assert must_keep in unlocked


def test_template_engine_structural_colon_and_paren():
    g_engine = GlossaryEngine(PACKS_DIR)
    t_engine = TemplateEngine(g_engine)

    for lang in ("ewondo", "duala", "fulfulde"):
        # Structural colon: "Total à débiter : 51 500 FCFA"
        s1 = EntityShield.lock("Total à débiter : 51 500 FCFA")
        m1 = t_engine.match(s1.masked_text, lang)
        assert m1 is not None, f"Failed structural colon match for {lang}"
        assert "51 500 FCFA" in EntityShield.unlock(m1.translated_masked_text, s1.entities)

        # Structural parentheses: "Frais de transaction (3,00 %)"
        s2 = EntityShield.lock("Frais de transaction (3,00 %)")
        m2 = t_engine.match(s2.masked_text, lang)
        assert m2 is not None, f"Failed structural parentheses match for {lang}"
        assert "3,00 %" in EntityShield.unlock(m2.translated_masked_text, s2.entities)


# ---------------------------------------------------------------------------
# 3. IntegrityVerifier & Circuit-Breaker tests
# ---------------------------------------------------------------------------
def test_integrity_verifier_rejects_corruptions():
    src = "Wa zu lôm {{AMT_1}} e be {{BEN_1}}. Frais : {{AMT_2}}."
    # Token dropped
    r1 = IntegrityVerifier.verify(src, "Wa zu lôm {{AMT_1}} e be {{BEN_1}}.", "ewondo", "FINANCIAL_CORE")
    assert not r1.passed and "TOKEN_MISMATCH" in r1.reason

    # Unexpected digit invented
    r2 = IntegrityVerifier.verify(src, "Wa zu lôm {{AMT_1}} e be {{BEN_1}}. Frais 500 : {{AMT_2}}.", "ewondo", "FINANCIAL_CORE")
    assert not r2.passed and r2.reason == "UNEXPECTED_DIGITS_INTRODUCED"

    # Polarity lost on security warning
    sec_src = "Attention : ne communiquez jamais votre code PIN."
    r3 = IntegrityVerifier.verify(sec_src, "Keng : wa kat mot mfe ékôd PIN woe.", "ewondo", "L1_CRITICAL_SECURITY")
    assert not r3.passed and r3.reason == "POLARITY_LOSS_ON_SECURITY_WARNING"

    # Polarity preserved
    r4 = IntegrityVerifier.verify(sec_src, "Keng : te wa kat mot mfe ékôd PIN woe.", "ewondo", "L1_CRITICAL_SECURITY")
    assert r4.passed


# ---------------------------------------------------------------------------
# 4. Financial Invariance Fuzzing (600 synthetic cases -> 0% alteration)
# ---------------------------------------------------------------------------
def test_financial_invariance_fuzzing_600_cases():
    rng = random.Random(20261126)
    names = ["Jean-Paul Mballa", "Clarisse Ndongo", "Moussa Abdoulaye", "Marie-Claire Atangana", "Samuel Eto'o"]
    currencies = ["FCFA", "XAF", "EUR", "USD"]

    g_engine = GlossaryEngine(PACKS_DIR)
    t_engine = TemplateEngine(g_engine)

    for i in range(600):
        amt = rng.randint(500, 9_950_000)
        fee = max(100, int(amt * rng.uniform(0.005, 0.035)))
        total = amt + fee
        cur = rng.choice(currencies)
        fmt_amt = f"{amt:,}".replace(",", " ") + f" {cur}"
        fmt_fee = f"{fee:,}".replace(",", " ") + f" {cur}"
        fmt_tot = f"{total:,}".replace(",", " ") + f" {cur}"
        ben = rng.choice(names)
        phone = f"+237 6{rng.randint(50, 99)} {rng.randint(10, 99)} {rng.randint(10, 99)} {rng.randint(10, 99)}"
        lang = rng.choice(("ewondo", "duala", "fulfulde"))

        raw = (
            f"Vous allez transférer {fmt_amt} à {ben} ({phone}). "
            f"Frais : {fmt_fee}. Total à débiter : {fmt_tot}."
        )
        shielded = EntityShield.lock(raw, known_beneficiaries=[ben])

        # Verify 0 stray digits outside placeholders
        import re
        assert not re.search(r"\d", re.sub(r"\{\{[A-Z]+_\d+\}\}", "", shielded.masked_text))

        # Translate & verify invariance
        m = t_engine.match(shielded.masked_text, lang)
        assert m is not None, f"Fuzz case {i} failed template match"
        v = IntegrityVerifier.verify(shielded.masked_text, m.translated_masked_text, lang, m.criticality)
        assert v.passed, f"Fuzz case {i} failed integrity: {v.reason}"
        restored = EntityShield.unlock(m.translated_masked_text, shielded.entities)
        for exact_val in (fmt_amt, fmt_fee, fmt_tot, ben, phone):
            assert exact_val in restored


# ---------------------------------------------------------------------------
# 5. REST API Contract & Zero-PII Audit Log tests
# ---------------------------------------------------------------------------
def test_glossary_endpoint_and_etag():
    resp = client.get("/api/v1/glossary/ewondo")
    assert resp.status_code == 200
    assert "ETag" in resp.headers
    data = resp.json()
    assert data["language"] == "ewondo"
    assert len(data["entries"]) >= 15
    assert len(data["templates"]) >= 4

    resp_404 = client.get("/api/v1/glossary/klingon")
    assert resp_404.status_code == 404


def test_translate_batch_and_zero_pii_audit():
    audit_logger.clear()
    secret_name = "Jean-Paul Mballa"
    secret_amount = "145 750 FCFA"

    payload = {
        "target_lang": "ewondo",
        "source_lang": "fr",
        "items": [
            {
                "id": "n1",
                "text": f"Solde disponible : {secret_amount}",
                "criticality": "FINANCIAL_CORE",
            },
            {
                "id": "n2",
                "masked_text": "Vous allez transférer {{AMT_1}} à {{BEN_1}}. Frais : {{FEE_1}}.",
                "entity_types": {"AMT_1": "AMOUNT", "BEN_1": "BENEFICIARY", "FEE_1": "FEE"},
                "criticality": "FINANCIAL_CORE",
            },
            {
                "id": "n3",
                "masked_text": "Attention : ne communiquez jamais votre code PIN.",
                "criticality": "L1_CRITICAL_SECURITY",
            },
            {
                "id": "n4",
                "masked_text": "Message inédit de maintenance le {{DATE_1}}.",
                "criticality": "UNSEEN_DYNAMIC",
            },
        ],
    }

    resp = client.post("/api/v1/translate/batch", json=payload)
    assert resp.status_code == 200
    body = resp.json()
    results = {r["id"]: r for r in body["results"]}

    assert results["n1"]["tier_used"] == "TEMPLATE_L2"
    assert results["n1"]["integrity_passed"] is True
    assert secret_amount in (results["n1"]["unlocked_text"] or "")

    assert results["n2"]["tier_used"] == "TEMPLATE_L2"
    assert "{{AMT_1}}" in results["n2"]["translated_masked_text"]
    assert "{{BEN_1}}" in results["n2"]["translated_masked_text"]
    assert "{{FEE_1}}" in results["n2"]["translated_masked_text"]

    assert results["n3"]["tier_used"] == "GLOSSARY_L1"
    assert results["n3"]["integrity_passed"] is True

    # In Sprint 2 (glossary_only), unseen falls back safely to original
    assert results["n4"]["tier_used"] == "FALLBACK_ORIGINAL"
    assert results["n4"]["fallback_triggered"] is True

    # Audit endpoint must NEVER contain raw PII or raw amounts
    audit_resp = client.get("/api/v1/audit/recent")
    assert audit_resp.status_code == 200
    audit_dump = json.dumps(audit_resp.json())
    assert secret_amount not in audit_dump
    assert secret_name not in audit_dump

