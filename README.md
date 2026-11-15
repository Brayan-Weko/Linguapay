# LinguaPay — Couche d'Adaptation Linguistique Sécurisée & Vocale pour l'Inclusion Financière

> **LinguaPay Assistant** — Couche Universelle d'Adaptation Linguistique et Vocale pour Services Financiers
> *Inclusion financière par l'adaptation native en langues camerounaises (Ewondo, Duala, Fulfulde)*

[![Backend CI & Security](https://github.com/placeholder/linguapay/actions/workflows/ci-backend.yml/badge.svg)](https://github.com/placeholder/linguapay/actions)
[![Extension CI & Build](https://github.com/placeholder/linguapay/actions/workflows/ci-extension.yml/badge.svg)](https://github.com/placeholder/linguapay/actions)
[![Security & Audits](https://github.com/placeholder/linguapay/actions/workflows/ci-security.yml/badge.svg)](https://github.com/placeholder/linguapay/actions)
[![E2E Integration](https://github.com/placeholder/linguapay/actions/workflows/ci-e2e.yml/badge.svg)](https://github.com/placeholder/linguapay/actions)

---

## 1. Contexte & Problématique Résolue

L'utilisation des services financiers numériques (banque mobile, portefeuilles électroniques, microfinance) constitue un levier majeur d'inclusion financière au Cameroun. Cependant, la quasi-totalité des interfaces bancaires est proposée exclusivement en français ou en anglais, avec un vocabulaire technique souvent hermétique (*solde disponible, frais de commission, bénéficiaire, code PIN à usage unique, plafond journalier*).

Pour des millions d'utilisateurs maîtrisant peu ces langues administratives écrites, cette situation crée une barrière critique d'accès, un risque accru d'erreurs de transfert et une vulnérabilité aux fraudes.

**LinguaPay** résout ce défi par une **couche d'adaptation universelle non-intrusive** qui :

1. **S'adapte à n'importe quel service financier web existant sans modifier son code source** (Zéro-Intrusion côté serveur).
2. **Garantit l'intégrité absolue des montants, frais, bénéficiaires et alertes de sécurité** via son bouclier déterministe `EntityShield` et son `IntegrityVerifier` (Circuit-Breaker).
3. **Fonctionne pour tous les sites quelle que soit la langue source** via un **pont universel de pivot vers l'anglais** (`UniversalPivotBridge`) avant d'adapter vers les langues nationales camerounaises (**Ewondo**, **Duala**, **Fulfulde**).
4. **Offre une assistance vocale native complète** avec verbalisation grammaticale des montants en FCFA (`NumberComposer`) et lecture audio séquentielle WebAudio.
5. **Gère en temps réel le contenu inédit injecté en direct** via `MutationObserver` et un moteur d'IA contraint à faible latence (&lt; 1,2 s).

---

## 2. Grille d'Excellence & Critères d'Évaluation (100 Points)

| Critère d'évaluation                           |      Poids      | Exigence Réglementaire                                                                | Réponse & Implémentation LinguaPay                                                                          |
| :----------------------------------------------- | :--------------: | :------------------------------------------------------------------------------------- | :------------------------------------------------------------------------------------------------------------ |
| **Fonctionnement du prototype**            | **25 pts** | Parcours complet simulé (solde, frais, transfert, récapitulatif, alerte).            | Extension MV3 opérationnelle + Simulateur `SimuBank CM` validant les 5 étapes pas-à-pas.                 |
| **Intégration & indépendance**           | **20 pts** | Zéro modification du code source cible ; réutilisable sur l'environnement jury.      | Injection DOM pure (Content Script + Shadow DOM isolé), aucun appel ou modification du serveur hôte.        |
| **Sécurité & préservation financière** | **20 pts** | Exactitude absolue des montants, frais, téléphones, conditions et alertes PIN.       | Bouclier déterministe `EntityShield` + `IntegrityVerifier` + Zéro fuite de PII (*Zero-PII Egress*).   |
| **Accessibilité & UX**                    | **15 pts** | Solution adaptée aux populations ayant des difficultés d'accès au numérique.       | Double affichage bilingue (infobulle FR/EN), fort contraste, police +20% et **lecture vocale audio**.   |
| **Adaptation à un contenu inédit**       | **10 pts** | Traiter en direct un nouveau message introduit par le jury durant la démonstration.   | `MutationObserver` temps réel (debounce 80 ms) + IA contrainte par glossaire + vérification d'invariance. |
| **Faisabilité technique & documentation** | **10 pts** | Architecture claire, dépendances déclarées, méthode linguistique, limites connues. | Monorepo documenté, Docker reproductible, CI/CD GitHub Actions, protocole linguistique en 4 phases.          |

---

## 3. Architecture Technique

```
┌────────────────────────────────────────────────────────────────────────┐
│                   NAVIGATEUR CLIENT (Chrome / Edge MV3)                 │
│                                                                        │
│   ┌───────────────────────────┐      ┌─────────────────────────────┐   │
│   │  Service Financier Cible  │      │    Content Script MV3       │   │
│   │    (DOM NON MODIFIÉ)      │ ───> │  - DOMWalker (filtre secret)│   │
│   │   SimuBank / Plateforme   │ <─── │  - MutationObserver (80ms)  │   │
│   │  FR / EN / ES / DE ...    │      │  - EntityShield (masquage)  │   │
│   └───────────────────────────┘      └──────────────┬──────────────┘   │
│                                                     │                  │
│                                      ┌──────────────┴──────────────┐   │
│                                      │   Background Service Worker │   │
│                                      │ (contourne CSP cible via MV3│   │
│                                      └──────────────┬──────────────┘   │
└─────────────────────────────────────────────────────┼──────────────────┘
                                                      │ JSON (Zéro-PII)
                                                      ▼
┌────────────────────────────────────────────────────────────────────────┐
│              LINGUAPAY CORE API (Python 3.13 / FastAPI)                │
│                                                                        │
│   ┌────────────────────────────────────────────────────────────────┐   │
│   │                 Universal Language Pivot Bridge                │   │
│   │    Détection source -> Pivot Anglais Universel si étranger     │   │
│   └────────────────────────────────┬───────────────────────────────┘   │
│                                    ▼                                   │
│   ┌────────────────────────────────────────────────────────────────┐   │
│   │                  Moteur Hybride à 3 Niveaux                    │   │
│   │  Niveau 1 : Glossaire Certifié Natif (< 5 ms, RapidFuzz >= 92%)│   │
│   │  Niveau 2 : Templates Transactionnels Paramétrés (< 10 ms)     │   │
│   │  Niveau 3 : IA Contrainte (Gemini / Ollama Local) (< 1.2 s)   │   │
│   └────────────────────────────────┬───────────────────────────────┘   │
│                                    ▼                                   │
│   ┌────────────────────────────────────────────────────────────────┐   │
│   │              IntegrityVerifier & Circuit-Breaker               │   │
│   │   Bijection tokens 100% + Zéro chiffre inventé + Polarité OK   │   │
│   └────────────────────────────────┬───────────────────────────────┘   │
│                                    ▼                                   │
│   ┌────────────────────────────────────────────────────────────────┐   │
│   │                  Audio Engine & TTS Hybride                    │   │
│   │  NumberComposer (0..999M FCFA) + AudioResolver + Capsules WAV   │   │
│   └────────────────────────────────────────────────────────────────┘   │
└────────────────────────────────────────────────────────────────────────┘
```

---

## 4. Structure Complète du Monorepo

```
Linguapay/
├── .github/
│   └── workflows/
│       ├── ci-backend.yml           # Tests Pytest, couverture & audit Bandit
│       ├── ci-extension.yml         # Typecheck TypeScript, Vitest & bundle MV3
│       ├── ci-security.yml          # Audit de vulnérabilités hebdomadaire
│       └── ci-e2e.yml               # Test smoke Playwright de bout en bout
├── backend/                         # LinguaPay Core API (Python 3.13 / FastAPI)
│   ├── .env.example                 # Modèle de configuration d'environnement
│   ├── pyproject.toml               # Configuration packaging et options Pytest
│   ├── requirements.txt             # Dépendances Python gelées
│   ├── app/
│   │   ├── main.py                  # Point d'entrée FastAPI, CORS et middlewares
│   │   ├── config.py                # Configuration Pydantic Settings
│   │   ├── api/v1/
│   │   │   ├── translate.py         # Routes POST /translate & POST /translate/batch
│   │   │   ├── glossary.py          # Routes GET /glossary/{lang} & GET /audit/recent
│   │   │   └── tts.py               # Routes POST /tts/sequence & GET /tts/capsule/{lang}/{clip}
│   │   ├── core/
│   │   │   ├── entity_shield.py     # Bouclier d'extraction et verrouillage déterministe
│   │   │   ├── pivot_bridge.py      # Pont universel multi-langues vers l'anglais
│   │   │   ├── glossary_engine.py   # Moteur Niveau 1 (glossaire exact & fuzzy)
│   │   │   ├── template_engine.py   # Moteur Niveau 2 (phrases paramétrées)
│   │   │   ├── ai_translator.py     # Moteur Niveau 3 (IA contrainte avec cache LRU)
│   │   │   ├── integrity_verifier.py# Circuit-Breaker et vérification d'invariance
│   │   │   └── audit_logger.py      # Journal d'audit en mémoire 100% anonymisé
│   │   └── tts/
│   │       ├── number_composer.py   # Algorithme de verbalisation des nombres FCFA
│   │       └── audio_resolver.py    # Assemblage de playlist pour lecture WebAudio
│   └── tests/                       # Suite complète de tests unitaires et fuzzing (26 tests)
│       ├── test_api_health_and_language_packs.py            # Santé API, chargement & conformité packs JSON
│       ├── test_financial_shield_and_invariance_fuzzing.py  # EntityShield & Fuzzing 600 cas d'invariance financière
│       ├── test_ai_translation_and_circuit_breaker.py       # Moteur IA L3, cache LRU & Circuit-Breaker
│       ├── test_fcfa_number_composer_and_audio.py           # Algorithme NumberComposer & synthèse audio WAV
│       ├── test_openapi_swagger_specification.py            # Spécification OpenAPI, documentation Swagger & ReDoc
│       └── test_universal_pivot_bridge.py                   # Détection multi-langues & pivot universel anglais
├── extension/                       # Extension Chrome / Edge Manifest V3 (TypeScript + esbuild)
│   ├── manifest.json                # Déclaration MV3 stricte
│   ├── package.json                 # Dépendances Node & scripts de build
│   ├── tsconfig.json                # Typage strict TypeScript
│   ├── build.mjs                    # Script de bundling autonome sans dépendances lourdes
│   ├── dist/                        # Bundle prêt à charger dans Chrome/Edge
│   └── src/
│       ├── background/
│       │   └── service-worker.ts    # Passerelle réseau isolée du CSP de la cible
│       ├── content/
│       │   ├── index.ts             # Orchestrateur Content Script
│       │   ├── dom-walker.ts        # Scanner DOM avec exclusion des secrets (PIN, password)
│       │   ├── mutation-watcher.ts  # Détection temps réel (MutationObserver debounce 80ms)
│       │   ├── entity-shield.ts     # Bouclier client TypeScript (invariance locale)
│       │   ├── offline-matcher.ts   # Résolution rapide hors-ligne via cache local
│       │   ├── audio-player.ts      # Lecteur WebAudio séquentiel (crossfade 25 ms)
│       │   └── shadow-overlay.ts    # Overlay flottant & Inspecteur Jury (Shadow DOM)
│       └── popup/
│           ├── popup.html           # Interface popup rapide
│           └── popup.ts             # Contrôleur d'activation popup
├── linguistics/                     # Référentiel Linguistique & Validation Native
│   ├── schema/
│   │   └── lang-pack.schema.json    # Schéma JSON Draft 2020-12 normé
│   ├── packs/
│   │   ├── ewondo.json              # Pack complet Ewondo (Centre / Sud)
│   │   ├── duala.json               # Pack complet Duala (Littoral)
│   │   └── fulfulde.json            # Pack complet Fulfulde (Grand Nord)
│   ├── audio/                       # Répertoire des capsules audio natives et générées
│   ├── validation/
│   │   └── README.md                # Protocole formel de validation en 4 phases
│   └── validate_packs.py            # Validateur automatisé de cohérence des dictionnaires
├── simulator/                       # Simulateur Indépendant de Démonstration (SimuBank CM)
│   ├── index.html                   # Application bancaire simulée (port 5173)
│   ├── app.js                       # Logique des 5 étapes du parcours + console jury
│   ├── styles.css                   # Feuilles de style de la banque simulée
│   └── microfinance-skin.html       # Interface alternative wallet mobile anglais
├── tests-e2e/                       # Tests Playwright d'intégration de bout en bout
│   ├── README.md
│   └── run_smoke.py                 # Lance SimuBank + API + Playwright avec l'extension
├── scripts/
│   └── package_extension.py         # Script d'empaquetage de l'extension en archive ZIP
├── linguapay-extension-v1.0.zip     # Archive de distribution prête pour le jury
├── CAHIER_DE_TESTS.md               # Guide de recette et protocole de test complet pas-à-pas
├── docker-compose.yml               # Déploiement local orchestré pour le jury
└── docs/                            # Dossier de documentation technique et d'architecture
    ├── livrable-1-description-succincte.md      # Livrable 1 : Fiche synthétique du projet
    ├── livrable-2-guide-reproductible.md        # Livrable 2 : Protocole pas-à-pas de reproduction
    ├── livrable-3-script-video-demonstration.md # Livrable 3 : Storyboard & script vidéo 3 minutes
    ├── livrable-4-note-technique.md             # Livrable 4 : Architecture & conformité Section 9
    ├── livrable-5-dossier-linguistique.md       # Livrable 5 : Dictionnaires, AGLC & validation 4 phases
    ├── declarations-tiers.md                    # Déclaration formelle des composants tiers et licences
    └── note-technique.md                        # Note technique synthétique
```

---

## 5. Guide de Démarrage Rapide

### Prérequis

- **Python** 3.12 ou 3.13
- **Node.js** 20 ou 22
- **Navigateur** Google Chrome ou Microsoft Edge (version 120+)

### Étape 1 : Cloner le dépôt

```bash
git clone <URL_DU_DEPOT>
cd Linguapay
```

### Étape 2 : Préparer et lancer le Backend Python

```powershell
# Créer et activer l'environnement virtuel
cd backend
python -m venv .venv
.\.venv\Scripts\activate

# Installer les dépendances
pip install -r requirements.txt

# Configurer l'environnement (optionnel, glossary_only par défaut)
cp .env.example .env

# Démarrer le serveur API FastAPI (port 8000)
uvicorn app.main:app --port 8000 --reload
```

Le serveur démarre sur `http://localhost:8000`.

- **Documentation interactive Swagger UI** : [http://localhost:8000/docs](http://localhost:8000/docs) (test interactif de chaque route avec pré-remplissage des exemples réels)
- **Documentation ReDoc** : [http://localhost:8000/redoc](http://localhost:8000/redoc)
- **Schéma OpenAPI 3.1.0** : `http://localhost:8000/openapi.json`

Vérifiez l'état de santé :

```bash
curl http://localhost:8000/api/v1/health
```

### Étape 3 : Compiler l'Extension Chrome / Edge MV3

Dans un second terminal :

```powershell
cd extension
npm install
npm run build
```

Les fichiers distribuables sont générés instantanément dans le dossier `extension/dist/`.

### Étape 4 : Charger l'Extension dans votre Navigateur

1. Ouvrez **Google Chrome** ou **Microsoft Edge**.
2. Accédez à l'URL : `chrome://extensions/` (ou `edge://extensions/`).
3. Activez le **Mode développeur** (en haut à droite).
4. Cliquez sur **Charger l'extension non empaquetée** (*Load unpacked*).
5. Sélectionnez le dossier : `c:\Users\PC\Documents\Linguapay\extension\dist`.

### Étape 5 : Lancer le Simulateur Bancaire (`SimuBank CM`)

Dans un troisième terminal :

```powershell
python -m http.server 5173 --directory simulator
```

Ouvrez dans votre navigateur : `http://localhost:5173/index.html`.

L'overlay flottant **LinguaPay** apparaît automatiquement en bas à droite de la page !

---

## 6. Guide des Tests & Vérifications Automatisées

> 📘 **Cahier de Recette Officiel** : Consultez le document exhaustif [CAHIER_DE_TESTS.md](file:///c:/Users/PC/Documents/Linguapay/CAHIER_DE_TESTS.md) qui détaille l'ensemble des scénarios de test (Swagger UI, bouclier financier, Circuit-Breaker, pivot multi-langues, simulateur bancaire SimuBank CM et épreuve jury live).

Le projet intègre une suite de tests rigoureuse couvrant les contrats d'API, l'invariance financière, le fuzzing et l'intégration de bout en bout.

### 1. Validation du Schéma des Packs Linguistiques

```powershell
backend\.venv\Scripts\python.exe linguistics\validate_packs.py
```

*Vérifie que chaque pack respecte `lang-pack.schema.json`, ne contient aucun identifiant dupliqué et que tous les tokens des templates sont bien préservés.*

### 2. Tests Backend, Fuzzing & Conformité OpenAPI (26 tests)

```powershell
cd backend
.\.venv\Scripts\python.exe -m pytest tests -v
```

Cette suite exécute :

- **Fuzzing sur 600 cas synthétiques aléatoires** : montants, frais, bénéficiaires camerounais, téléphones (+237) et devises (FCFA, XAF, EUR, USD) avec **0 % d'altération**.
- **Tests de Conformité OpenAPI / Swagger** : validation structurelle du schéma, exhaustivité des routes, conformité des métadonnées, codes 200 OK sur `/docs`, `/redoc` et `/openapi.json`.
- **Tests du Bouclier `EntityShield`** : masquage et démasquage réversible déterministe.
- **Tests du Vérificateur d'Intégrité `IntegrityVerifier`** : rejet immédiat si un token est supprimé, si un chiffre est inventé ou si une négation de sécurité est perdue.
- **Tests du Pont Universel `UniversalPivotBridge`** : détection multi-alphabets et pivot universel vers l'anglais pour 9 langues sources (ES, DE, PT, IT, SW, AR, ZH, RU, TR) avant adaptation vers les langues nationales.
- **Tests Audio `NumberComposer` & `AudioResolver`** : verbalisation grammaticale des montants de 0 à 1 000 000 FCFA en Ewondo, Duala et Fulfulde.
- **Audit Zéro-PII** : vérification que `/api/v1/audit/recent` ne contient aucune donnée personnelle en clair.

### 3. Tests TypeScript & Compilation de l'Extension

```powershell
cd extension
npm run typecheck
npm test
npm run build
```

### 4. Test Smoke End-to-End Automatisé (Playwright)

```powershell
backend\.venv\Scripts\python.exe tests-e2e\run_smoke.py
```

*Démarre automatiquement SimuBank CM et l'API FastAPI, lance Chromium avec l'extension MV3 chargée, vérifie la présence du Shadow DOM, injecte un message inédit, réalise un transfert simulé et valide la non-altération du solde.*

---

## 7. Déploiement

### Profil A : Déploiement Local Reproductible (Recommandé pour la Démonstration Jury)

Le fichier `docker-compose.yml` permet de démarrer l'ensemble du système en une seule commande, sans nécessiter de connexion internet :

```bash
docker compose up --build
```

- **Backend API** : disponible sur `http://localhost:8000`
- **Simulateur SimuBank** : disponible sur `http://localhost:5173`
- L'extension MV3 chargée localement dans Chrome/Edge communique directement avec le conteneur.

### Profil B : Déploiement Cloud Hybride (Évaluation à Distance)

- Le backend FastAPI peut être conteneurisé et déployé sur n'importe quel service Cloud (Cloud Run, Railway, VPS) avec la variable `LINGUAPAY_AI_PROVIDER=gemini` et `GEMINI_API_KEY`.
- L'extension est empaquetée en archive ZIP (`linguapay-extension-v1.0.zip`, générée via `python scripts/package_extension.py`) prête à être distribuée et installée par le jury.

---

## 8. Respect des Règles de Sécurité & d'Intégrité (Section 9)

- **Aucun compte réel ni transaction réelle** : l'environnement `SimuBank CM` utilise des soldes et des bénéficiaires purement fictifs.
- **Politique Zero-PII Egress** : aucun nom de bénéficiaire, numéro de téléphone ou solde bancaire réel n'est envoyé aux moteurs d'IA externes ; seuls des squelettes syntaxiques masqués (`{{AMT_1}}`, `{{BEN_1}}`) transitent sur le réseau.
- **Exclusion stricte des champs secrets** : les balises `<input type="password">`, champs OTP, CVV et codes PIN sont explicitement ignorés par le `DOMWalker` et ne sont jamais lus, stockés ou transmis.
- **Circuit-Breaker Fail-Safe** : à la moindre anomalie détectée post-traduction (placeholder manquant, chiffre inattendu), le système conserve automatiquement le texte original FR/EN sans interrompre l'expérience de l'utilisateur.

---

## 9. Contacts & Équipe

- **Projet** : LinguaPay Assistant
- **Statut** : Version 1.0.0 Production Ready
- **Licence du Code** : Propriété de l'équipe (composants tiers sous licences libres MIT / BSD / Apache-2.0 déclarées dans `docs/declarations-tiers.md`).
