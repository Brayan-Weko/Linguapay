"""TemplateEngine: Level-2 structural pattern matching with token binding."""

from __future__ import annotations

import re
from dataclasses import dataclass

from app.core.glossary_engine import GlossaryEngine, GlossaryPack

_PLACEHOLDER_RE = re.compile(r"\{\{([A-Z]+_\d+)\}\}")


@dataclass(frozen=True)
class TemplateMatch:
    template_id: str
    translated_masked_text: str
    criticality: str
    confidence: float


class _CompiledTemplate:
    def __init__(
        self,
        template_id: str,
        criticality: str,
        target_template: str,
        patterns: list[tuple[re.Pattern[str], list[str]]],
    ) -> None:
        self.template_id = template_id
        self.criticality = criticality
        self.target_template = target_template
        self.patterns = patterns

    def try_match(self, masked_text: str) -> TemplateMatch | None:
        normalized_input = re.sub(r"\s+", " ", masked_text.strip())
        for regex, slot_names in self.patterns:
            m = regex.fullmatch(normalized_input)
            if not m:
                continue
            rendered = self.target_template
            # Bind each matched slot token (e.g. {{AMT_2}}) into the template's slot
            # Use two-stage temporary markers to avoid cross-replacement collisions
            temp_map: dict[str, str] = {}
            for idx, slot_name in enumerate(slot_names, start=1):
                captured_token = m.group(idx)
                marker = f"__LP_SLOT_{idx}__"
                rendered = rendered.replace(f"{{{{{slot_name}}}}}", marker, 1)
                temp_map[marker] = captured_token
            for marker, captured_token in temp_map.items():
                rendered = rendered.replace(marker, captured_token)
            return TemplateMatch(
                template_id=self.template_id,
                translated_masked_text=rendered,
                criticality=self.criticality,
                confidence=1.0,
            )
        return None


def _compile_pattern(pattern_str: str) -> tuple[re.Pattern[str], list[str]]:
    """Turn 'Solde disponible : {{AMT_1}}' into a regex capturing any {{TOKEN_N}}."""
    slot_names: list[str] = []
    parts = _PLACEHOLDER_RE.split(pattern_str.strip())
    regex_chunks: list[str] = []
    for i, part in enumerate(parts):
        if i % 2 == 1:
            slot_names.append(part)
            regex_chunks.append(r"(\{\{[A-Z]+_\d+\}\})")
        else:
            escaped = re.escape(part)
            # Allow flexible whitespace around punctuation
            escaped = re.sub(r"(?:\\ )+", r"\\s+", escaped)
            regex_chunks.append(escaped)
    full_regex = re.compile("".join(regex_chunks), re.IGNORECASE)
    return full_regex, slot_names


class TemplateEngine:
    """Matches parameterized transactional sentences and label+token hybrids."""

    def __init__(self, glossary_engine: GlossaryEngine) -> None:
        self.glossary_engine = glossary_engine
        self._compiled: dict[str, list[_CompiledTemplate]] = {}
        self.reload()

    def reload(self) -> None:
        self._compiled.clear()
        for lang in self.glossary_engine.available_languages():
            pack = self.glossary_engine.get_pack(lang)
            if pack is None:
                continue
            self._compiled[lang] = self._build_for_pack(pack)

    @staticmethod
    def _build_for_pack(pack: GlossaryPack) -> list[_CompiledTemplate]:
        compiled: list[_CompiledTemplate] = []
        for tpl in pack.raw.get("templates", []):
            patterns: list[tuple[re.Pattern[str], list[str]]] = []
            for key in ("fr_pattern", "en_pattern"):
                pat = tpl.get(key)
                if pat:
                    patterns.append(_compile_pattern(pat))
            compiled.append(
                _CompiledTemplate(
                    template_id=tpl["id"],
                    criticality=tpl["criticality"],
                    target_template=tpl["target_template"],
                    patterns=patterns,
                )
            )
        return compiled

    def match(self, masked_text: str, lang: str) -> TemplateMatch | None:
        lang_key = lang.lower()
        for tpl in self._compiled.get(lang_key, []):
            res = tpl.try_match(masked_text)
            if res is not None:
                return res

        # Fallback structural pattern: "<GlossaryLabel> : {{TOKEN_1}}" or "<GlossaryLabel> ({{TOKEN_1}})"
        colon_match = re.fullmatch(r"\s*(.+?)\s*:\s*(\{\{[A-Z]+_\d+\}\})\s*", masked_text)
        if colon_match:
            label_part, token_part = colon_match.group(1), colon_match.group(2)
            g = self.glossary_engine.match(label_part, lang_key)
            if g is not None:
                return TemplateMatch(
                    template_id=f"STRUCT_COLON_{g.entry_id}",
                    translated_masked_text=f"{g.translation} : {token_part}",
                    criticality=g.criticality,
                    confidence=g.confidence,
                )

        paren_match = re.fullmatch(r"\s*(.+?)\s*\(\s*(\{\{[A-Z]+_\d+\}\})\s*\)\s*", masked_text)
        if paren_match:
            label_part, token_part = paren_match.group(1), paren_match.group(2)
            g = self.glossary_engine.match(label_part, lang_key)
            if g is not None:
                return TemplateMatch(
                    template_id=f"STRUCT_PAREN_{g.entry_id}",
                    translated_masked_text=f"{g.translation} ({token_part})",
                    criticality=g.criticality,
                    confidence=g.confidence,
                )

        return None
