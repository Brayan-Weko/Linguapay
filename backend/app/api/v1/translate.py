"""Routes /translate and /translate/batch implementing the 3-tier shield pipeline."""

from __future__ import annotations

import time
import uuid
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field, model_validator

from app.api.v1.glossary import audit_logger, glossary_engine, template_engine
from app.config import settings
from app.core.ai_translator import AITranslator
from app.core.entity_shield import EntityShield
from app.core.integrity_verifier import IntegrityVerifier, VerificationResult
from app.core.pivot_bridge import UniversalPivotBridge

router = APIRouter(prefix="/api/v1", tags=["translate"])
ai_translator = AITranslator(settings=settings)


class TranslateItemRequest(BaseModel):
    id: str = Field(default_factory=lambda: f"seg_{uuid.uuid4().hex[:8]}")
    masked_text: str | None = None
    text: str | None = None
    entity_types: dict[str, str] = Field(default_factory=dict)
    criticality: str = "UI_NAV"

    @model_validator(mode="after")
    def ensure_text_present(self) -> "TranslateItemRequest":
        if not self.masked_text and not self.text:
            raise ValueError("Either 'masked_text' or 'text' must be provided.")
        return self


class TranslateBatchRequest(BaseModel):
    target_lang: str
    source_lang: str = "auto"
    items: list[TranslateItemRequest] = Field(min_length=1, max_length=200)


class TranslateItemResponse(BaseModel):
    id: str
    translated_masked_text: str
    unlocked_text: str | None = None
    tier_used: str
    confidence: float
    integrity_passed: bool
    verification_reason: str
    fallback_triggered: bool
    audio_clip: str | None = None


class TranslateBatchResponse(BaseModel):
    request_id: str
    target_lang: str
    results: list[TranslateItemResponse]


def _translate_single(
    item: TranslateItemRequest,
    target_lang: str,
    request_id: str,
    source_lang: str = "auto",
) -> TranslateItemResponse:
    t0 = time.perf_counter()
    pack = glossary_engine.get_pack(target_lang)
    if pack is None:
        raise HTTPException(status_code=404, detail=f"Unsupported target language '{target_lang}'")

    server_entities: dict[str, str] = {}
    if item.masked_text is not None:
        # Defense-in-depth: mask any stray digits/PII accidentally left unmasked
        shielded = EntityShield.lock(item.masked_text)
        working_masked = shielded.masked_text
        server_entities = shielded.entities
    else:
        shielded = EntityShield.lock(item.text or "")
        working_masked = shielded.masked_text
        server_entities = shielded.entities

    # Universal Language Pivot Bridge: pivot non-FR/non-EN sites to English canonical form
    pivot_res = UniversalPivotBridge.pivot_to_english(working_masked, source_lang, ai_translator=ai_translator)
    query_masked = pivot_res.pivoted_text if pivot_res.pivoted else working_masked

    tier_used = "FALLBACK_ORIGINAL"
    candidate = working_masked
    confidence = 0.0
    audio_clip: str | None = None
    effective_criticality = item.criticality

    # Level 1: Certified/Validated Glossary (try original query, then pivoted query)
    g_match = glossary_engine.match(working_masked, target_lang)
    if g_match is None and pivot_res.pivoted:
        g_match = glossary_engine.match(query_masked, target_lang)

    if g_match is not None:
        tier_used = "GLOSSARY_L1" if not pivot_res.pivoted else "PIVOT_GLOSSARY_L1"
        candidate = g_match.translation
        confidence = g_match.confidence
        audio_clip = g_match.audio_clip
        if effective_criticality == "UI_NAV":
            effective_criticality = g_match.criticality
    else:
        # Level 2: Parameterized Template & Structural Label+Token Match
        t_match = template_engine.match(working_masked, target_lang)
        if t_match is None and pivot_res.pivoted:
            t_match = template_engine.match(query_masked, target_lang)

        if t_match is not None:
            tier_used = "TEMPLATE_L2" if not pivot_res.pivoted else "PIVOT_TEMPLATE_L2"
            candidate = t_match.translated_masked_text
            confidence = t_match.confidence
            if effective_criticality == "UI_NAV":
                effective_criticality = t_match.criticality
        else:
            # Level 3: Constrained AI Adaptation for unseen dynamic content
            ai_res = ai_translator.translate(query_masked, pack)
            if ai_res is not None:
                tier_used = "AI_CONSTRAINED_L3"
                candidate = ai_res.translated_masked_text
                confidence = ai_res.confidence
                if effective_criticality == "UI_NAV":
                    effective_criticality = "UNSEEN_DYNAMIC"

    # Integrity Verification & Circuit-Breaker
    fallback_triggered = False
    if tier_used == "FALLBACK_ORIGINAL":
        v_res = VerificationResult(True, "NO_MATCH_KEPT_ORIGINAL")
        fallback_triggered = True
    else:
        v_res = IntegrityVerifier.verify(
            source_masked=working_masked,
            target_masked=candidate,
            lang=target_lang,
            criticality=effective_criticality,
            target_negation_markers=pack.negation_markers,
        )
        if not v_res.passed and settings.strict_verifier:
            candidate = working_masked
            tier_used = "CIRCUIT_BREAKER_FALLBACK"
            confidence = 0.0
            fallback_triggered = True

    unlocked_text = (
        EntityShield.unlock(candidate, server_entities)
        if item.text is not None or server_entities
        else None
    )

    latency_ms = (time.perf_counter() - t0) * 1000.0
    token_count = len(item.entity_types) + len(server_entities)
    audit_logger.record(
        request_id=request_id,
        segment_id=item.id,
        target_lang=target_lang,
        tier_used=tier_used,
        masked_text=working_masked,
        token_count=token_count,
        integrity_passed=v_res.passed,
        verification_reason=v_res.reason,
        fallback_triggered=fallback_triggered,
        latency_ms=latency_ms,
    )

    return TranslateItemResponse(
        id=item.id,
        translated_masked_text=candidate,
        unlocked_text=unlocked_text,
        tier_used=tier_used,
        confidence=confidence,
        integrity_passed=v_res.passed,
        verification_reason=v_res.reason,
        fallback_triggered=fallback_triggered,
        audio_clip=audio_clip,
    )


@router.post("/translate/batch", response_model=TranslateBatchResponse)
def translate_batch(payload: TranslateBatchRequest) -> TranslateBatchResponse:
    request_id = f"req_{uuid.uuid4().hex[:10]}"
    results = [
        _translate_single(item, payload.target_lang.lower(), request_id, source_lang=payload.source_lang)
        for item in payload.items
    ]
    return TranslateBatchResponse(
        request_id=request_id,
        target_lang=payload.target_lang.lower(),
        results=results,
    )


class SingleTranslateRequest(BaseModel):
    target_lang: str
    source_lang: str = "auto"
    masked_text: str | None = None
    text: str | None = None
    entity_types: dict[str, str] = Field(default_factory=dict)
    criticality: str = "UI_NAV"

    @model_validator(mode="after")
    def ensure_text_present(self) -> "SingleTranslateRequest":
        if not self.masked_text and not self.text:
            raise ValueError("Either 'masked_text' or 'text' must be provided.")
        return self


@router.post("/translate", response_model=TranslateItemResponse)
def translate_single(payload: SingleTranslateRequest) -> TranslateItemResponse:
    request_id = f"req_{uuid.uuid4().hex[:10]}"
    item = TranslateItemRequest(
        masked_text=payload.masked_text,
        text=payload.text,
        entity_types=payload.entity_types,
        criticality=payload.criticality,
    )
    return _translate_single(item, payload.target_lang.lower(), request_id, source_lang=payload.source_lang)
