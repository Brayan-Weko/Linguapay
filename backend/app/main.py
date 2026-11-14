"""FastAPI entrypoint for LinguaPay Core API with comprehensive OpenAPI/Swagger documentation."""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from app.api.v1.glossary import glossary_engine, router as glossary_router
from app.api.v1.translate import router as translate_router
from app.api.v1.tts import router as tts_router
from app.config import settings

OPENAPI_DESCRIPTION = """
## 🏛️ Présentation de LinguaPay Core API

**LinguaPay** est la couche d'adaptation linguistique et vocale sécurisée conçue pour le **SAFINUM Innovate Challenge 2026** (Comité National Économique et Financier - CNEF Cameroun).

Elle permet d'adapter instantanément n'importe quel service financier numérique (banque en ligne, microfinance, portefeuille mobile) dans les langues nationales camerounaises (**Ewondo**, **Duala**, **Fulfulde**) **sans modifier une seule ligne du code source hôte**.

---

### 🛡️ Piliers Techniques Clés

1. **Bouclier Financier Déterministe (`EntityShield`)** :
   - Verrouille 100 % des données critiques (montants FCFA, pourcentages de frais, numéros de téléphone +237, noms de bénéficiaires) dans des jetons syntaxiques immuables (`{{AMT_1}}`, `{{BEN_1}}`, etc.).
   - Aucun montant financier n'est exposé à une déformation.

2. **Moteur Hybride à 3 Niveaux & Circuit-Breaker** :
   - **Niveau 1 — Glossaire Certifié Natif** : Résolution locale ultra-rapide (< 5 ms) basée sur les dictionnaires homologués par des locuteurs natifs.
   - **Niveau 2 — Patrons Paramétrés (`TemplateEngine`)** : Compilation déterministe des phrases transactionnelles complexes avec variables liées.
   - **Niveau 3 — IA Contrainte (`AITranslator`)** : Traitement temps réel des messages inédits avec validation d'invariance obligatoire.
   - **Garde-Fou Circuit-Breaker** : Restauration automatique du texte source en cas d'anomalie détectée (chiffre inventé, placeholder manquant, altération de sécurité).

3. **Pont Universel Multi-Langues (`UniversalPivotBridge`)** :
   - Détection automatique de 9 langues sources étrangères (Espagnol, Allemand, Portugais, Italien, Swahili, Arabe, Chinois, Russe, Turc) et pivot vers l'anglais canonique avant adaptation dans les langues camerounaises.

4. **Synthèse Vocale & Verbalisation FCFA (`NumberComposer`)** :
   - Composition grammaticale récursive des nombres de 0 à 999 999 999 FCFA en Ewondo, Duala et Fulfulde.
   - Séquençage audio WebAudio fluide avec capsules PCM 22 050 Hz et fondu croisé (*crossfade*) de 25 ms.

5. **Politique Zero-PII Egress** :
   - Aucune donnée personnelle réelle (PIN, mot de passe, coordonnées réelles) n'est enregistrée dans les journaux d'audit.

---

### 🧪 Guide d'Utilisation Swagger UI

Vous pouvez tester immédiatement chaque route directement depuis cette interface interactive :
- Cliquez sur une route ci-dessous (ex : **`POST /api/v1/translate`**).
- Cliquez sur le bouton **« Try it out »**.
- Le corps de la requête est pré-rempli avec des données réelles de test.
- Cliquez sur **« Execute »** pour visualiser la réponse HTTP 200 en direct.
"""

TAGS_METADATA = [
    {
        "name": "health",
        "description": "Surveillance opérationnelle, état de santé du moteur et découverte dynamique des packs linguistiques installés.",
    },
    {
        "name": "translate",
        "description": "Endpoints d'adaptation linguistique unitaire et par lots (Batch) avec protection EntityShield et Circuit-Breaker.",
    },
    {
        "name": "glossary",
        "description": "Consultation des dictionnaires terminologiques certifiés (avec support ETag) et du journal d'audit Zero-PII en direct.",
    },
    {
        "name": "tts",
        "description": "Moteur vocal hybride : verbalisation des montants en FCFA, calcul de séquences de lecture et capsules audio WAV 22 kHz.",
    },
]

app = FastAPI(
    title="LinguaPay Core API — Documentation Interactive Swagger",
    summary="Couche d'adaptation linguistique et vocale sécurisée pour services financiers camerounais (SAFINUM 2026)",
    description=OPENAPI_DESCRIPTION,
    version="1.0.0",
    openapi_tags=TAGS_METADATA,
    contact={
        "name": "Équipe Projet LinguaPay — SAFINUM Innovate Challenge 2026",
        "url": "https://github.com/placeholder/linguapay",
        "email": "contact@linguapay.cm",
    },
    license_info={
        "name": "Licence MIT — Développé pour le CNEF Cameroun",
        "url": "https://opensource.org/licenses/MIT",
    },
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    swagger_ui_parameters={
        "defaultModelsExpandDepth": 1,
        "docExpansion": "list",
        "filter": True,
        "syntaxHighlight.theme": "monokai",
        "tryItOutEnabled": True,
    },
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Content-Type"],
)

app.include_router(glossary_router)
app.include_router(translate_router)
app.include_router(tts_router)


class LanguageCatalogItem(BaseModel):
    language: str = Field(description="Code normalisé de la langue (ex: ewondo, duala, fulfulde)", examples=["ewondo"])
    display_name: str | None = Field(description="Nom d'usage et région pilote", examples=["Ewondo (Centre / Sud)"])
    iso_639_3: str | None = Field(description="Code ISO 639-3 officiel", examples=["ewo"])
    etag: str = Field(description="Empreinte cryptographique MD5 du dictionnaire", examples=["a1b2c3d4e5f6"])
    entries_count: int = Field(description="Nombre d'entrées lexicales homologuées (Niveau 1)", examples=[15])
    templates_count: int = Field(description="Nombre de patrons transactionnels paramétrés (Niveau 2)", examples=[5])


class HealthResponse(BaseModel):
    status: str = Field(description="Statut global du service", examples=["ok"])
    service: str = Field(description="Nom du microservice", examples=["linguapay-core"])
    version: str = Field(description="Version applicative", examples=["1.0.0"])
    ai_provider: str = Field(description="Fournisseur d'IA actif pour le Niveau 3 (glossary_only, gemini, ollama, auto)", examples=["glossary_only"])
    strict_verifier: bool = Field(description="Activation du Circuit-Breaker strict sur anomalie d'invariance", examples=[True])
    zero_pii_logging: bool = Field(description="Politique Zero-PII garantissant l'absence de données personnelles dans les logs", examples=[True])
    languages: list[LanguageCatalogItem] = Field(description="Catalogue des packs linguistiques disponibles")


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


@app.get(
    "/api/v1/health",
    tags=["health"],
    response_model=HealthResponse,
    summary="État de santé et catalogue des langues nationales",
    description="Vérifie le bon fonctionnement de l'API LinguaPay Core, les paramètres de sécurité (Zero-PII, Circuit-Breaker) et liste dynamiquement les langues camerounaises chargées en mémoire avec leurs versions et empreintes ETag.",
    response_description="Rapport de santé complet et catalogue des packs linguistiques disponibles.",
)
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
