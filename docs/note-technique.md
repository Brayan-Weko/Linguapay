# Note Technique — LinguaPay (SAFINUM Innovate Challenge 2026)

*Document de suivi technique (complété progressivement jusqu'au Sprint 5).*

- **Cahier des charges complet** : `../Cahier_des_Charges_LinguaPay_SAFINUM_2026.pdf`
- **Architecture** : Couche d'adaptation client *Zero-Intrusion* (Extension MV3 + Shadow DOM) découplée du moteur Python FastAPI (`EntityShield` + Pipeline 3 niveaux + Audio Hybride).
- **Limites connues (v1)** : Les textes embarqués dans des images rasterisées (PNG/JPEG sans `alt` ni DOM texte) ne sont pas traduits sans module OCR dédié.

