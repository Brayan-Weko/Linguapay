# Livrable 1 — Description Succincte de la Solution

**Événement** : SAFINUM Innovate Challenge 2026 (CNEF Cameroun)  
**Nom du Projet** : LinguaPay  
**Référence** : `LP-LIV-01-v1.0`

---

## 1. Problème Résolu

Au Cameroun, la digitalisation financière s'est accélérée (Mobile Money, applications bancaires, microfinance), mais les interfaces restent quasi exclusivement rédigées en **français** ou en **anglais**, utilisant un vocabulaire administratif et technique complexe (*solde disponible, frais de commission, bénéficiaire, code PIN secret, virement irréversible*).

Pour des millions de citoyens dont les langues d'usage quotidien sont les langues nationales (Ewondo, Duala, Fulfulde, etc.), cette barrière linguistique entraîne :
- **L'exclusion numérique** : renoncement aux services financiers ou dépendance dangereuse à des tiers pour effectuer des opérations (perte de confidentialité des codes PIN).
- **Le risque financier** : incompréhension des frais appliqués ou des montants débités.
- **La vulnérabilité aux fraudes** : incapacité à décrypter les avertissements de sécurité et messages d'alerte.

## 2. Solution Proposée : LinguaPay

**LinguaPay** est une couche d'adaptation linguistique et vocale **universelle, sécurisée et non-intrusive** qui s'intègre par-dessus n'importe quel service financier numérique existant, **sans modifier une seule ligne de son code source**.

### Piliers Clés de l'Innovation :
1. **Zéro-Intrusion & Compatibilité Universelle** : L'adaptation s'opère côté client via une extension de navigateur (Manifest V3) et un composant Shadow DOM isolé, compatible avec tout portail web bancaire ou de paiement en ligne.
2. **Préservation Déterministe des Données Financières (`EntityShield`)** : Avant toute traduction, un bouclier mathématique extrait et verrouille 100 % des montants en FCFA, pourcentages de frais, numéros de téléphone (+237), comptes et noms de bénéficiaires dans des jetons immuables (`{{AMT_1}}`, `{{BEN_1}}`). Aucun montant ne peut être déformé.
3. **Moteur Hybride à 3 Niveaux & Circuit-Breaker** :
   - **Niveau 1 (Glossaire Certifié)** : Résolution locale instantanée (&lt; 5 ms) basée sur une terminologie bancaire validée par des locuteurs natifs.
   - **Niveau 2 (Templates Paramétrés)** : Prise en charge des phrases transactionnelles complexes avec variables liées.
   - **Niveau 3 (IA Contrainte)** : Traitement en temps réel des **contenus inédits** injectés en direct, avec validation d'invariance obligatoire avant affichage. En cas d'anomalie, le *Circuit-Breaker* préserve le texte original.
4. **Pont Universel vers l'Anglais (`UniversalPivotBridge`)** : Si une plateforme financière étrangère utilise une autre langue (espagnol, allemand, portugais, swahili, etc.), LinguaPay pivote le texte masqué vers l'anglais avant de le restituer dans les langues nationales.
5. **Assistance Vocale Native Hybride** : Verbalisation complète des montants en FCFA (`NumberComposer`) et lecture audio séquentielle WebAudio avec fondu de 25 ms pour les personnes analphabètes ou malvoyantes.

## 3. Impact Attendu sur l'Inclusion Financière

- **Autonomie complète** des usagers pour consulter leur solde, vérifier les frais et valider des transferts sans recourir à un intermédiaire.
- **Conformité totale avec la Section 9 du Règlement SAFINUM** : aucune donnée personnelle (PII) n'est collectée, aucune modification du service cible n'est requise, et le système est 100 % fonctionnel hors-ligne en salle de jury.
