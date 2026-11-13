"""GlossaryEngine: Level-1 deterministic & fuzzy financial glossary lookup."""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from pathlib import Path
from rapidfuzz import fuzz, process


_WS_PUNCT_RE = re.compile(r"[\s\u00A0]+")
_EDGE_PUNCT_RE = re.compile(r"^[\s.:;!?]+|[\s.:;!?]+$")


def normalize_phrase(text: str) -> str:
    cleaned = _WS_PUNCT_RE.sub(" ", text.strip().lower())
    return _EDGE_PUNCT_RE.sub("", cleaned)


@dataclass(frozen=True)
class GlossaryMatch:
    entry_id: str
    translation: str
    criticality: str
    confidence: float
    validation_status: str
    audio_clip: str | None = None


class GlossaryPack:
    """In-memory indexed language pack."""

    def __init__(self, raw_data: dict, etag: str) -> None:
        self.raw = raw_data
        self.etag = etag
        self.language: str = raw_data["language"]
        self.negation_markers: set[str] = {
            m.lower() for m in raw_data.get("negation_markers", [])
        }
        self.exact_index: dict[str, GlossaryMatch] = {}
        self.candidates: list[str] = []

        for entry in raw_data.get("entries", []):
            match_obj = GlossaryMatch(
                entry_id=entry["id"],
                translation=entry["translation"],
                criticality=entry["criticality"],
                confidence=1.0,
                validation_status=entry["validation_status"],
                audio_clip=entry.get("audio_clip"),
            )
            for phrase in entry.get("fr", []) + entry.get("en", []):
                norm = normalize_phrase(phrase)
                if norm and norm not in self.exact_index:
                    self.exact_index[norm] = match_obj
                    self.candidates.append(norm)


class GlossaryEngine:
    """Loads language packs and performs fast Level-1 lookup."""

    def __init__(self, packs_dir: Path, fuzzy_threshold: float = 92.0) -> None:
        self.packs_dir = packs_dir
        self.fuzzy_threshold = fuzzy_threshold
        self._packs: dict[str, GlossaryPack] = {}
        self.reload()

    def reload(self) -> None:
        self._packs.clear()
        if not self.packs_dir.exists():
            return
        for path in sorted(self.packs_dir.glob("*.json")):
            raw_bytes = path.read_bytes()
            etag = hashlib.sha256(raw_bytes).hexdigest()[:16]
            raw_data = json.loads(raw_bytes.decode("utf-8"))
            pack = GlossaryPack(raw_data=raw_data, etag=etag)
            self._packs[pack.language] = pack

    def available_languages(self) -> list[str]:
        return sorted(self._packs.keys())

    def get_pack(self, lang: str) -> GlossaryPack | None:
        return self._packs.get(lang.lower())

    def match(self, text: str, lang: str) -> GlossaryMatch | None:
        pack = self.get_pack(lang)
        if pack is None:
            return None

        norm = normalize_phrase(text)
        if not norm:
            return None

        # 1. Exact normalized match
        exact = pack.exact_index.get(norm)
        if exact is not None:
            return exact

        # 2. High-confidence fuzzy match (RapidFuzz WRatio / ratio)
        # Never fuzzy-match if length is too short (<6 chars) to prevent false positives
        if len(norm) < 6 or not pack.candidates:
            return None

        best = process.extractOne(norm, pack.candidates, scorer=fuzz.ratio)
        if best is None:
            return None
        matched_key, score, _ = best
        if score >= self.fuzzy_threshold:
            base = pack.exact_index[matched_key]
            return GlossaryMatch(
                entry_id=base.entry_id,
                translation=base.translation,
                criticality=base.criticality,
                confidence=round(score / 100.0, 4),
                validation_status=base.validation_status,
                audio_clip=base.audio_clip,
            )

        return None
