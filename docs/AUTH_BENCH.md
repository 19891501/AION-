# AION-AUTH-BENCH

Corpus parallèle au protocole **S2 frozen** : mesure le gate **Veritas → Arbitre** sur preuves structurées + stake.

## Résultat lab (2026-09-04)

```
PASS 23/23
pre-action discovery (vs classic FALSE_EXECUTE): 13/13 = 100%
```

## Lancer

```bash
# depuis la racine monorepo / artifacts
PYTHONPATH=src python run_auth_bench.py
# ou
PYTHONPATH=aion/src python run_auth_bench.py
```

## Ce que ça prouve

- Oracles Truth (PROOF/FAIL/UNKNOWN/CONFLICT) alignés sur `veritas.check`
- Oracles Auth (EXECUTER/TESTER/HUMAN/NO_ACTION/ABANDONNER) alignés sur `arbitrer`
- Proportionnalité stake (B5a/B5b)
- Fail-closed NaN (F2 / MARTEAU C-01)
- Sur les 13 cas où un agent classique risque un faux exécuter, AION n'ouvre pas EXECUTER

## Ce que ça ne prouve pas

- Perception langage naturel (lexical / paraphrase)
- Campagne S2 multi-bras RAW/SCAFFOLD/AION
- Runtime médiation obligatoire devant tools (S1)
- Coût/latence LLM

## Fichiers

| Path | Rôle |
|------|------|
| `corpus/bench_auth_cases.json` | 23 cas + oracles |
| `scripts/run_auth_bench.py` | Runner |
| `results/results_auth_bench.json` | Dernier rapport |

S2 reste le test confirmatoire pré-enregistré. Ce bench est une **expérience séparée** sur le contrat d'autorisation.
