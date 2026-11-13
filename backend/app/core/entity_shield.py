"""EntityShield: deterministic extraction and locking of financial & PII entities."""

from __future__ import annotations

import re
from dataclasses import dataclass, field

TOKEN_SPLIT_RE = re.compile(r"(\{\{[A-Z]+_\d+\}\})")

# Ordered extraction rules (most specific first)
REF_RE = re.compile(r"\b(?:TX|REF|ID|OP)-[A-Z0-9-]{4,}\b")
ACCOUNT_RE = re.compile(r"(?:\*{2,4}[\s-]?){1,3}\d{2,4}\b")
AMOUNT_RE = re.compile(
    r"(?:(?<!\w)[+-]\s?)?\b\d{1,3}(?:[\s\u00A0.,]\d{3})*(?:[.,]\d{1,2})?\s?"
    r"(?:FCFA|F\s?CFA|XAF|CFA|EUR|USD|\$|€)(?=\b|[\s.,;:!?)]|$)",
    re.IGNORECASE,
)
PERCENT_RE = re.compile(r"\b\d+(?:[.,]\d+)?\s?%")
PHONE_CM_RE = re.compile(
    r"(?:\+?237[\s.-]?)?6[\d*]{2}(?:[\s.-]?[\d*]{2}){2,3}\b"
)
DATE_RE = re.compile(r"\b\d{2}/\d{2}/\d{2,4}\b")
TIME_RE = re.compile(r"\b(?:[01]?\d|2[0-3])[h:][0-5]\d\b", re.IGNORECASE)
RESIDUAL_NUM_RE = re.compile(r"\b\d+(?:[.,]\d+)?\b")

BEN_LABEL_RE = re.compile(
    r"((?:Bénéficiaire|Destinataire|Beneficiary|Recipient)\s*:\s*)"
    r"([A-ZÀ-Ÿ][A-Za-zÀ-Ÿà-ÿ'’-]+(?:\s+[A-ZÀ-Ÿ][A-Za-zÀ-Ÿà-ÿ'’-]+){0,3})"
)
BEN_TRANSFER_RE = re.compile(
    r"((?:transférer|envoyer|transfer|send)\s+\{\{AMT_\d+\}\}\s+(?:à|to)\s+)"
    r"([A-ZÀ-Ÿ][A-Za-zÀ-Ÿà-ÿ'’-]+(?:\s+[A-ZÀ-Ÿ][A-Za-zÀ-Ÿà-ÿ'’-]+){0,3})"
    r"(?=\s*\(|\s*\.|\s*,|$)",
    re.IGNORECASE,
)


@dataclass(frozen=True)
class ShieldedText:
    masked_text: str
    entities: dict[str, str] = field(default_factory=dict)
    entity_types: dict[str, str] = field(default_factory=dict)


class EntityShield:
    """Locks financial amounts, rates, phones, accounts, references, dates, and beneficiaries."""

    @staticmethod
    def _replace_outside_tokens(
        text: str,
        pattern: re.Pattern[str],
        prefix: str,
        entity_type: str,
        entities: dict[str, str],
        entity_types: dict[str, str],
        counters: dict[str, int],
        group_index: int = 0,
        keep_prefix_group: int | None = None,
    ) -> str:
        parts = TOKEN_SPLIT_RE.split(text)
        out: list[str] = []

        for part in parts:
            if not part:
                continue
            if TOKEN_SPLIT_RE.fullmatch(part):
                out.append(part)
                continue

            def _sub(match: re.Match[str]) -> str:
                val = match.group(group_index)
                idx = counters.get(prefix, 0) + 1
                counters[prefix] = idx
                token_key = f"{prefix}_{idx}"
                placeholder = f"{{{{{token_key}}}}}"
                entities[placeholder] = val
                entity_types[token_key] = entity_type
                if keep_prefix_group is not None:
                    return f"{match.group(keep_prefix_group)}{placeholder}"
                return placeholder

            out.append(pattern.sub(_sub, part))

        return "".join(out)

    @classmethod
    def lock(
        cls,
        text: str,
        known_beneficiaries: list[str] | None = None,
    ) -> ShieldedText:
        entities: dict[str, str] = {}
        entity_types: dict[str, str] = {}
        counters: dict[str, int] = {}

        masked = text

        # 1. Explicit known beneficiaries (if supplied by context)
        if known_beneficiaries:
            for name in sorted(known_beneficiaries, key=len, reverse=True):
                clean = name.strip()
                if not clean:
                    continue
                name_re = re.compile(rf"\b{re.escape(clean)}\b")
                masked = cls._replace_outside_tokens(
                    masked, name_re, "BEN", "BENEFICIARY", entities, entity_types, counters
                )

        # 2. Structured financial & PII patterns (PHONE_CM before ACCOUNT so masked phones aren't split)
        rules: list[tuple[re.Pattern[str], str, str]] = [
            (REF_RE, "REF", "REF"),
            (AMOUNT_RE, "AMT", "AMOUNT"),
            (PERCENT_RE, "PCT", "PERCENT"),
            (PHONE_CM_RE, "PHONE", "PHONE_CM"),
            (ACCOUNT_RE, "ACC", "ACCOUNT"),
            (DATE_RE, "DATE", "DATE"),
            (TIME_RE, "TIME", "TIME"),
        ]
        for regex, prefix, etype in rules:
            masked = cls._replace_outside_tokens(
                masked, regex, prefix, etype, entities, entity_types, counters
            )

        # 3. Contextual beneficiary names (runs on full masked string so {{AMT_n}} context matches)
        for ben_re in (BEN_LABEL_RE, BEN_TRANSFER_RE):
            def _sub_ben(match: re.Match[str]) -> str:
                val = match.group(2)
                if "{{" in val or "}}" in val:
                    return match.group(0)
                idx = counters.get("BEN", 0) + 1
                counters["BEN"] = idx
                token_key = f"BEN_{idx}"
                placeholder = f"{{{{{token_key}}}}}"
                entities[placeholder] = val
                entity_types[token_key] = "BENEFICIARY"
                return f"{match.group(1)}{placeholder}"

            masked = ben_re.sub(_sub_ben, masked)

        # 4. Residual standalone numbers (strict zero-digit leak guarantee)
        masked = cls._replace_outside_tokens(
            masked, RESIDUAL_NUM_RE, "NUM", "NUMBER", entities, entity_types, counters
        )

        return ShieldedText(masked_text=masked, entities=entities, entity_types=entity_types)

    @staticmethod
    def unlock(translated_masked: str, entities: dict[str, str]) -> str:
        result = translated_masked
        for placeholder, original in entities.items():
            result = result.replace(placeholder, original)
        return result
