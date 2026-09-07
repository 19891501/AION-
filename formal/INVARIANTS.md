# AION Kernel — Invariants formels (v0.1)

Vérifiés par `formal/verify_kernel_z3.py` (Z3 SMT).  
Modèle abstrait aligné sur `arbitre.py` / ARCHÉ — **pas** une preuve du bytecode Python.

## Arbiter

| ID | Propriété | Résultat |
|----|----------|----------|
| I1 | FAIL ⇒ ¬EXECUTER | PASS |
| I2 | CONFLICT ⇒ ¬EXECUTER | PASS |
| I3 | UNKNOWN ⇒ ¬EXECUTER | PASS |
| I4 | EXECUTER ⇒ PROOF | PASS |
| I5 | PROOF ∧ ¬reversible ⇒ ¬EXECUTER | PASS |
| I6 | PROOF ∧ cout > seuil ⇒ ¬EXECUTER | PASS |
| I7 | PROOF ∧ reversible ∧ 0≤cout≤seuil ⇒ EXECUTER | PASS |
| I8 | FAIL ⇒ NO_ACTION | PASS |

## Authorization

| ID | Propriété | Résultat |
|----|----------|----------|
| DEF | Authorized ⇒ PROOF ∧ reversible ∧ cout∈[0,seuil] | PASS |

## ARCHÉ (abstrait)

| ID | Propriété | Résultat |
|----|----------|----------|
| A3 | justification vide interdite | PASS |
| A4 | proof-status ∧ source vide illégal | PASS |

## Non couvert (volontairement)

- R0–R10 (table de décision — tests unitaires + exhaustivité flags)
- Extracteur lexical / paraphrase
- Hash chain ledger (candidat TLA+ plus tard)
- Comportement LLM

## Run

```bash
pip install z3-solver
PYTHONPATH=src python formal/verify_kernel_z3.py
```

S2 reste empirique. Ces invariants durcissent le **contrat d'autorisation** déterministe.
