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
    id: str = Field(
        default_factory=lambda: f"seg_{uuid.uuid4().hex[:8]}",
        description="Identifiant unique du segment de texte (DOM element ID)",
        examples=["seg_8f1a2c3d"],
    )
    masked_text: str | None = Field(
        default=None,
        description="Texte avec placeholders EntityShield déjà verrouillés côté client (ex: {{AMT_1}})",
        examples=["Moni woe a ne tebe : {{AMT_1}}"],
    )
    text: str | None = Field(
        default=None,
        description="Texte brut non masqué (le bouclier EntityShield s'exécutera automatiquement côté serveur)",
        examples=["Solde disponible : 145 750 FCFA"],
    )
    entity_types: dict[str, str] = Field(
        default_factory=dict,
        description="Dictionnaire des métadonnées de types d'entités verrouillées",
        examples=[{"{{AMT_1}}": "AMOUNT_FCFA"}],
    )
    criticality: str = Field(
        default="UI_NAV",
        description="Niveau de criticité financière du segment (FINANCIAL_CORE, L1_CRITICAL_SECURITY, L2_TRANSACTION_CORE, UI_NAV)",
        examples=["FINANCIAL_CORE"],
    )

    @model_validator(mode="after")
    def ensure_text_present(self) -> "TranslateItemRequest":
        if not self.masked_text and not self.text:
            raise ValueError("Either 'masked_text' or 'text' must be provided.")
        return self


class TranslateBatchRequest(BaseModel):
    target_lang: str = Field(
        description="Langue nationale camerounaise cible (ewondo, duala, fulfulde)",
        examples=["ewondo"],
    )
    source_lang: str = Field(
        default="auto",
        description="Langue source du texte bancaire (auto, fr, en, es, de, pt, it, zh, ar, etc.)",
        examples=["auto"],
    )
    items: list[TranslateItemRequest] = Field(
        min_length=1,
        max_length=200,
        description="Liste ordonnée des segments textuels à adapter (maximum 200 par lot)",
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "target_lang": "ewondo",
                    "source_lang": "auto",
                    "items": [
                        {
                            "id": "seg_solde",
                            "text": "Solde disponible : 145 750 FCFA",
                            "criticality": "FINANCIAL_CORE",
                        },
                        {
                            "id": "seg_frais",
                            "text": "Frais de transfert : 1 500 FCFA",
                            "criticality": "FINANCIAL_CORE",
                        },
                        {
                            "id": "seg_alerte",
                            "text": "Attention : ne communiquez jamais votre code PIN.",
                            "criticality": "L1_CRITICAL_SECURITY",
                        },
                    ],
                }
            ]
        }
    }


class TranslateItemResponse(BaseModel):
    id: str = Field(description="Identifiant du segment traité", examples=["seg_solde"])
    translated_masked_text: str = Field(
        description="Texte adapté dans la langue nationale avec placeholders de variables préservés",
        examples=["[À VALIDER NATIF] Moni woe a ne tebe : {{AMT_1}}"],
    )
    unlocked_text: str | None = Field(
        default=None,
        description="Texte final réinjecté avec les montants et données financières réinsérées sans la moindre altération",
        examples=["[À VALIDER NATIF] Moni woe a ne tebe : 145 750 FCFA"],
    )
    tier_used: str = Field(
        description="Moteur de résolution employé (GLOSSARY_L1, TEMPLATE_L2, AI_CONSTRAINED_L3, PIVOT_GLOSSARY_L1, PIVOT_TEMPLATE_L2, CIRCUIT_BREAKER_FALLBACK)",
        examples=["TEMPLATE_L2"],
    )
    confidence: float = Field(description="Indice de confiance de la traduction (0.0 à 1.0)", examples=[1.0])
    integrity_passed: bool = Field(description="Indique si le contrôle mathématique d'invariance et de sécurité est validé", examples=[True])
    verification_reason: str = Field(description="Détail du verdict du vérificateur d'intégrité", examples=["OK_IDENTICAL_TOKENS_AND_INTEGRITY"])
    fallback_triggered: bool = Field(description="Vrai si le Circuit-Breaker a restauré le texte d'origine suite à une anomalie", examples=[False])
    audio_clip: str | None = Field(default=None, description="Lien relatif vers la capsule audio pré-enregistrée le cas échéant", examples=["audio/ewondo/fin_bal_001.ogg"])


class TranslateBatchResponse(BaseModel):
    request_id: str = Field(description="Identifiant unique de la transaction de lot", examples=["req_b3a7f8e12d"])
    target_lang: str = Field(description="Langue nationale cible", examples=["ewondo"])
    results: list[TranslateItemResponse] = Field(description="Résultats d'adaptation pour chacun des segments du lot")


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


class SingleTranslateRequest(BaseModel):
    target_lang: str = Field(
        description="Langue nationale cible (ewondo, duala, fulfulde)",
        examples=["ewondo"],
    )
    source_lang: str = Field(
        default="auto",
        description="Langue source (auto, fr, en, es, de, pt, it, zh, ar, etc.)",
        examples=["auto"],
    )
    masked_text: str | None = Field(
        default=None,
        description="Texte avec variables pré-masquées par EntityShield (optionnel si 'text' est fourni)",
        examples=["Moni woe a ne tebe : {{AMT_1}}"],
    )
    text: str | None = Field(
        default=None,
        description="Texte brut bancaire à sécuriser et traduire",
        examples=["Solde disponible : 145 750 FCFA"],
    )
    entity_types: dict[str, str] = Field(
        default_factory=dict,
        description="Types des entités financières masquées",
        examples=[{"{{AMT_1}}": "AMOUNT_FCFA"}],
    )
    criticality: str = Field(
        default="FINANCIAL_CORE",
        description="Niveau de criticité financière (FINANCIAL_CORE, L1_CRITICAL_SECURITY, L2_TRANSACTION_CORE, UI_NAV)",
        examples=["FINANCIAL_CORE"],
    )

    @model_validator(mode="after")
    def ensure_text_present(self) -> "SingleTranslateRequest":
        if not self.masked_text and not self.text:
            raise ValueError("Either 'masked_text' or 'text' must be provided.")
        return self

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "target_lang": "ewondo",
                    "source_lang": "auto",
                    "text": "Solde disponible : 145 750 FCFA",
                    "criticality": "FINANCIAL_CORE",
                },
                {
                    "target_lang": "duala",
                    "source_lang": "es",
                    "text": "Saldo disponible : 50 000 FCFA",
                    "criticality": "FINANCIAL_CORE",
                },
                {
                    "target_lang": "fulfulde",
                    "source_lang": "fr",
                    "text": "Vous allez transférer 50 000 FCFA à Jean-Paul Mballa (+237 699 45 12 88). Frais : 1 500 FCFA. Total à débiter : 51 500 FCFA.",
                    "criticality": "FINANCIAL_CORE",
                },
            ]
        }
    }


@router.post(
    "/translate",
    response_model=TranslateItemResponse,
    summary="Traduction unitaire sécurisée avec EntityShield & Circuit-Breaker",
    description="Adapte une phrase financière dans la langue nationale choisie (Ewondo, Duala, Fulfulde). "
    "Exécute le bouclier déterministe EntityShield, pivote si nécessaire via UniversalPivotBridge, "
    "résout via le Glossaire L1, les Patrons L2 ou l'IA contrainte L3, puis vérifie la bijection mathématique stricte.",
    response_description="Résultat d'adaptation contenant le texte masqué, le texte réinjecté sans altération et les métadonnées de vérification.",
)
def translate_single(payload: SingleTranslateRequest) -> TranslateItemResponse:
    request_id = f"req_{uuid.uuid4().hex[:10]}"
    item = TranslateItemRequest(
        masked_text=payload.masked_text,
        text=payload.text,
        entity_types=payload.entity_types,
        criticality=payload.criticality,
    )
    return _translate_single(item, payload.target_lang.lower(), request_id, source_lang=payload.source_lang)


@router.post(
    "/translate/batch",
    response_model=TranslateBatchResponse,
    summary="Traduction groupée sécurisée par lots (Batch DOM)",
    description="Permet à l'extension navigateur ou au client API d'adapter simultanément jusqu'à 200 segments DOM en une seule requête HTTP.",
    response_description="Ensemble ordonné des segments adaptés avec statuts de vérification d'intégrité individuels.",
)
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
