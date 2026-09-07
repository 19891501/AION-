# AION TLA+ — ledger ARCHÉ + gate

## Résultat TLC

```
Model checking completed. No error has been found.
530701 states generated, 20500 distinct states found
depth 5 · MaxEntries=3 · MaxCost=2 · Threshold=1
```

## Invariants prouvés (espace d'états exhaustif borné)

| Invariant | Sens |
|-----------|------|
| TypeOK | Types cohérents |
| InvA3_Justified | Toute entrée a une justification |
| InvA4_ProofNeedsSrc | Statut de preuve ⇒ source ≠ none |
| InvGate_NoBadExec | EXECUTER ⇒ PROOF |
| InvAuth_ImpliesProof | EXECUTER ⇒ PROOF ∧ réversible ∧ coût ≤ seuil |
| InvFailIsNoAction | FAIL ⇒ NO_ACTION |
| InvUnknownNeverExec | UNKNOWN ⇒ ¬EXECUTER |
| InvConflictNeverExec | CONFLICT ⇒ ¬EXECUTER |

Les transitions d'append **illégales** (justification vide, preuve sans source) sont *exclues* de `Next` → l'invariant est structurel + exploré.

## Run

```bash
java -XX:+UseParallelGC -cp formal/tla/tla2tools.jar tlc2.TLC \
  -config formal/tla/AION.cfg formal/tla/AION.tla
```

## Limites

- Borné (MaxEntries, MaxCost) — pas une preuve pour N arbitraire
- Arbitre abstrait (pas le bytecode Python)
- Pas R0–R10, pas extracteur, pas hash cryptographique

Complète Z3 (`formal/verify_kernel_z3.py`) : Z3 = prédicats un coup ; TLA+ = traces ledger + décisions dans le temps.
