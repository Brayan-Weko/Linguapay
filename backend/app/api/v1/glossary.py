"""Routes /glossary/{lang} and runtime engine registry."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Response

from app.config import settings
from app.core.audit_logger import AuditLogger
from app.core.glossary_engine import GlossaryEngine
from app.core.template_engine import TemplateEngine

router = APIRouter(prefix="/api/v1", tags=["glossary"])

glossary_engine = GlossaryEngine(settings.linguistics_dir / "packs")
template_engine = TemplateEngine(glossary_engine)
audit_logger = AuditLogger(maxlen=250)


@router.get("/glossary/{lang}")
def get_glossary(lang: str, response: Response) -> dict:
    pack = glossary_engine.get_pack(lang)
    if pack is None:
        raise HTTPException(
            status_code=404,
            detail=f"Language pack '{lang}' not found. Available: {glossary_engine.available_languages()}",
        )
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


@router.get("/audit/recent")
def get_recent_audit(limit: int = 50) -> dict:
    safe_limit = max(1, min(limit, 200))
    return {"records": audit_logger.recent(limit=safe_limit)}
