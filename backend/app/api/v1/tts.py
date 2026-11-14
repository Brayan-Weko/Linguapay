"""Routes /api/v1/tts/sequence and /api/v1/tts/capsule/{lang}/{clip_id}."""

from __future__ import annotations

import io
import math
import struct
import wave
from pathlib import Path
from fastapi import APIRouter, HTTPException, Response
from pydantic import BaseModel, Field

from app.api.v1.glossary import glossary_engine
from app.config import settings
from app.tts.audio_resolver import AudioResolver

router = APIRouter(prefix="/api/v1/tts", tags=["tts"])


class TTSSequenceRequest(BaseModel):
    target_lang: str = Field(
        description="Langue nationale pour la lecture vocale (ewondo, duala, fulfulde)",
        examples=["ewondo"],
    )
    text: str = Field(
        min_length=1,
        max_length=1000,
        description="Texte financier à verbaliser (avec ou sans montants en FCFA)",
        examples=["Solde disponible : 145 750 FCFA"],
    )
    audio_clip: str | None = Field(
        default=None,
        description="Lien direct optionnel vers une capsule audio spécifique du glossaire",
        examples=["audio/ewondo/fin_bal_001.ogg"],
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "target_lang": "ewondo",
                    "text": "Solde disponible : 145 750 FCFA",
                },
                {
                    "target_lang": "duala",
                    "text": "Vous allez transférer 50 000 FCFA à Jean-Paul Mballa (+237 699 45 12 88). Frais : 1 500 FCFA. Total à débiter : 51 500 FCFA.",
                },
                {
                    "target_lang": "fulfulde",
                    "text": "Solde disponible : 82 400 FCFA",
                },
            ]
        }
    }


class TTSPlaylistItem(BaseModel):
    clip_id: str = Field(description="Identifiant de la capsule sonore", examples=["fin_bal_001"])
    audio_url: str = Field(description="URL relative pour récupérer le flux binaire WAV", examples=["/api/v1/tts/capsule/ewondo/fin_bal_001.wav"])
    label: str = Field(description="Libellé textuel correspondant au segment", examples=["Moni woe a ne tebe"])
    duration_estimate_ms: int = Field(description="Estimation de la durée en millisecondes pour synchronisation", examples=[1200])


class TTSSequenceResponse(BaseModel):
    target_lang: str = Field(description="Langue nationale cible", examples=["ewondo"])
    full_transcript: str = Field(description="Transcription complète en langage naturel", examples=["Moni woe a ne tebe : tósen ntet a mewôm menyin a tán a ntet zamgbwal a mewôm metán falang CFA"])
    total_duration_estimate_ms: int = Field(description="Durée estimée totale de la séquence audio en millisecondes", examples=[3400])
    items: list[TTSPlaylistItem] = Field(description="Liste ordonnée des capsules audio à lire séquentiellement avec crossfade 25 ms")


def _generate_synthetic_pcm_wav(frequency_hz: float = 440.0, duration_sec: float = 0.25) -> bytes:
    """Generates a clean 16-bit mono 22050 Hz PCM WAV audio clip in pure Python."""
    sample_rate = 22050
    num_samples = int(sample_rate * duration_sec)
    buffer = io.BytesIO()

    with wave.open(buffer, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)

        samples: list[int] = []
        for i in range(num_samples):
            t = float(i) / sample_rate
            # Smooth envelope (attack + decay) to avoid clicks
            envelope = min(1.0, 10.0 * t, 10.0 * (duration_sec - t)) if duration_sec > 0.1 else 1.0
            val = int(32767.0 * 0.5 * envelope * math.sin(2.0 * math.pi * frequency_hz * t))
            samples.append(val)

        raw_data = struct.pack(f"<{len(samples)}h", *samples)
        wf.writeframes(raw_data)

    return buffer.getvalue()


@router.post(
    "/sequence",
    response_model=TTSSequenceResponse,
    summary="Calcul d'une playlist audio avec verbalisation grammaticale des montants FCFA",
    description="Prend en entrée une chaîne financière (solde, frais, récapitulatif), "
    "extrait et verbalise tous les montants monétaires en FCFA selon la grammaire de la langue nationale "
    "(Ewondo, Duala, Fulfulde), et génère la liste des capsules sonores prêtes à être enchaînées "
    "par le lecteur WebAudio avec un fondu croisé de 25 ms.",
    response_description="Transcription complète et liste des capsules audio ordonnées avec durées estimées.",
)
def get_audio_sequence(payload: TTSSequenceRequest) -> dict:
    pack = glossary_engine.get_pack(payload.target_lang.lower())
    if pack is None:
        raise HTTPException(
            status_code=404,
            detail=f"Unsupported target language '{payload.target_lang}'",
        )

    seq = AudioResolver.resolve_summary(payload.text, pack, audio_clip=payload.audio_clip)

    return {
        "target_lang": seq.target_lang,
        "full_transcript": seq.full_transcript,
        "total_duration_estimate_ms": seq.total_duration_estimate_ms,
        "items": [
            {
                "clip_id": it.clip_id,
                "audio_url": it.audio_url,
                "label": it.label,
                "duration_estimate_ms": it.duration_estimate_ms,
            }
            for it in seq.items
        ],
    }


@router.get(
    "/capsule/{lang}/{clip_name}",
    summary="Diffusion ou téléchargement d'une capsule audio WAV (PCM 22 050 Hz 16-bit)",
    description="Sert une capsule sonore au format WAV. Si le fichier physique pré-enregistré existe dans "
    "`linguistics/audio/{lang}/`, il est diffusé directement ; sinon, une capsule harmonique déterministe "
    "est synthétisée dynamiquement en mémoire avec enveloppe anti-clic et mise en cache disque.",
    responses={
        200: {
            "content": {"audio/wav": {}},
            "description": "Fichier audio PCM WAV 22 050 Hz mono.",
        },
        404: {"description": "Langue ou capsule inexistante."},
    },
)
def serve_audio_capsule(lang: str, clip_name: str) -> Response:
    lang_clean = lang.lower().strip()
    pack = glossary_engine.get_pack(lang_clean)
    if pack is None:
        raise HTTPException(status_code=404, detail="Language not found")

    clip_file = settings.linguistics_dir / "audio" / lang_clean / clip_name
    if clip_file.exists() and clip_file.is_file():
        audio_bytes = clip_file.read_bytes()
    else:
        # Generate tone deterministically based on hash of clip_name so different tokens have distinct musical pitches
        pitch_base = 320.0 + (abs(hash(clip_name)) % 360)
        dur = 0.35 if "thousand" in clip_name or "million" in clip_name else 0.22
        audio_bytes = _generate_synthetic_pcm_wav(frequency_hz=pitch_base, duration_sec=dur)
        # Cache to disk for instant subsequent serving
        clip_file.parent.mkdir(parents=True, exist_ok=True)
        try:
            clip_file.write_bytes(audio_bytes)
        except OSError:
            pass

    return Response(
        content=audio_bytes,
        media_type="audio/wav",
        headers={"Cache-Control": "public, max-age=86400"},
    )
