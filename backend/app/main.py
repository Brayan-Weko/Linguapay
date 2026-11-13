"""FastAPI entrypoint for LinguaPay Core API."""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.glossary import glossary_engine, router as glossary_router
from app.api.v1.translate import router as translate_router
from app.api.v1.tts import router as tts_router
from app.config import settings

app = FastAPI(
    title="LinguaPay Core API",
    description="Couche d'adaptation linguistique sécurisée pour l'inclusion financière au Cameroun (SAFINUM 2026).",
    version="0.2.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Restreint en production / extension ID en Sprint 5
    allow_credentials=False,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Content-Type"],
)

app.include_router(glossary_router)
app.include_router(translate_router)
app.include_router(tts_router)


def _discover_languages() -> list[dict]:
    languages: list[dict] = []
    for lang in glossary_engine.available_languages():
        pack = glossary_engine.get_pack(lang)
        if pack is None:
            continue
        languages.append(
            {
                "language": pack.language,
                "display_name": pack.raw.get("display_name"),
                "iso_639_3": pack.raw.get("iso_639_3"),
                "etag": pack.etag,
                "entries_count": len(pack.raw.get("entries", [])),
                "templates_count": len(pack.raw.get("templates", [])),
            }
        )
    return languages


@app.get("/api/v1/health")
def health() -> dict:
    return {
        "status": "ok",
        "service": "linguapay-core",
        "version": app.version,
        "ai_provider": settings.ai_provider,
        "strict_verifier": settings.strict_verifier,
        "zero_pii_logging": not settings.log_pii,
        "languages": _discover_languages(),
    }
