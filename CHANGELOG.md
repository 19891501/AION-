# Changelog

## 0.1.0 — 2026-08-29

### Gelé
- Pré-enregistrement S2 (`preenregistrement.json` v2, empreinte `d2fc38c0…`)
- Corpus 20 cas (hash `dccc6774fc0f2ab7`)
- Protocole : entrée `paraphrase`, extracteur `llm`, 20 répétitions, budget 800

### Ajouté
- Providers : mock, simule, local, ollama, anthropic, openai, grok
- `aion audit` renforcé
- `aion status`, `aion corpus`
- `aion bench --micro`
- Rapport markdown automatique
- Script `scripts/campagne_reelle.sh`

### Limites assumées
- Corpus rédigé par l'auteur → pas de preuve de généralisation
- 0 campagne sur modèle de frontier
- Faille extracteur « bruit de politesse » volontairement non corrigée

### Non inclus
- Nouvelle architecture, multi-agent, GUI
