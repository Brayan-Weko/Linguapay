# Livrable 4 — Note Technique Officielle

**Événement** : SAFINUM Innovate Challenge 2026 (CNEF Cameroun)  
**Nom du Projet** : LinguaPay  
**Référence** : `LP-LIV-04-v1.0`

---

## 1. Architecture Générale de la Solution

LinguaPay adopte une architecture strictement découplée en trois couches pour satisfaire l'impératif de **Zéro-Intrusion** et d'**Indépendance absolue vis-à-vis du service financier cible** :

```
[ Navigateur Client ]                    [ LinguaPay Core API ]
+-------------------------+              +--------------------------+
|  DOM Bancaire Cible     |              |  UniversalPivotBridge    |
|  (Inchangé, non-modifié)|              |  (Pivot vers anglais)    |
|            |            |              +------------+-------------+
|            v            |                           |
|  DOMWalker (Exclusions) |                           v
|            |            |              +--------------------------+
|            v            |              |  GlossaryEngine (L1)     |
|  EntityShield (Client)  | === JSON ==> |  TemplateEngine (L2)     |
|            |            | (Zéro-PII)   |  AITranslator (L3)       |
|            v            |              +------------+-------------+
|  MutationObserver (80ms)|                           |
|            |            |                           v
|            v            |              +--------------------------+
|  Shadow DOM Overlay     |              |  IntegrityVerifier       |
|  & WebAudio Player      |              |  (Circuit-Breaker)       |
+-------------------------+              +--------------------------+
```

### 1.1 Modalités d'Intégration Côté Client (Extension MV3)
- **Manifest V3** : Utilise les APIs standardisées modernes (`content_scripts`, `background service worker`, `chrome.storage.local`).
- **Encapsulation Shadow DOM** : L'interface utilisateur de LinguaPay (panneau flottant, contrôles de langue, inspecteur de jury) est injectée dans un `ShadowRoot` fermé (`mode: 'closed'`). Aucun style CSS de la banque cible ne perturbe LinguaPay, et aucun style de LinguaPay ne modifie la mise en page de la banque hôte.
- **Contournement des politiques CSP hôtes** : Toutes les requêtes réseau sont relayées par le `Background Service Worker`, qui opère dans un contexte isolé non soumis aux directives `Content-Security-Policy: connect-src 'self'` de l'application bancaire hôte.

### 1.2 Pipeline de Traduction à Trois Niveaux & Préservation Financière
1. **Extraction Déterministe (`EntityShield`)** : Avant tout traitement linguistique, regex et automates d'états extraient tous les montants (ex : `50 000 FCFA`, `1 500.00 XAF`), pourcentages, téléphones camerounais (+237), références d'opérations et noms de bénéficiaires en jetons abstraits immuables (`{{AMT_1}}`, `{{BEN_1}}`).
2. **Niveau 1 — Glossaire Certifié Natif** : Résolution locale par hachage normalisé ou distance de Levenshtein (`RapidFuzz` $\ge 92\%$). Latence moyenne &lt; 5 ms.
3. **Niveau 2 — Patrons Transactionnels Paramétrés (`TemplateEngine`)** : Compilation des motifs récurrents (ex : *"Vous allez transférer {{AMT_1}} à {{BEN_1}}..."*) avec liaison stricte des variables.
4. **Niveau 3 — IA Contrainte (`AITranslator`)** : Pour les messages inédits ou dynamiques, appel à un grand modèle de langage avec consigne stricte de zéro-altération des jetons et injection des exemples du glossaire.
5. **Vérification d'Intégrité & Circuit-Breaker (`IntegrityVerifier`)** : Contrôle de bijection multiset des jetons, interdiction formelle de tout chiffre inventé hors placeholders, et vérification de la présence des marqueurs de négation pour les alertes de sécurité. En cas de non-conformité, le texte original FR/EN est immédiatement restauré.

---

## 2. Déclaration des Dépendances & Composants Tiers

Conformément à la Section 6 du règlement, l'ensemble des bibliothèques logicielles tierces est déclaré :

| Dépendance | Version | Licence | Rôle dans la solution |
| :--- | :---: | :---: | :--- |
| **Python** | 3.13.14 | PSF License | Langage principal du backend |
| **FastAPI** | 0.162.5 | MIT | Serveur d'API REST asynchrone |
| **Pydantic / Pydantic-Settings** | 2.14 / 2.16 | MIT | Validation de contrats et typage fort |
| **Uvicorn** | 0.54.0 | BSD-3-Clause | Serveur ASGI de production |
| **RapidFuzz** | 3.14.6 | MIT | Correspondance floue haute performance |
| **HTTPX** | 0.28.1 | BSD-3-Clause | Client HTTP asynchrone pour les adaptateurs IA |
| **JSONSchema** | 4.26.0 | MIT | Validation structurelle des packs de langues |
| **Playwright** | 1.65.1 | Apache-2.0 | Tests d'intégration E2E automatisés |
| **TypeScript / esbuild** | 5.7 / 0.25 | Apache / MIT | Typage strict et bundling de l'extension |
| **Vitest** | 3.2.7 | MIT | Tests unitaires de l'extension client |

---

## 3. Limites Connues de la Solution (Version Prototype v1.0)

1. **Textes embarqués dans des images rasterisées (PNG/JPEG sans attributs)** :
   - Si une banque diffuse une bannière promotionnelle sous forme d'image PNG sans texte alternatif (`alt` ou `aria-label`), LinguaPay v1.0 ne traduit pas l'image (nécessiterait un module OCR embarqué, prévu dans la roadmap v2.0).
2. **Éléments dans des canvas HTML5 ou WebGL** :
   - Les graphiques financiers rendus exclusivement via l'API Canvas 2D/WebGL sans arbre DOM textuel sous-jacent ne sont pas indexables par le `DOMWalker`.
3. **Latence du Niveau 3 en cas de connexion réseau satellite très lente** :
   - Alors que les Niveaux 1 et 2 répondent en moins de 10 ms en cache local, la génération par IA externe sur un contenu inédit très long dépend de la latence Internet (mesurée entre 0,6 s et 1,2 s avec Gemini 2.5 Flash).

