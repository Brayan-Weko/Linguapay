# 🎬 Vidéo Officielle de Présentation — LinguaPay Assistant

## 🔗 Liens d'Accès Publics

* **Téléchargement / Visionnage Direct (Release GitHub) :**  
  [https://github.com/Brayan-Weko/Linguapay/releases/download/v1.0.0/demo_linguapay_presentation.webm](https://github.com/Brayan-Weko/Linguapay/releases/download/v1.0.0/demo_linguapay_presentation.webm)
* **Release Complète des Livrables :**  
  [https://github.com/Brayan-Weko/Linguapay/releases/tag/v1.0.0](https://github.com/Brayan-Weko/Linguapay/releases/tag/v1.0.0)

---

## 📋 Contenu & Parcours Démontré dans la Vidéo (HD 720p)

1. **Parcours Bancaire Réel (`SimuBank CM`)** : Présentation initiale de l'interface en français (solde 145 750 FCFA, carte bancaire, formulaires de virement).
2. **Activation de LinguaPay en un clic** : Sélection de la langue nationale **Ewondo** via le Shadow DOM isolé.
3. **Adaptation Instantanée & Zéro-Intrusion** : Traduction fluide des libellés et infobulles bilingues au survol sans aucune altération du montant.
4. **Virement & Préservation des Frais** : Saisie d'un virement de 50 000 FCFA avec calcul automatique des frais (1 500 FCFA) et récapitulatif totalisé à 51 500 FCFA.
5. **Assistance Vocale WebAudio & Verbalisation FCFA** : Décomposition vocale grammaticale du montant en FCFA dans la langue nationale.
6. **Épreuve du Contenu Inédit en Direct** : Détection et traduction en moins de 80 ms d'une alerte de maintenance imprévue avec conservation des horaires (02h00 et 04h00).
7. **Inspecteur d'Intégrité & Audit Zero-PII** : Affichage en direct des jetons verrouillés et de l'empreinte SHA-256 sans fuite de données personnelles.
8. **Parité Linguistique Duala & Fulfulde** : Bascule instantanée démontrant la couverture équitable des 3 langues nationales.
9. **Restauration Immédiate** : Retour instantané à l'interface originale française en un clic.

---

## 🛠️ Reproductibilité

La vidéo a été générée de façon 100 % automatisée et reproductible via Playwright :
```powershell
backend\.venv\Scripts\python.exe scripts/record_demo_video.py
```
