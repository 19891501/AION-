# Changelog

## 0.1.0 — 2026-08-29

### Gelé
- Pré-enregistrement S2 (`preenregistrement.json` v2, empreinte `d2fc38c0…`)
- Corpus 20 cas (hash `dccc6774fc0f2ab7`)
- Protocole : entrée `paraphrase`, extracteur `llm`, 20 répétitions, budget 800

### Ajouté
- Providers : mock, simule, anthropic, openai, grok
- `aion audit` renforcé (verdict TESTABLE/NON_TESTABLE, rapport hashable)
- `aion status` — état des verrous
- `aion bench --micro` — validation circuit (5 cas × 3 reps)
- Rapport markdown automatique à côté de chaque JSON de campagne
- Script `scripts/campagne_reelle.sh` avec contrôles pré-vol
- Suite MARTEAU (attaques + failles verrouillées)

### Limites assumées
- Corpus rédigé par l'auteur → pas de preuve de généralisation
- 0 campagne sur modèle réel à la date de release
- Faille extracteur « bruit de politesse » volontairement non corrigée (test de verrouillage)

### Non inclus (volontairement)
- Nouvelle architecture
- Multi-agent
- Interface graphique
