#!/usr/bin/env python3
"""R4/SIF — preuve bornee de composition (extension verify_kernel_z3)."""
from z3 import And, If, Or, Real, Solver, sat, unsat

D_EXEC, D_HUMAN = 0, 1


def naive_decision(cout, seuil):
    return If(cout > seuil, D_HUMAN, D_EXEC)


def patched_decision(cout, seuil, cum_avant, plafond_global):
    projete = cum_avant + cout
    return If(Or(cout > seuil, projete > plafond_global), D_HUMAN, D_EXEC)


def check(name, formula, expect_sat: bool):
    s = Solver()
    s.add(formula)
    r = s.check()
    ok = (r == sat) if expect_sat else (r == unsat)
    print(f"[{'PASS' if ok else 'FAIL'}] {name}")
    if r == sat:
        print("   contre-exemple:", s.model())
    return ok


def r4_naive_violation_exists(k: int, seuil_val: float, plafond_val: float):
    costs = [Real(f"c{i}") for i in range(k)]
    seuil, plafond = Real("seuil"), Real("plafond")
    all_exec = And(*[naive_decision(c, seuil) == D_EXEC for c in costs])
    all_bounded = And(*[And(c >= 0, c <= seuil) for c in costs])
    formula = And(
        seuil == seuil_val,
        plafond == plafond_val,
        all_bounded,
        all_exec,
        sum(costs) > plafond,
    )
    return formula


def r4_patched_no_violation(k: int, seuil_val: float, plafond_val: float):
    costs = [Real(f"pc{i}") for i in range(k)]
    seuil, plafond = Real("pseuil"), Real("pplafond")
    cum = Real("cum0")
    constraints = [cum == 0, seuil == seuil_val, plafond == plafond_val]
    for i, c in enumerate(costs):
        constraints.append(c >= 0)
        constraints.append(c <= seuil)
        constraints.append(patched_decision(c, seuil, cum, plafond) == D_EXEC)
        next_cum = Real(f"cum{i + 1}")
        constraints.append(next_cum == cum + c)
        cum = next_cum
    formula = And(*constraints, sum(costs) > plafond)
    return formula


def main():
    print("=== R4 composition (naive SAT / patched UNSAT) ===\n")
    ok1 = check(
        "R4 naive k=2 seuil=200 plafond=50 -> violation EXISTS",
        r4_naive_violation_exists(2, 200.0, 50.0),
        True,
    )
    ok2 = check(
        "R4 naive k=10 seuil=200 plafond=200 -> violation EXISTS",
        r4_naive_violation_exists(10, 200.0, 200.0),
        True,
    )
    K = 15
    ok3 = check(
        f"R4 patched k<={K} seuil=200 plafond=200 -> NO violation",
        r4_patched_no_violation(K, 200.0, 200.0),
        False,
    )
    all_ok = ok1 and ok2 and ok3
    print("\n===", "ALL PASS" if all_ok else "ECART", "===")
    return 0 if all_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
