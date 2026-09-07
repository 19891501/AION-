#!/usr/bin/env python3
"""Équivalence CPython arbitrer() ↔ modèle abstrait Z3 (avec isfinite)."""
from __future__ import annotations

import math
from itertools import product

from aion.arbitre import Decision, Stake, arbitrer
from aion.veritas import Ruling, Verdict

V_PROOF, V_FAIL, V_UNKNOWN, V_CONFLICT = 0, 1, 2, 3
D_EXEC, D_TEST, D_HUMAN, D_NO = 0, 1, 2, 3

VERDICT_MAP = {
    Verdict.PROOF: V_PROOF,
    Verdict.FAIL: V_FAIL,
    Verdict.UNKNOWN: V_UNKNOWN,
    Verdict.CONFLICT: V_CONFLICT,
}
INT_TO_DEC = {
    D_EXEC: Decision.EXECUTER,
    D_TEST: Decision.TESTER,
    D_HUMAN: Decision.DEMANDER_HUMAIN,
    D_NO: Decision.NO_ACTION,
}


def abstract_arbitrer_aligned(verdict: int, reversible: bool, cout: float, seuil: float, test_dispo: bool) -> int:
    """Aligné sur arbitre.py : non-fini ou < 0 → HUMAN en premier."""
    if not math.isfinite(cout) or cout < 0:
        return D_HUMAN
    if verdict == V_FAIL:
        return D_NO
    if verdict == V_CONFLICT:
        return D_HUMAN
    if verdict == V_UNKNOWN:
        return D_TEST if test_dispo else D_HUMAN
    if (not reversible) or (cout > seuil):
        return D_HUMAN
    return D_EXEC


def main() -> int:
    verdicts = list(Verdict)
    grid = product(
        verdicts,
        [True, False],
        [-1.0, 0.0, 1.0, 50.0, 50.0001, 100.0, float("nan"), float("inf"), float("-inf")],
        [0.0, 50.0, 100.0],
        [True, False],
    )
    mismatches = []
    n = 0
    for v, rev, c, s, td in grid:
        n += 1
        py = arbitrer(Ruling(verdict=v, reason="eq"), Stake(reversible=rev, cout=c, seuil_humain=s, test_disponible=td)).decision
        ab = INT_TO_DEC[abstract_arbitrer_aligned(VERDICT_MAP[v], rev, c, s, td)]
        if py != ab:
            mismatches.append((v.value, rev, c, s, td, py.value, ab.value))
    print(f"checked={n} mismatches={len(mismatches)}")
    for m in mismatches[:20]:
        print(" ", m)
    if mismatches:
        return 1
    print("EQUIVALENCE OK: CPython arbitrer == abstract model (isfinite-aligned)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
