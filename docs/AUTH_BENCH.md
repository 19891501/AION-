# AION-AUTH-BENCH

Corpus parallèle au protocole **S2 frozen** : mesure le gate **Veritas → Arbitre** sur preuves structurées + stake.

## Résultat lab (2026-09-04)

```
PASS 23/23
pre-action discovery (vs classic FALSE_EXECUTE): 13/13 = 100%
```

## Lancer

```bash
PYTHONPATH=src python scripts/run_auth_bench.py
pytest tests/test_auth_bench.py -q
```

## Ce que ça prouve

- Oracles Truth (PROOF/FAIL/UNKNOWN/CONFLICT) alignés sur `veritas.check`
- Oracles Auth alignés sur `arbitrer`
- Proportionnalité stake (B5a/B5b)
- Fail-closed NaN (F2 / MARTEAU C-01)
- Sur 13 cas FALSE_EXECUTE classique, AION n'ouvre pas EXECUTER (100%)

## Ce que ça ne prouve pas

- Perception NL, campagne S2 multi-bras, médiation runtime tools (S1)

S2 reste le test confirmatoire pré-enregistré. Ce bench est une expérience séparée.
