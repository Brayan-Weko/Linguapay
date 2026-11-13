"""AITranslator: Level-3 constrained LLM translation for unseen dynamic content."""

from __future__ import annotations

from collections import OrderedDict
from dataclasses import dataclass
import httpx

from app.config import Settings
from app.core.glossary_engine import GlossaryPack


@dataclass(frozen=True)
class AITranslationResult:
    translated_masked_text: str
    provider: str
    confidence: float
    cached: bool = False


class AITranslator:
    """Constrained Level-3 translator supporting Gemini, local Ollama, and LRU cache."""

    def __init__(self, settings: Settings, cache_size: int = 256) -> None:
        self.settings = settings
        self.cache_size = cache_size
        self._cache: OrderedDict[tuple[str, str], AITranslationResult] = OrderedDict()

    def clear_cache(self) -> None:
        self._cache.clear()

    @staticmethod
    def build_system_prompt(pack: GlossaryPack) -> str:
        examples: list[str] = []
        for entry in pack.raw.get("entries", [])[:8]:
            fr_list = entry.get("fr", [])
            tr = entry.get("translation", "").replace("[À VALIDER NATIF] ", "")
            if fr_list and tr:
                examples.append(f'- "{fr_list[0]}" => "{tr}"')
        neg_list = ", ".join(sorted(pack.negation_markers))
        examples_block = "\n".join(examples)

        return (
            f"You are a precision financial translator into {pack.raw.get('display_name', pack.language)} "
            f"(Cameroonian national language).\n"
            "STRICT RULES:\n"
            "1. Keep EVERY placeholder token like {{AMT_1}}, {{FEE_1}}, {{BEN_1}}, {{PHONE_1}}, "
            "{{DATE_1}}, {{TIME_1}}, {{ACC_1}}, {{REF_1}}, {{PCT_1}}, {{NUM_1}} EXACTLY unchanged.\n"
            "2. NEVER invent, alter, or add any digits/numbers outside placeholders.\n"
            f"3. Preserve negations and security warnings faithfully (negation markers include: {neg_list}).\n"
            "4. Output ONLY the translated sentence, with no quotes, no markdown, and no explanation.\n"
            f"Glossary reference examples:\n{examples_block}"
        )

    def translate(
        self,
        masked_text: str,
        pack: GlossaryPack,
        transport: httpx.BaseTransport | None = None,
    ) -> AITranslationResult | None:
        provider = self.settings.ai_provider.lower().strip()
        if provider == "glossary_only":
            return None

        cache_key = (pack.language, masked_text)
        if cache_key in self._cache:
            self._cache.move_to_end(cache_key)
            hit = self._cache[cache_key]
            return AITranslationResult(
                translated_masked_text=hit.translated_masked_text,
                provider=hit.provider,
                confidence=hit.confidence,
                cached=True,
            )

        system_prompt = self.build_system_prompt(pack)
        result: AITranslationResult | None = None

        if provider == "gemini":
            result = self._call_gemini(masked_text, system_prompt, transport=transport)
        elif provider == "ollama":
            result = self._call_ollama(masked_text, system_prompt, transport=transport)
        elif provider == "auto":
            if self.settings.gemini_api_key:
                result = self._call_gemini(masked_text, system_prompt, transport=transport)
            if result is None:
                result = self._call_ollama(masked_text, system_prompt, transport=transport)

        if result is not None:
            self._cache[cache_key] = result
            if len(self._cache) > self.cache_size:
                self._cache.popitem(last=False)

        return result

    def pivot_to_english(
        self,
        masked_text: str,
        source_lang: str = "auto",
        transport: httpx.BaseTransport | None = None,
    ) -> str | None:
        """Pivots arbitrary non-English/non-French text into canonical English while strictly preserving tokens."""
        provider = self.settings.ai_provider.lower().strip()
        if provider == "glossary_only":
            return None

        cache_key = (f"pivot_en_{source_lang}", masked_text)
        if cache_key in self._cache:
            self._cache.move_to_end(cache_key)
            return self._cache[cache_key].translated_masked_text

        system_prompt = (
            "You are a precision financial translator into English.\n"
            "STRICT RULES:\n"
            "1. Keep EVERY placeholder token like {{AMT_1}}, {{FEE_1}}, {{BEN_1}}, {{PHONE_1}}, "
            "{{DATE_1}}, {{TIME_1}}, {{ACC_1}}, {{REF_1}}, {{PCT_1}}, {{NUM_1}} EXACTLY unchanged.\n"
            "2. NEVER alter, translate, or invent numbers or placeholders.\n"
            "3. Faithfully translate the sentence into clear, concise English.\n"
            "4. Output ONLY the translated sentence, with no quotes, no markdown, and no explanation."
        )

        res: AITranslationResult | None = None
        if provider == "gemini":
            res = self._call_gemini(masked_text, system_prompt, transport=transport)
        elif provider == "ollama":
            res = self._call_ollama(masked_text, system_prompt, transport=transport)
        elif provider == "auto":
            if self.settings.gemini_api_key:
                res = self._call_gemini(masked_text, system_prompt, transport=transport)
            if res is None:
                res = self._call_ollama(masked_text, system_prompt, transport=transport)

        if res is not None:
            self._cache[cache_key] = res
            if len(self._cache) > self.cache_size:
                self._cache.popitem(last=False)
            return res.translated_masked_text
        return None

    def _call_gemini(
        self,
        masked_text: str,
        system_prompt: str,
        transport: httpx.BaseTransport | None = None,
    ) -> AITranslationResult | None:
        if not self.settings.gemini_api_key:
            return None

        url = (
            f"https://generativelanguage.googleapis.com/v1beta/models/"
            f"{self.settings.gemini_model}:generateContent"
        )
        payload = {
            "system_instruction": {"parts": [{"text": system_prompt}]},
            "contents": [{"role": "user", "parts": [{"text": masked_text}]}],
            "generationConfig": {"temperature": 0.1, "maxOutputTokens": 256},
        }
        try:
            with httpx.Client(timeout=self.settings.ai_timeout_seconds, transport=transport) as client:
                resp = client.post(
                    url,
                    params={"key": self.settings.gemini_api_key},
                    json=payload,
                )
                resp.raise_for_status()
                data = resp.json()
            text = (
                data.get("candidates", [{}])[0]
                .get("content", {})
                .get("parts", [{}])[0]
                .get("text", "")
                .strip()
            )
            if not text:
                return None
            return AITranslationResult(
                translated_masked_text=text,
                provider="gemini",
                confidence=0.88,
            )
        except Exception:
            return None

    def _call_ollama(
        self,
        masked_text: str,
        system_prompt: str,
        transport: httpx.BaseTransport | None = None,
    ) -> AITranslationResult | None:
        url = f"{self.settings.ollama_base_url.rstrip('/')}/api/chat"
        payload = {
            "model": self.settings.ollama_model,
            "stream": False,
            "options": {"temperature": 0.1},
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": masked_text},
            ],
        }
        try:
            with httpx.Client(timeout=self.settings.ai_timeout_seconds, transport=transport) as client:
                resp = client.post(url, json=payload)
                resp.raise_for_status()
                data = resp.json()
            text = data.get("message", {}).get("content", "").strip()
            if not text:
                return None
            return AITranslationResult(
                translated_masked_text=text,
                provider="ollama",
                confidence=0.84,
            )
        except Exception:
            return None
