# AION — noyau

Kernel de confiance **déterministe** (ARCHÉ + VERITAS + Arbitre + Behavior Engine)
et banc d'essai comportemental **AION-100**.

Thèse testée : *intelligence ≠ comportement*.

## État (0.1.0)

| Verrou | Valeur |
|--------|--------|
| Pré-enregistrement S2 | FROZEN — `d2fc38c0…` |
| Corpus | 20 cas — `dccc6774fc0f2ab7` |
| Audit | TESTABLE |
| Campagnes frontier | **aucune** |

```bash
pip install -e ".[dev]"
aion status && aion selftest && aion audit && aion preenreg
bash scripts/campagne_reelle.sh ollama micro
```

Providers: `mock` `simule` `local` `ollama` `anthropic` `openai` `grok`

## Licence

MIT
