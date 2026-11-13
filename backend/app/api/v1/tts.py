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
    target_lang: str
    text: str = Field(min_length=1, max_length=1000)
    audio_clip: str | None = None


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


@router.post("/sequence")
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


@router.get("/capsule/{lang}/{clip_name}")
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
