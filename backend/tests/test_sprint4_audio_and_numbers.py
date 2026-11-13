"""Tests for Sprint 4: NumberComposer, AudioResolver, and TTS Audio Serving."""

from __future__ import annotations

import sys
from pathlib import Path
from fastapi.testclient import TestClient

BACKEND_DIR = Path(__file__).resolve().parents[1]
REPO_ROOT = Path(__file__).resolve().parents[2]
for p in (str(BACKEND_DIR), str(REPO_ROOT)):
    if p not in sys.path:
        sys.path.insert(0, p)

from app.core.glossary_engine import GlossaryEngine  # noqa: E402
from app.main import app  # noqa: E402
from app.tts.audio_resolver import AudioResolver  # noqa: E402
from app.tts.number_composer import NumberComposer  # noqa: E402

client = TestClient(app)
PACKS_DIR = REPO_ROOT / "linguistics" / "packs"


def test_number_composer_ewondo():
    g = GlossaryEngine(PACKS_DIR)
    pack = g.get_pack("ewondo")
    rules = pack.raw["number_rules"]

    # 0 FCFA
    c0 = NumberComposer.compose(0, rules)
    assert "ze" in c0.text and "falang CFA" in c0.text

    # 1 500 FCFA
    c1500 = NumberComposer.compose(1500, rules)
    assert "tósen" in c1500.text
    assert "ntet" in c1500.text
    assert "falang CFA" in c1500.text

    # 50 000 FCFA
    c50000 = NumberComposer.compose(50000, rules)
    assert "mewôm metán" in c50000.text
    assert "tósen" in c50000.text

    # 1 000 000 FCFA
    c1m = NumberComposer.compose(1_000_000, rules)
    assert "miliɔn" in c1m.text


def test_number_composer_duala_and_fulfulde():
    g = GlossaryEngine(PACKS_DIR)

    # Duala
    p_dua = g.get_pack("duala")
    c_dua = NumberComposer.compose(82400, p_dua.raw["number_rules"])
    assert "franka CFA" in c_dua.text
    assert "ikoli" in c_dua.text

    # Fulfulde
    p_ful = g.get_pack("fulfulde")
    c_ful = NumberComposer.compose(50000, p_ful.raw["number_rules"])
    assert "farank CFA" in c_ful.text
    assert "ujunere" in c_ful.text


def test_audio_resolver_summary():
    g = GlossaryEngine(PACKS_DIR)
    pack = g.get_pack("ewondo")

    summary_text = (
        "Vous allez transférer 50 000 FCFA à Jean-Paul Mballa. "
        "Frais : 1 500 FCFA. Total à débiter : 51 500 FCFA."
    )
    seq = AudioResolver.resolve_summary(summary_text, pack, audio_clip="audio/ewondo/fin_bal_001.ogg")

    assert seq.target_lang == "ewondo"
    assert len(seq.items) >= 4
    assert seq.total_duration_estimate_ms > 1000
    assert any("/api/v1/tts/capsule/ewondo/" in it.audio_url for it in seq.items)


def test_api_tts_sequence_and_capsule_endpoints():
    resp_seq = client.post(
        "/api/v1/tts/sequence",
        json={
            "target_lang": "ewondo",
            "text": "Solde disponible : 145 750 FCFA",
        },
    )
    assert resp_seq.status_code == 200
    data = resp_seq.json()
    assert data["target_lang"] == "ewondo"
    assert len(data["items"]) > 0

    first_url = data["items"][0]["audio_url"]
    resp_audio = client.get(first_url)
    assert resp_audio.status_code == 200
    assert resp_audio.headers["content-type"] == "audio/wav"
    # Check valid RIFF/WAVE header
    assert resp_audio.content.startswith(b"RIFF")
    assert b"WAVE" in resp_audio.content[:16]

