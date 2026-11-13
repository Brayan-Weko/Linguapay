"""AudioResolver: constructs ordered playlist of audio capsules and verbalized amounts
for WebAudio sequential playback.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from app.core.glossary_engine import GlossaryPack
from app.tts.number_composer import NumberComposer, VerbalizedNumber

AMOUNT_PARSE_RE = re.compile(
    r"\b(\d{1,3}(?:[\s\u00A0.,]\d{3})*|\d+)\s*(?:FCFA|XAF|F\s?CFA|CFA)?\b",
    re.IGNORECASE,
)


@dataclass(frozen=True)
class AudioPlaylistItem:
    clip_id: str
    audio_url: str
    label: str
    duration_estimate_ms: int


@dataclass(frozen=True)
class AudioSequence:
    target_lang: str
    items: list[AudioPlaylistItem] = field(default_factory=list)
    full_transcript: str = ""
    total_duration_estimate_ms: int = 0


class AudioResolver:
    @classmethod
    def resolve_summary(
        cls,
        text: str,
        pack: GlossaryPack,
        audio_clip: str | None = None,
    ) -> AudioSequence:
        items: list[AudioPlaylistItem] = []
        transcript_parts: list[str] = []

        rules = pack.raw.get("number_rules", {})

        # If a dedicated pre-recorded capsule exists for this entire message
        if audio_clip:
            clean_name = audio_clip.split("/")[-1].replace(".ogg", "").replace(".wav", "").replace(".mp3", "")
            items.append(
                AudioPlaylistItem(
                    clip_id=clean_name,
                    audio_url=f"/api/v1/tts/capsule/{pack.language}/{clean_name}.wav",
                    label=text,
                    duration_estimate_ms=1600,
                )
            )
            transcript_parts.append(text)

        # Detect amounts in the text to verbalize them in national language
        amounts: list[int] = []
        for m in AMOUNT_PARSE_RE.finditer(text):
            raw_digits = re.sub(r"[^\d]", "", m.group(1))
            if raw_digits:
                val = int(raw_digits)
                # Keep significant financial figures (avoid isolated tiny numbers)
                if val >= 100 or "FCFA" in text or "CFA" in text:
                    amounts.append(val)

        for amt in amounts:
            verbal: VerbalizedNumber = NumberComposer.compose(amt, rules, include_currency=True)
            transcript_parts.append(verbal.text)
            for tok in verbal.tokens:
                items.append(
                    AudioPlaylistItem(
                        clip_id=tok,
                        audio_url=f"/api/v1/tts/capsule/{pack.language}/{tok}.wav",
                        label=tok,
                        duration_estimate_ms=450,
                    )
                )

        if not items:
            # Fallback single generic confirmation chime / chime capsule
            items.append(
                AudioPlaylistItem(
                    clip_id="tone_chime",
                    audio_url=f"/api/v1/tts/capsule/{pack.language}/tone_chime.wav",
                    label="Signal sonore",
                    duration_estimate_ms=500,
                )
            )
            transcript_parts.append(text)

        total_ms = sum(it.duration_estimate_ms for it in items)
        full_transcript = " | ".join(transcript_parts)

        return AudioSequence(
            target_lang=pack.language,
            items=items,
            full_transcript=full_transcript,
            total_duration_estimate_ms=total_ms,
        )
