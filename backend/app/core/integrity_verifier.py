"""IntegrityVerifier: Circuit-Breaker preventing financial or polarity alteration."""

from __future__ import annotations

import re
from dataclasses import dataclass

TOKEN_RE = re.compile(r"\{\{[A-Z]+_\d+\}\}")

NEGATION_MARKERS_SOURCE: set[str] = {
    "ne",
    "jamais",
    "pas",
    "aucun",
    "aucune",
    "interdit",
    "refuse",
    "refusé",
    "impossible",
    "never",
    "not",
    "cannot",
    "cant",
    "dont",
    "do",
    "no",
}

DEFAULT_NEGATION_MARKERS_TARGET: dict[str, set[str]] = {
    "ewondo": {"te", "tege", "aa", "kokoa", "abé", "ka"},
    "duala": {"si", "titi", "bebe", "ke"},
    "fulfulde": {"taa", "waata", "walaa", "haa", "naa"},
}


@dataclass(frozen=True)
class VerificationResult:
    passed: bool
    reason: str


class IntegrityVerifier:
    """Enforces 100% placeholder preservation, zero invented digits, and negation polarity."""

    @staticmethod
    def verify(
        source_masked: str,
        target_masked: str,
        lang: str,
        criticality: str = "UI_NAV",
        target_negation_markers: set[str] | None = None,
    ) -> VerificationResult:
        if not target_masked or not target_masked.strip():
            return VerificationResult(False, "EMPTY_TRANSLATION")

        # 1. Exact multiset bijection of placeholders
        src_tokens = TOKEN_RE.findall(source_masked)
        tgt_tokens = TOKEN_RE.findall(target_masked)
        if sorted(src_tokens) != sorted(tgt_tokens):
            return VerificationResult(
                False,
                f"TOKEN_MISMATCH: expected {sorted(src_tokens)}, got {sorted(tgt_tokens)}",
            )

        # 2. Zero unexpected digits introduced outside placeholders
        cleaned_tgt = TOKEN_RE.sub("", target_masked)
        if re.search(r"\d", cleaned_tgt):
            return VerificationResult(False, "UNEXPECTED_DIGITS_INTRODUCED")

        # 3. Polarity guard on security warnings and dynamic unseen content
        if criticality in ("L1_CRITICAL_SECURITY", "CRITICAL_SECURITY", "UNSEEN_DYNAMIC"):
            src_words = set(re.findall(r"[a-zà-ÿ']+", source_masked.lower()))
            # Trigger check when strong negation words appear
            strong_neg = src_words & (NEGATION_MARKERS_SOURCE - {"do", "no"})
            if strong_neg or "do not" in source_masked.lower():
                allowed_neg = (
                    target_negation_markers
                    if target_negation_markers is not None
                    else DEFAULT_NEGATION_MARKERS_TARGET.get(lang.lower(), set())
                )
                tgt_words = set(re.findall(r"[a-zà-ÿəɔɛŋɓɗɲ']+", target_masked.lower()))
                if allowed_neg and not (tgt_words & allowed_neg):
                    return VerificationResult(False, "POLARITY_LOSS_ON_SECURITY_WARNING")

        return VerificationResult(True, "OK")
