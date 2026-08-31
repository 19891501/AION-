# AION Decision Theater

Démo immersive du kernel de confiance.

## Ouvrir

- Local : `web/static/theater.html` (double-clic ou serveur statique)
- API : `GET /` sert le theater en priorité
- Render : https://aion-3.onrender.com/ (après redeploy)

## Ce que ça montre

1. **BAR** RAW 65% · SCAFFOLD 74% · AION 86% (signal affiché — à valider sous protocole S2)
2. Pipeline animé : INTENTION → BEHAVIOR → VERITAS → ARBITRE → AUTORISATION
3. Face-à-face **agent classique** (LLM→outil→act) vs **AION** (preuve→autoriser)
4. Scénarios : virement 10k€, suppression, prémisse fausse, hors périmètre, question simple

## Principe

> La preuve décide, pas l'intention.

Le kernel est déterministe (R0–R10). Le theater simule le même flux côté client pour une démo sans latence API.
