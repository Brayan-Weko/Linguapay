"""Tests for Universal Language Pivot Bridge (Any source language -> EN pivot -> Cameroonian national languages)."""

from __future__ import annotations

import sys
from pathlib import Path
from fastapi.testclient import TestClient

BACKEND_DIR = Path(__file__).resolve().parents[1]
REPO_ROOT = Path(__file__).resolve().parents[2]
for p in (str(BACKEND_DIR), str(REPO_ROOT)):
    if p not in sys.path:
        sys.path.insert(0, p)

from app.core.entity_shield import EntityShield  # noqa: E402
from app.core.pivot_bridge import UniversalPivotBridge  # noqa: E402
from app.main import app  # noqa: E402

client = TestClient(app)


def test_language_detection_heuristics():
    assert UniversalPivotBridge.detect_language("Saldo disponible en cuenta") == "es"
    assert UniversalPivotBridge.detect_language("Verfügbares Guthaben und Überweisung") == "de"
    assert UniversalPivotBridge.detect_language("Saldo disponível para transferência") == "pt"
    assert UniversalPivotBridge.detect_language("Salio lililopo na gharama ya uhamisho") == "sw"
    assert UniversalPivotBridge.detect_language("Available balance in checking account") == "en"
    assert UniversalPivotBridge.detect_language("Votre solde disponible en compte") == "fr"


def test_spanish_pivot_preserves_tokens():
    shielded = EntityShield.lock("Saldo disponible : 145 750 FCFA")
    assert "{{AMT_1}}" in shielded.masked_text
    pivot = UniversalPivotBridge.pivot_to_english(shielded.masked_text, source_lang="es")
    assert pivot.pivoted is True
    assert "Available balance" in pivot.pivoted_text
    assert "{{AMT_1}}" in pivot.pivoted_text


def test_german_pivot_preserves_tokens():
    shielded = EntityShield.lock("Verfügbares Guthaben : 82 400 FCFA")
    pivot = UniversalPivotBridge.pivot_to_english(shielded.masked_text, source_lang="de")
    assert pivot.pivoted is True
    assert "Available balance" in pivot.pivoted_text
    assert "{{AMT_1}}" in pivot.pivoted_text


def test_e2e_api_translate_from_spanish_and_german():
    # Spanish site translation to Ewondo
    resp_es = client.post(
        "/api/v1/translate",
        json={
            "target_lang": "ewondo",
            "source_lang": "es",
            "text": "Saldo disponible : 145 750 FCFA",
            "criticality": "FINANCIAL_CORE",
        },
    )
    assert resp_es.status_code == 200
    r_es = resp_es.json()
    assert "145 750 FCFA" in r_es["unlocked_text"]
    assert r_es["tier_used"] in ("PIVOT_TEMPLATE_L2", "TEMPLATE_L2", "PIVOT_GLOSSARY_L1")
    assert r_es["integrity_passed"] is True

    # German site translation to Duala
    resp_de = client.post(
        "/api/v1/translate",
        json={
            "target_lang": "duala",
            "source_lang": "de",
            "text": "Verfügbares Guthaben : 50 000 FCFA",
            "criticality": "FINANCIAL_CORE",
        },
    )
    assert resp_de.status_code == 200
    r_de = resp_de.json()
    assert "50 000 FCFA" in r_de["unlocked_text"]
    assert r_de["integrity_passed"] is True

