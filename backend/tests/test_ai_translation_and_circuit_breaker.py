"""Sprint 3 backend tests: Level-3 constrained AI translation, LRU cache, and Circuit-Breaker."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import httpx
from fastapi.testclient import TestClient

BACKEND_DIR = Path(__file__).resolve().parents[1]
REPO_ROOT = Path(__file__).resolve().parents[2]
for p in (str(BACKEND_DIR), str(REPO_ROOT)):
    if p not in sys.path:
        sys.path.insert(0, p)

from app.api.v1 import translate as translate_mod  # noqa: E402
from app.config import Settings  # noqa: E402
from app.core.ai_translator import AITranslationResult, AITranslator  # noqa: E402
from app.core.glossary_engine import GlossaryEngine  # noqa: E402
from app.main import app  # noqa: E402

client = TestClient(app)
PACKS_DIR = REPO_ROOT / "linguistics" / "packs"


def test_ai_translator_gemini_mock_and_cache():
    calls = {"count": 0}

    def handler(request: httpx.Request) -> httpx.Response:
        calls["count"] += 1
        assert "generativelanguage.googleapis.com" in str(request.url)
        return httpx.Response(
            200,
            json={
                "candidates": [
                    {
                        "content": {
                            "parts": [
                                {
                                    "text": "Ésaé ya kôm é ne sondô nyi asô {{TIME_1}} akek {{TIME_2}}."
                                }
                            ]
                        }
                    }
                ]
            },
        )

    transport = httpx.MockTransport(handler)
    g_engine = GlossaryEngine(PACKS_DIR)
    pack = g_engine.get_pack("ewondo")
    assert pack is not None

    cfg = Settings(ai_provider="gemini", gemini_api_key="test-key")
    translator = AITranslator(settings=cfg)

    masked = "Maintenance prévue ce dimanche de {{TIME_1}} à {{TIME_2}}."
    res1 = translator.translate(masked, pack, transport=transport)
    assert res1 is not None
    assert res1.provider == "gemini"
    assert not res1.cached
    assert "{{TIME_1}}" in res1.translated_masked_text and "{{TIME_2}}" in res1.translated_masked_text

    # Second call hits LRU cache without hitting HTTP transport
    res2 = translator.translate(masked, pack, transport=transport)
    assert res2 is not None and res2.cached is True
    assert calls["count"] == 1


def test_ai_translator_ollama_mock():
    def handler(request: httpx.Request) -> httpx.Response:
        assert str(request.url).endswith("/api/chat")
        body = json.loads(request.content.decode("utf-8"))
        assert "{{AMT_1}}" in body["messages"][1]["content"]
        return httpx.Response(
            200,
            json={
                "message": {
                    "content": "Keng : te wa kañese lôm {{AMT_1}} amu ésaé é tege."
                }
            },
        )

    transport = httpx.MockTransport(handler)
    g_engine = GlossaryEngine(PACKS_DIR)
    pack = g_engine.get_pack("ewondo")
    assert pack is not None

    cfg = Settings(ai_provider="ollama", ollama_base_url="http://localhost:11434")
    translator = AITranslator(settings=cfg)

    res = translator.translate(
        "Alerte : ne validez jamais un transfert de {{AMT_1}} sans vérification.",
        pack,
        transport=transport,
    )
    assert res is not None
    assert res.provider == "ollama"
    assert "{{AMT_1}}" in res.translated_masked_text


def test_api_level3_unseen_success_and_circuit_breaker(monkeypatch):
    # Case 1: Valid Level-3 translation preserves tokens and negation
    def fake_ok(masked_text, pack):
        return AITranslationResult(
            translated_masked_text="Ésaé ya kôm asô {{TIME_1}} akek {{TIME_2}}.",
            provider="gemini",
            confidence=0.9,
        )

    monkeypatch.setattr(translate_mod.ai_translator, "translate", fake_ok)
    resp = client.post(
        "/api/v1/translate/batch",
        json={
            "target_lang": "ewondo",
            "source_lang": "fr",
            "items": [
                {
                    "id": "unseen_ok",
                    "text": "Maintenance ce dimanche de 02h00 à 04h00.",
                    "criticality": "UNSEEN_DYNAMIC",
                }
            ],
        },
    )
    assert resp.status_code == 200
    r = resp.json()["results"][0]
    assert r["tier_used"] == "AI_CONSTRAINED_L3"
    assert r["integrity_passed"] is True
    assert r["fallback_triggered"] is False
    assert "02h00" in (r["unlocked_text"] or "") and "04h00" in (r["unlocked_text"] or "")

    # Case 2: Hallucinated LLM drops {{AMT_1}} -> Circuit-Breaker MUST restore safe original!
    def fake_bad_token(masked_text, pack):
        return AITranslationResult(
            translated_masked_text="Keng : te wa lôm 5000 FCFA.",
            provider="gemini",
            confidence=0.7,
        )

    monkeypatch.setattr(translate_mod.ai_translator, "translate", fake_bad_token)
    resp2 = client.post(
        "/api/v1/translate",
        json={
            "target_lang": "ewondo",
            "source_lang": "fr",
            "text": "Alerte : ne validez pas ce transfert de 25 000 FCFA.",
            "criticality": "UNSEEN_DYNAMIC",
        },
    )
    assert resp2.status_code == 200
    r2 = resp2.json()
    assert r2["tier_used"] == "CIRCUIT_BREAKER_FALLBACK"
    assert r2["integrity_passed"] is False
    assert r2["fallback_triggered"] is True
    assert "25 000 FCFA" in (r2["unlocked_text"] or "")

