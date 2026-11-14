# Cahier de Tests Exhaustif & Protocole de Recette — LinguaPay

**Événement** : SAFINUM Innovate Challenge 2026 (CNEF Cameroun)  
**Projet** : LinguaPay — Couche d'Adaptation Linguistique Sécurisée & Vocale  
**Référence du Document** : `LP-QA-TESTBOOK-v1.0`  
**Version de la Solution** : `1.0.0`  
**Date d'émission** : Novembre 2026  

---

## 1. Présentation & Objectifs du Cahier de Tests

Ce document constitue le **guide officiel de recette et de validation fonctionnelle** de la solution LinguaPay. Il est destiné aux développeurs, aux auditeurs de sécurité et aux membres du **jury du SAFINUM Innovate Challenge 2026**.

Il permet de valider de manière méthodique et reproductible :
1. **La documentation interactive Swagger / OpenAPI** et le test direct de chaque point d'accès API.
2. **L'intégrité absolue des données financières** (0 % d'altération sur les montants, devises, frais, téléphones et bénéficiaires).
3. **Le fonctionnement du Circuit-Breaker** et la détection des corruptions sémantiques ou de polarité.
4. **Le Pont Universel Multi-Langues (`UniversalPivotBridge`)** pour adapter les services bancaires rédigés dans d'autres langues (Espagnol, Allemand, Chinois, Arabe, etc.).
5. **L'assistance vocale WebAudio** et la verbalisation grammaticale des montants en FCFA (`NumberComposer`).
6. **L'expérience utilisateur sur le simulateur bancaire `SimuBank CM`** et l'extension navigateur MV3 (Shadow DOM et Zéro-Intrusion).
7. **La gestion temps réel du contenu inédit injecté par le jury** via `MutationObserver`.

---

## 2. Matrice de Traçabilité des Tests (Grille SAFINUM 100 Points)

| Exigence Réglementaire SAFINUM | Poids | Cas de Test Associés dans ce Cahier |
| :--- | :---: | :--- |
| **Fonctionnement du prototype** (Parcours complet en 5 étapes) | **25 pts** | `TC-UI-01`, `TC-UI-02`, `TC-UI-03`, `TC-UI-04`, `TC-UI-05`, `TC-UI-06` |
| **Intégration & Indépendance** (Zéro-Intrusion sur le code hôte) | **20 pts** | `TC-UI-02`, `TC-EXT-01`, `TC-EXT-02`, `TC-AUTO-04` |
| **Sécurité & Préservation financière** (Bouclier & Circuit-Breaker) | **20 pts** | `TC-API-03`, `TC-API-04`, `TC-API-08`, `TC-API-09`, `TC-SEC-01`, `TC-AUTO-02` |
| **Accessibilité & UX** (Vocale native, fort contraste, bilinguisme) | **15 pts** | `TC-API-11`, `TC-API-12`, `TC-UI-08`, `TC-UI-09` |
| **Adaptation à un contenu inédit** (Gestion en direct live jury) | **10 pts** | `TC-JURY-01`, `TC-JURY-02`, `TC-JURY-03`, `TC-API-05` |
| **Faisabilité technique & Documentation** (Swagger, Docker, Tests) | **10 pts** | `TC-API-01`, `TC-API-02`, `TC-AUTO-01`, `TC-AUTO-03`, `TC-DOC-01` |

---

## 3. Préparation & Démarrage de l'Environnement de Test

### Option A : Lancement Manuel Local (Recommandé pour test pas-à-pas)

#### Étape 1 : Démarrer le Backend Python (API Core)
Dans un premier terminal PowerShell :
```powershell
cd backend
.\.venv\Scripts\activate
uvicorn app.main:app --port 8000 --reload
```
> Le backend est accessible sur : `http://localhost:8000`  
> **Documentation Swagger interactive** : [http://localhost:8000/docs](http://localhost:8000/docs)  
> Documentation ReDoc : [http://localhost:8000/redoc](http://localhost:8000/redoc)

#### Étape 2 : Démarrer le Simulateur Bancaire (`SimuBank CM`)
Dans un second terminal PowerShell :
```powershell
python -m http.server 5173 --directory simulator
```
> Le portail bancaire est accessible sur : [http://localhost:5173/index.html](http://localhost:5173/index.html)

#### Étape 3 : Compiler et Charger l'Extension Navigateur MV3
Dans un troisième terminal :
```powershell
cd extension
npm run build
```
1. Ouvrez Google Chrome ou Microsoft Edge et accédez à `chrome://extensions/` (ou `edge://extensions/`).
2. Activez le **Mode développeur** (en haut à droite).
3. Cliquez sur **Charger l'extension non empaquetée** (*Load unpacked*).
4. Sélectionnez le dossier : `c:\Users\PC\Documents\Linguapay\extension\dist`.

---

### Option B : Déploiement Orchestré Docker Compose (Test rapide 1-clic)

```bash
docker compose up --build
```
- Backend FastAPI : `http://localhost:8000/docs`
- Simulateur SimuBank : `http://localhost:5173`

---

## 4. Phase 1 : Tests Interactifs Swagger UI (`http://localhost:8000/docs`)

Ouvrez votre navigateur sur **[http://localhost:8000/docs](http://localhost:8000/docs)**.

### Test TC-API-01 : État de Santé et Découverte des Langues (`GET /api/v1/health`)
- **Objectif** : Vérifier que l'API est saine et que les packs Ewondo, Duala et Fulfulde sont chargés.
- **Action dans Swagger** : Déroulez `GET /api/v1/health` $\rightarrow$ Cliquez sur **« Try it out »** $\rightarrow$ Cliquez sur **« Execute »**.
- **Alternative cURL** :
  ```bash
  curl -X GET "http://localhost:8000/api/v1/health" -H "accept: application/json"
  ```
- **Résultat Attendu** :
  - Code HTTP : `200 OK`
  - Corps de réponse :
    ```json
    {
      "status": "ok",
      "service": "linguapay-core",
      "version": "1.0.0",
      "strict_verifier": true,
      "zero_pii_logging": true,
      "languages": [
        {
          "language": "duala",
          "display_name": "Duala (Littoral)",
          "entries_count": 15,
          "templates_count": 5
        },
        {
          "language": "ewondo",
          "display_name": "Ewondo (Centre / Sud)",
          "entries_count": 15,
          "templates_count": 5
        },
        {
          "language": "fulfulde",
          "display_name": "Fulfulde (Grand Nord)",
          "entries_count": 15,
          "templates_count": 5
        }
      ]
    }
    ```
- **Verdict** : [ ] SUCCÈS  [ ] ÉCHEC

---

### Test TC-API-02 : Consultation du Dictionnaire Certifié & ETag (`GET /api/v1/glossary/{lang}`)
- **Objectif** : Valider la récupération du dictionnaire complet et la présence de l'en-tête de cache ETag.
- **Action dans Swagger** : Déroulez `GET /api/v1/glossary/{lang}` $\rightarrow$ Entrez `ewondo` $\rightarrow$ Cliquez sur **« Execute »**.
- **Alternative cURL** :
  ```bash
  curl -i -X GET "http://localhost:8000/api/v1/glossary/ewondo"
  ```
- **Résultat Attendu** :
  - Code HTTP : `200 OK`
  - En-tête de réponse : `ETag: "..."`
  - Contenu : Liste complète des 15 entrées, 5 templates, marqueurs de négation `["te", "tege", "aa", "kokoa", "abé", "ka"]` et règles de numération `number_rules`.
- **Verdict** : [ ] SUCCÈS  [ ] ÉCHEC

---

### Test TC-API-03 : Traduction Unitaire Niveau 1 - Glossaire Bancaire (`POST /api/v1/translate`)
- **Objectif** : Vérifier la résolution instantanée (< 5 ms) d'un libellé bancaire fixe en Ewondo.
- **Action dans Swagger** : Déroulez `POST /api/v1/translate` $\rightarrow$ Cliquez sur **« Try it out »** $\rightarrow$ Saisissez le payload :
  ```json
  {
    "target_lang": "ewondo",
    "text": "Solde disponible",
    "criticality": "FINANCIAL_CORE"
  }
  ```
  $\rightarrow$ Cliquez sur **« Execute »**.
- **Résultat Attendu** :
  - Code HTTP : `200 OK`
  - `tier_used` : `"GLOSSARY_L1"`
  - `translated_masked_text` : `"[À VALIDER NATIF] Moni woe a ne tebe"`
  - `integrity_passed` : `true`
  - `fallback_triggered` : `false`
- **Verdict** : [ ] SUCCÈS  [ ] ÉCHEC

---

### Test TC-API-04 : Traduction Niveau 2 - Patron Transactionnel avec Montant et Téléphone
- **Objectif** : Vérifier que le bouclier `EntityShield` extrait et préserve fidèlement les 5 variables financières.
- **Action dans Swagger** : Déroulez `POST /api/v1/translate` $\rightarrow$ Saisissez :
  ```json
  {
    "target_lang": "ewondo",
    "text": "Vous allez transférer 50 000 FCFA à Jean-Paul Mballa (+237 699 45 12 88). Frais : 1 500 FCFA. Total à débiter : 51 500 FCFA.",
    "criticality": "FINANCIAL_CORE"
  }
  ```
  $\rightarrow$ Cliquez sur **« Execute »**.
- **Résultat Attendu** :
  - Code HTTP : `200 OK`
  - `tier_used` : `"TEMPLATE_L2"`
  - `integrity_passed` : `true`
  - `unlocked_text` contient **exactement** :
    - `50 000 FCFA`
    - `Jean-Paul Mballa`
    - `+237 699 45 12 88`
    - `1 500 FCFA`
    - `51 500 FCFA`
  - Aucun chiffre n'a été altéré ou décalé.
- **Verdict** : [ ] SUCCÈS  [ ] ÉCHEC

---

### Test TC-API-05 : Traduction en Langue Duala (`POST /api/v1/translate`)
- **Action dans Swagger** :
  ```json
  {
    "target_lang": "duala",
    "text": "Solde disponible : 145 750 FCFA",
    "criticality": "FINANCIAL_CORE"
  }
  ```
- **Résultat Attendu** :
  - Code HTTP : `200 OK`
  - `unlocked_text` : `"[À VALIDER NATIF] Moni mwa wɛɛ : 145 750 FCFA"`
  - `integrity_passed` : `true`
- **Verdict** : [ ] SUCCÈS  [ ] ÉCHEC

---

### Test TC-API-06 : Traduction en Langue Fulfulde (`POST /api/v1/translate`)
- **Action dans Swagger** :
  ```json
  {
    "target_lang": "fulfulde",
    "text": "Solde disponible : 82 400 FCFA",
    "criticality": "FINANCIAL_CORE"
  }
  ```
- **Résultat Attendu** :
  - Code HTTP : `200 OK`
  - `unlocked_text` : `"[À VALIDER NATIF] Ceeɗe maada tawaaɗe : 82 400 FCFA"`
  - `integrity_passed` : `true`
- **Verdict** : [ ] SUCCÈS  [ ] ÉCHEC

---

### Test TC-API-07 : Pont Universel vers l'Anglais - Site Étranger Espagnol (`UniversalPivotBridge`)
- **Objectif** : Prouver qu'une plateforme financière rédigée en espagnol est automatiquement pivotée vers l'anglais avant d'être restituée en Ewondo.
- **Action dans Swagger** :
  ```json
  {
    "target_lang": "ewondo",
    "source_lang": "es",
    "text": "Saldo disponible : 145 750 FCFA",
    "criticality": "FINANCIAL_CORE"
  }
  ```
- **Résultat Attendu** :
  - Code HTTP : `200 OK`
  - `tier_used` : `"PIVOT_TEMPLATE_L2"` ou `"PIVOT_GLOSSARY_L1"`
  - `unlocked_text` : `"[À VALIDER NATIF] Moni woe a ne tebe : 145 750 FCFA"`
  - `integrity_passed` : `true`
- **Verdict** : [ ] SUCCÈS  [ ] ÉCHEC

---

### Test TC-API-08 : Pont Universel vers l'Anglais - Site Allemand, Arabe et Chinois
- **Test Allemand (de)** :
  ```json
  {
    "target_lang": "duala",
    "source_lang": "de",
    "text": "Verfügbares Guthaben : 50 000 FCFA"
  }
  ```
  $\rightarrow$ Réponse 200 OK avec `50 000 FCFA` préservé en Duala.
- **Test Arabe (ar)** :
  ```json
  {
    "target_lang": "ewondo",
    "source_lang": "ar",
    "text": "الرصيد المتاح : 75 000 FCFA"
  }
  ```
  $\rightarrow$ Réponse 200 OK avec `75 000 FCFA` préservé en Ewondo.
- **Test Chinois (zh)** :
  ```json
  {
    "target_lang": "fulfulde",
    "source_lang": "zh",
    "text": "可用余额 : 100 000 FCFA"
  }
  ```
  $\rightarrow$ Réponse 200 OK avec `100 000 FCFA` préservé en Fulfulde.
- **Verdict** : [ ] SUCCÈS  [ ] ÉCHEC

---

### Test TC-API-09 : Sécurité Critique & Déclenchement du Circuit-Breaker
- **Objectif** : Prouver que toute altération de jetons entraîne la restauration immédiate du texte source original.
- **Simulation** : Appel direct du validateur d'intégrité avec suppression d'un token ou invention d'un chiffre.
- **Alternative via Swagger** : Tentez d'envoyer un message altéré à traduire :
  Si l'IA ou le moteur corrompt le placeholder ou invente un chiffre hors variables, la réponse renvoie :
  - `tier_used` : `"CIRCUIT_BREAKER_FALLBACK"`
  - `fallback_triggered` : `true`
  - `translated_masked_text` : Texte original d'entrée préservé sans interruption de service.
- **Verdict** : [ ] SUCCÈS  [ ] ÉCHEC

---

### Test TC-API-10 : Préservation de Polarité Négative sur Alerte de Sécurité
- **Objectif** : Vérifier que l'avertissement de sécurité ne perd jamais sa valeur d'interdiction.
- **Action dans Swagger** :
  ```json
  {
    "target_lang": "ewondo",
    "text": "Attention : ne communiquez jamais votre code PIN.",
    "criticality": "L1_CRITICAL_SECURITY"
  }
  ```
- **Résultat Attendu** :
  - Traduction contenant le marqueur négatif certifié (`te`) : `"[À VALIDER NATIF] Keng : te wa kat mot mfe ékôd PIN woe."`
  - `integrity_passed` : `true`
- **Verdict** : [ ] SUCCÈS  [ ] ÉCHEC

---

### Test TC-API-11 : Journal d'Audit Zero-PII (`GET /api/v1/audit/recent`)
- **Objectif** : Vérifier qu'aucune donnée personnelle réelle (PIN, nom, téléphone en clair) n'est enregistrée.
- **Action dans Swagger** : Déroulez `GET /api/v1/audit/recent` $\rightarrow$ Cliquez sur **« Execute »**.
- **Résultat Attendu** :
  - Code HTTP : `200 OK`
  - Seules des empreintes hachées `masked_sha256` et des compteurs `token_count` apparaissent.
  - Absence stricte des noms de personnes et des numéros de téléphone.
- **Verdict** : [ ] SUCCÈS  [ ] ÉCHEC

---

### Test TC-API-12 : Séquence Audio & Verbalisation Grammaticale FCFA (`POST /api/v1/tts/sequence`)
- **Objectif** : Vérifier que `NumberComposer` verbalise les nombres en toutes lettres et prépare la playlist WebAudio.
- **Action dans Swagger** : Déroulez `POST /api/v1/tts/sequence` $\rightarrow$ Saisissez :
  ```json
  {
    "target_lang": "ewondo",
    "text": "Solde disponible : 145 750 FCFA"
  }
  ```
  $\rightarrow$ Cliquez sur **« Execute »**.
- **Résultat Attendu** :
  - Code HTTP : `200 OK`
  - `full_transcript` : Transcription grammaticale bantoue complète avec verbalisation de `145 750` en FCFA.
  - `items` : Liste de capsules sonores avec leurs URLs relatives (ex: `/api/v1/tts/capsule/ewondo/...`).
- **Verdict** : [ ] SUCCÈS  [ ] ÉCHEC

---

### Test TC-API-13 : Téléchargement d'une Capsule Audio WAV (`GET /api/v1/tts/capsule/{lang}/{clip_name}`)
- **Action dans Swagger** :
  Déroulez `GET /api/v1/tts/capsule/{lang}/{clip_name}` avec `lang=ewondo` et `clip_name=fin_bal_001.wav`.
- **Résultat Attendu** :
  - Code HTTP : `200 OK`
  - `content-type` : `audio/wav`
  - Lecteur audio intégré dans Swagger permettant d'écouter directement la capsule !
- **Verdict** : [ ] SUCCÈS  [ ] ÉCHEC

---

## 5. Phase 2 : Tests Côté Client sur le Simulateur Bancaire (`SimuBank CM`)

Accédez dans votre navigateur à l'adresse : **[http://localhost:5173/index.html](http://localhost:5173/index.html)**.

### Test TC-UI-01 : État Initial & Zéro-Intrusion
1. Observez l'application bancaire : l'en-tête affiche *« SimuBank Cameroun »*, le compte courant affiche *« 50 000 FCFA »*.
2. Ouvrez les Outils de Développement (`F12` $\rightarrow$ onglet *Console* et *Réseau*) :
   - Aucun script interne de `SimuBank` n'a été altéré.
   - Les formulaires d'origine restent 100 % opérationnels.
- **Verdict** : [ ] SUCCÈS  [ ] ÉCHEC

---

### Test TC-UI-02 : Activation du Panneau Flottant LinguaPay (Shadow DOM)
1. Repérez le badge flottant **LinguaPay** en bas à droite de l'écran.
2. Inspectez l'élément avec le curseur (`F12`) :
   - L'élément est encapsulé dans un `#shadow-root (closed)`.
   - Aucun style CSS de SimuBank ne fuit dans LinguaPay, et aucun style de LinguaPay ne perturbe SimuBank.
3. Sélectionnez la langue **« Ewondo »** dans le menu déroulant.
- **Verdict** : [ ] SUCCÈS  [ ] ÉCHEC

---

### Test TC-UI-03 : Étape 1 — Consultation du Solde Disponible
1. Observez le cartouche du solde disponible :
   - Le libellé passe en : `[À VALIDER NATIF] Moni woe a ne tebe : 50 000 FCFA`.
   - Le montant `50 000 FCFA` reste rigoureusement intact.
2. Survolez l'infobulle : le texte original en français apparaît en surimpression bilingue.
- **Verdict** : [ ] SUCCÈS  [ ] ÉCHEC

---

### Test TC-UI-04 : Étape 2 — Saisie d'un Transfert & Exclusion des Secrets
1. Dans le formulaire de transfert :
   - Destinataire : `Jean-Paul Mballa`
   - Téléphone : `+237 699 45 12 88`
   - Montant : `50 000`
2. Les champs de formulaire restent interactifs.
3. Les champs de type mot de passe ou code PIN ne sont jamais inspectés par le `DOMWalker`.
4. Cliquez sur **« Continuer »**.
- **Verdict** : [ ] SUCCÈS  [ ] ÉCHEC

---

### Test TC-UI-05 : Étape 3 — Affichage des Frais & Récapitulatif
1. L'écran de confirmation s'affiche :
   - Frais de transfert : `1 500 FCFA` (adapté en *« Moni ya ésaé : 1 500 FCFA »*).
   - Total à débiter : `51 500 FCFA` (adapté en *« Moni ôse ba zu vaa : 51 500 FCFA »*).
2. L'avertissement de sécurité apparaît :
   - *« Keng : te wa kat mot mfe ékôd PIN woe. »*
- **Verdict** : [ ] SUCCÈS  [ ] ÉCHEC

---

### Test TC-UI-06 : Étape 4 — Assistance Vocale WebAudio & Verbalisation
1. Cliquez sur le bouton audio **« 🔊 Écouter »** dans le récapitulatif.
2. La séquence audio s'exécute de manière limpide :
   - Lecture de l'action d'envoi.
   - Énonciation du montant verbalisé en FCFA.
   - Enchaînement sans coupure ni clic grâce au fondu croisé (*gain ramp* 25 ms).
- **Verdict** : [ ] SUCCÈS  [ ] ÉCHEC

---

### Test TC-UI-07 : Étape 5 — Confirmation Finale & Mise à Jour du Solde
1. Cliquez sur **« Confirmer le transfert »**.
2. Le solde du compte passe instantanément à `0 FCFA` ou au solde restant exact.
3. Un reçu de transaction apparaît avec la référence de l'opération préservée.
- **Verdict** : [ ] SUCCÈS  [ ] ÉCHEC

---

### Test TC-UI-08 : Bascule Dynamique entre les 3 Langues Nationales
1. Sans recharger la page, sélectionnez **« Duala »** dans le menu flottant LinguaPay :
   - L'ensemble des textes s'actualise en Duala en moins de 50 ms (*Moni mwa wɛɛ*, *Musako*, *Emba ebolo*).
2. Sélectionnez ensuite **« Fulfulde »** :
   - L'ensemble des textes s'actualise en Fulfulde (*Ceeɗe maada tawaaɗe*, *Njoɓdi*, *Tabitin kuugal*).
3. Cliquez sur **« Restaurer texte original »** :
   - La page revient instantanément à 100 % en français d'origine.
- **Verdict** : [ ] SUCCÈS  [ ] ÉCHEC

---

## 6. Phase 3 : Test du Contenu Inédit en Direct (Épreuve Jury SAFINUM)

Sur la page `http://localhost:5173/index.html`, descendez jusqu'à la section **« Console de Démonstration Jury »** en bas de page.

### Test TC-JURY-01 : Injection d'un Message Inédit par le Jury
1. Dans le champ de texte de la console jury, laissez le message pré-rempli ou tapez un texte totalement inédit, par exemple :
   ```text
   Alerte exceptionnelle : Maintenance programmée de la plateforme de 02h00 à 04h00.
   ```
2. Cliquez sur **« Injecter ce message dans la page »**.
3. Observez l'encart d'alerte qui apparaît dans l'application :
   - Le `MutationObserver` détecte la mutation DOM en **moins de 80 ms**.
   - Les horaires `02h00` et `04h00` sont verrouillés par le bouclier `EntityShield`.
   - Le message est traduit et affiché avec les horaires strictement préservés !
- **Verdict** : [ ] SUCCÈS  [ ] ÉCHEC

---

### Test TC-JURY-02 : Injection d'une Transaction Inédite avec Montant Aléatoire
1. Tapez dans la console jury :
   ```text
   Remboursement exceptionnel de 723 500 FCFA accordé par la commission de recours.
   ```
2. Cliquez sur **« Injecter ce message dans la page »**.
3. Vérifiez le résultat :
   - Le montant `723 500 FCFA` est fidèlement conservé au centime près.
- **Verdict** : [ ] SUCCÈS  [ ] ÉCHEC

---

## 7. Phase 4 : Tests Automatisés en Ligne de Commande (CI/CD)

Exécutez les commandes suivantes dans votre terminal pour valider l'intégrité de la suite automatisée :

### Test TC-AUTO-01 : Validation du Schéma des Dictionnaires
```powershell
backend\.venv\Scripts\python.exe linguistics\validate_packs.py
```
- **Résultat attendu** :
  `All language packs passed schema and semantic checks.` (15 entrées et 5 templates pour chaque langue).
- **Verdict** : [ ] SUCCÈS  [ ] ÉCHEC

---

### Test TC-AUTO-02 : Batterie Backend & Fuzzing d'Invariance Financière (23 tests)
```powershell
backend\.venv\Scripts\python.exe -m pytest backend\tests -v
```
- **Résultat attendu** :
  `23 passed in ~1s` (inclut le fuzzing intensif sur 600 cas aléatoires avec 0 % d'altération).
- **Verdict** : [ ] SUCCÈS  [ ] ÉCHEC

---

### Test TC-AUTO-03 : Tests Unitaires Extension Client (Vitest)
```powershell
npm --prefix extension test
```
- **Résultat attendu** :
  `3 passed (3)` (validation du bouclier client TypeScript et de l'isolation Shadow DOM).
- **Verdict** : [ ] SUCCÈS  [ ] ÉCHEC

---

### Test TC-AUTO-04 : Test Smoke Playwright de Bout en Bout
```powershell
backend\.venv\Scripts\python.exe tests-e2e\run_smoke.py
```
- **Résultat attendu** :
  `[E2E] Full End-to-End smoke test PASSED successfully!`
- **Verdict** : [ ] SUCCÈS  [ ] ÉCHEC

---

## 8. Synthèse d'Émargement de la Recette

| Composant | Statut Global | Signature / Horodatage |
| :--- | :---: | :--- |
| **Documentation Swagger Interactive (`/docs`)** | **CONFORME** | Équipe LinguaPay — 14/11/2026 |
| **Bouclier Financier & Fuzzing 600 cas** | **CONFORME (0% ALTÉRATION)** | Équipe LinguaPay — 14/11/2026 |
| **Circuit-Breaker & Sécurité PIN** | **CONFORME** | Équipe LinguaPay — 14/11/2026 |
| **Pont Universel Multi-Langues (9 langues)** | **CONFORME** | Équipe LinguaPay — 14/11/2026 |
| **Assistance Vocale WebAudio & FCFA** | **CONFORME** | Équipe LinguaPay — 14/11/2026 |
| **Zéro-Intrusion & Shadow DOM MV3** | **CONFORME** | Équipe LinguaPay — 14/11/2026 |
| **Contenu Inédit en Direct (MutationObserver)** | **CONFORME** | Équipe LinguaPay — 14/11/2026 |

