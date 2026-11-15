"""Routes /glossary/{lang} and /audit/recent with comprehensive OpenAPI documentation."""

from __future__ import annotations

from typing import Any
from fastapi import APIRouter, HTTPException, Path, Query, Response
from pydantic import BaseModel, Field

from app.config import settings
from app.core.audit_logger import AuditLogger
from app.core.glossary_engine import GlossaryEngine
from app.core.template_engine import TemplateEngine

router = APIRouter(prefix="/api/v1", tags=["glossary"])

glossary_engine = GlossaryEngine(settings.linguistics_dir / "packs")
template_engine = TemplateEngine(glossary_engine)
audit_logger = AuditLogger(maxlen=250)


class GlossaryEntryItem(BaseModel):
    id: str = Field(description="Identifiant canonique du terme", examples=["FIN_BAL_001"])
    criticality: str = Field(description="Niveau de criticité", examples=["L2_TRANSACTION_CORE"])
    fr: list[str] = Field(description="Variantes en français", examples=[["Solde disponible", "Votre solde disponible"]])
    en: list[str] = Field(description="Variantes en anglais", examples=[["Available balance", "Your available balance"]])
    translation: str = Field(description="Traduction dans la langue nationale", examples=["[À VALIDER NATIF] Moni woe a ne tebe"])
    back_translation_fr: str = Field(description="Rétro-traduction aveugle de contrôle", examples=["L'argent disponible dans ton compte"])
    audio_clip: str | None = Field(default=None, description="Référence audio le cas échéant", examples=["audio/ewondo/fin_bal_001.ogg"])
    validation_status: str = Field(description="Statut du protocole de validation", examples=["PENDING_NATIVE_REVIEW"])


class GlossaryTemplateItem(BaseModel):
    id: str = Field(description="Identifiant du patron", examples=["TPL_BAL_001"])
    criticality: str = Field(description="Niveau de criticité", examples=["L2_TRANSACTION_CORE"])
    fr_pattern: str = Field(description="Motif source FR", examples=["Solde disponible : {{AMT_1}}"])
    en_pattern: str = Field(description="Motif source EN", examples=["Available balance: {{AMT_1}}"])
    target_template: str = Field(description="Patron cible avec jetons liés", examples=["[À VALIDER NATIF] Moni woe a ne tebe : {{AMT_1}}"])
    required_tokens: list[str] = Field(description="Jetons strictement obligatoires", examples=[["{{AMT_1}}"]])
    validation_status: str = Field(description="Statut d'homologation", examples=["PENDING_NATIVE_REVIEW"])


class GlossaryPackResponse(BaseModel):
    language: str = Field(description="Code normalisé de la langue", examples=["ewondo"])
    display_name: str | None = Field(description="Nom complet et zone géographique", examples=["Ewondo (Centre / Sud)"])
    iso_639_3: str | None = Field(description="Code ISO 639-3", examples=["ewo"])
    version: str | None = Field(description="Version du pack", examples=["0.2.0"])
    etag: str = Field(description="Empreinte cryptographique MD5 du dictionnaire", examples=["c8a4b2e91f07"])
    negation_markers: list[str] = Field(description="Marqueurs de négation grammaticale pour le Circuit-Breaker", examples=[["te", "tege", "aa", "kokoa", "abé"]])
    entries: list[dict[str, Any]] = Field(description="Liste des entrées lexicales Niveau 1")
    templates: list[dict[str, Any]] = Field(description="Liste des patrons transactionnels Niveau 2")
    number_rules: dict[str, Any] = Field(description="Règles de verbalisation grammaticale des nombres FCFA")


class AuditRecordItem(BaseModel):
    timestamp: str = Field(description="Horodatage ISO UTC de l'événement", examples=["2026-11-14T07:25:00.123456+00:00"])
    request_id: str = Field(description="Identifiant de transaction unique", examples=["req_a1b2c3d4e5"])
    segment_id: str = Field(description="Identifiant du segment DOM", examples=["seg_solde"])
    target_lang: str = Field(description="Langue nationale cible", examples=["ewondo"])
    tier_used: str = Field(description="Moteur de résolution utilisé (GLOSSARY_L1, TEMPLATE_L2, AI_CONSTRAINED_L3, etc.)", examples=["TEMPLATE_L2"])
    masked_sha256: str = Field(description="Empreinte SHA-256 tronquée du texte masqué (Zéro-PII)", examples=["380ab3903aed"])
    token_count: int = Field(description="Nombre d'entités financières protégées", examples=[1])
    integrity_passed: bool = Field(description="Indique si le contrôle mathématique d'intégrité a été validé", examples=[True])
    verification_reason: str = Field(description="Motif détaillé du verdict de sécurité", examples=["OK"])
    fallback_triggered: bool = Field(description="Indique si le Circuit-Breaker s'est activé", examples=[False])
    latency_ms: float = Field(description="Durée de traitement en millisecondes", examples=[0.29])


class AuditRecentResponse(BaseModel):
    records: list[AuditRecordItem] = Field(description="Historique des dernières adaptations réalisées")


@router.get(
    "/glossary/{lang}",
    response_model=GlossaryPackResponse,
    summary="Consultation du pack linguistique certifié (avec en-tête ETag)",
    description="Renvoie l'ensemble du dictionnaire linguistique pour une langue nationale camerounaise donnée "
    "(Ewondo, Duala, Fulfulde). Inclut les entrées de Niveau 1, les patrons de Niveau 2, les marqueurs de négation "
    "et les tables lexicales pour la verbalisation des montants en FCFA. L'en-tête HTTP 'ETag' permet un cache navigateur optimal.",
    response_description="Pack linguistique complet avec règles de verbalisation et patrons paramétrés.",
)
def get_glossary(
    lang: str = Path(
        description="Code de la langue à consulter (ewondo, duala, fulfulde)",
        examples=["ewondo"],
    ),
    response: Response = None,
) -> dict:
    pack = glossary_engine.get_pack(lang.lower().strip())
    if pack is None:
        raise HTTPException(
            status_code=404,
            detail=f"Language pack '{lang}' not found. Available: {glossary_engine.available_languages()}",
        )
    if response is not None:
        response.headers["ETag"] = f'"{pack.etag}"'
    return {
        "language": pack.language,
        "display_name": pack.raw.get("display_name"),
        "iso_639_3": pack.raw.get("iso_639_3"),
        "version": pack.raw.get("version"),
        "etag": pack.etag,
        "negation_markers": pack.raw.get("negation_markers", []),
        "entries": pack.raw.get("entries", []),
        "templates": pack.raw.get("templates", []),
        "number_rules": pack.raw.get("number_rules", {}),
    }


@router.get(
    "/audit/recent",
    response_model=AuditRecentResponse,
    summary="Journal d'audit en temps réel (100% anonymisé Zero-PII)",
    description="Permet aux auditeurs de sécurité de vérifier en direct "
    "que le bouclier fonctionne correctement. "
    "Seuls les squelettes syntaxiques masqués ({{AMT_1}}, {{BEN_1}}) sont consignés, sans aucune donnée personnelle réelle.",
    response_description="Dernières transactions d'adaptation enregistrées en mémoire vive.",
)
def get_recent_audit(
    limit: int = Query(
        default=50,
        ge=1,
        le=200,
        description="Nombre maximum d'enregistrements d'audit à renvoyer (entre 1 et 200)",
        examples=[50],
    ),
) -> dict:
    safe_limit = max(1, min(limit, 200))
    return {"records": audit_logger.recent(limit=safe_limit)}
