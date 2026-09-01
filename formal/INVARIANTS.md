# AION Kernel — Invariants formels (v0.1)

Verified by `formal/verify_kernel_z3.py` (Z3). Abstract model of Arbiter/ARCHÉ.

| ID | Property | Result |
|----|----------|--------|
| I1 | FAIL ⇒ ¬EXECUTER | PASS |
| I2 | CONFLICT ⇒ ¬EXECUTER | PASS |
| I3 | UNKNOWN ⇒ ¬EXECUTER | PASS |
| I4 | EXECUTER ⇒ PROOF | PASS |
| I5 | PROOF ∧ ¬reversible ⇒ ¬EXECUTER | PASS |
| I6 | PROOF ∧ cost > threshold ⇒ ¬EXECUTER | PASS |
| I7 | PROOF ∧ reversible ∧ cost in range ⇒ EXECUTER | PASS |
| I8 | FAIL ⇒ NO_ACTION | PASS |
| DEF | Authorized ⇒ PROOF ∧ reversible ∧ cost OK | PASS |
| A3/A4 | empty justification / proof without source illegal | PASS |

```bash
PYTHONPATH=src python formal/verify_kernel_z3.py
```
