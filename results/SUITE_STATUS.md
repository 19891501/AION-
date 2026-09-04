# Suite AION — statut 2026-09-04

## Fait

| Étape | Résultat |
|-------|----------|
| Auth-bench | 23/23 |
| Marche 0 drapeaux | AION BAR=1.00 |
| Marche 0 paraphrase+lexical | AION BAR=0.50 |
| Micro simule paraphrase+llm 3 reps | circuit OK, non opposable |
| S2 pré-reg | FROZEN |

## Bloqué

Pas de clé API / Ollama dans le runtime. S2 réel en attente de clé.

```bash
export ANTHROPIC_API_KEY=sk-...
PYTHONPATH=src python scripts/run_micro_s2.py --provider anthropic --reps 5 --max-calls 200 --max-usd 3
```

opposable_s2 seulement si reps≥20 + paraphrase + llm + provider autorisé.
