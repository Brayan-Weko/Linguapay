# Protocole de Validation Linguistique — LinguaPay

Conformément aux **Sections 6 et 8** du règlement *SAFINUM Innovate Challenge*, chaque pack linguistique (`ewondo.json`, `duala.json`, `fulfulde.json`) suit un processus de validation en 4 phases avant promotion au statut `CERTIFIED` :

1. **Traduction directe** par un locuteur natif maîtrisant la langue nationale et le vocabulaire financier courant.
2. **Rétro-traduction à l'aveugle** (*back-translation*) vers le français/anglais par un second locuteur indépendant.
3. **Audit d'exactitude financière & sécuritaire** : vérification stricte des négations (`negation_markers`), des frais, des montants et de l'absence d'ambiguïté sur les confirmations.
4. **Tests de compréhension utilisateurs** ($n \ge 5$ locuteurs par langue sur `SimuBank CM`, seuil $\ge 95\%$ de compréhension exacte).

## Vérification automatisée
Exécuter :
```powershell
backend\.venv\Scripts\python.exe linguistics\validate_packs.py
```

