# Livrable 2 — Guide de Démonstration Technique Reproductible

**Projet** : LinguaPay Assistant  
**Solution** : Couche d'Adaptation Linguistique Sécurisée & Vocale  
**Référence** : `LP-LIV-02-v1.0`

Ce document détaille la procédure pas-à-pas permettant au jury ou aux organisateurs de reproduire la démonstration complète sur n'importe quel ordinateur portable (Windows, macOS ou Linux), avec ou sans connexion Internet.

---

## 1. Options d'Exécution

| Méthode | Recommandée pour | Commandes clés |
| :--- | :--- | :--- |
| **Option A : Docker Compose** | Évaluation rapide sans installer Python/Node | `docker compose up --build` |
| **Option B : Local Natif** | Audit pas-à-pas du code source & tests unitaires | `pip install` + `npm run build` |
| **Option C : Script E2E Automatisé** | Vérification en 1 clic via Playwright | `python tests-e2e/run_smoke.py` |

---

## 2. Démonstration Pas-à-Pas (Option B & C)

### Étape 1 : Démarrer l'API Core LinguaPay
```bash
cd backend
# Sur Windows :
.\.venv\Scripts\activate
uvicorn app.main:app --port 8000
```
Le serveur démarre sur `http://localhost:8000`.
- **Documentation interactive Swagger UI** : `http://localhost:8000/docs` (test direct de toutes les routes API avec pré-remplissage)
- **Cahier de Recette Détaillé** : voir `CAHIER_DE_TESTS.md` à la racine du dépôt pour le guide complet des 25 cas de test.
- **Vérification de santé** : `http://localhost:8000/api/v1/health`

### Étape 2 : Démarrer le Simulateur Bancaire (`SimuBank CM`)
Dans un second terminal :
```bash
python -m http.server 5173 --directory simulator
```
L'interface de test est accessible sur `http://localhost:5173/index.html`.

### Étape 3 : Charger l'Extension Navigateur
1. Ouvrez **Google Chrome** ou **Microsoft Edge**.
2. Allez sur `chrome://extensions/` (ou `edge://extensions/`).
3. Activez le **Mode développeur** en haut à droite.
4. Cliquez sur **Charger l'extension non empaquetée** (*Load unpacked*).
5. Sélectionnez le dossier `Linguapay/extension/dist` (ou décompressez l'archive `linguapay-extension-v1.0.zip`).

---

## 3. Scénario de Test des 5 Capacités Minimales

Sur la page `http://localhost:5173/index.html` :

1. **Activation en 1 clic** :
   - Cliquez sur le panneau flottant **LinguaPay** en bas à droite (ou l'icône dans la barre d'outils).
   - Choisissez la langue : **Ewondo**, **Duala** ou **Fulfulde**.
   - Cliquez sur *« Traduire cette interface »* : les libellés se traduisent instantanément.
2. **Consultation du solde** :
   - Observez que le solde `145 750 FCFA` et le compte `**** 4821` sont **strictement identiques** et intacts.
   - Survolez le libellé pour voir l'infobulle originale en français.
3. **Vérification des frais & Transfert** :
   - Modifiez le montant dans le formulaire (ex. `50 000 FCFA`).
   - Observez le calcul des frais (`1 500 FCFA`) et le total à débiter (`51 500 FCFA`).
   - Cliquez sur *« Continuer »* : la modale de récapitulatif s'ouvre, traduite avec tous les montants conservés.
4. **Vérification vocale audio** :
   - Cliquez sur le bouton *« 🔊 Écouter le résumé (Audio) »* : la séquence sonore lit la phrase et décompose le montant en FCFA dans la langue nationale choisie.
5. **Démonstration du Contenu Inédit en Direct (Jury)** :
   - Dépliez la section *« Console d'Évaluation en Direct »* en bas à droite de SimuBank.
   - Cliquez sur *« Préréglage : Maintenance »* ou tapez un message libre (ex : `Interruption temporaire de 02h00 à 04h00 : les virements sont suspendus.`).
   - Cliquez sur *« Injecter ce message »* : le `MutationObserver` détecte l'élément en moins de 80 ms, masque les heures `02h00` et `04h00`, adapte le texte et affiche le résultat avec conservation rigoureuse des horaires !
6. **Restauration originale** :
   - Cliquez sur *« Restaurer texte original FR/EN »* dans le panneau : la page revient à son état initial exact.

