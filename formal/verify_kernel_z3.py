#!/usr/bin/env python3
"""Z3 checks for AION Arbiter/ARCHÉ invariants. See formal/INVARIANTS.md."""
from z3 import And, Bool, If, Implies, Int, Not, Or, Real, Solver, sat, unsat

V_PROOF, V_FAIL, V_UNKNOWN, V_CONFLICT = 0, 1, 2, 3
D_EXEC, D_TEST, D_HUMAN, D_NO = 0, 1, 2, 3

def abstract_arbitrer(verdict, reversible, cout, seuil, test_dispo):
    bad_cost = cout < 0
    return If(bad_cost, D_HUMAN,
        If(verdict == V_FAIL, D_NO,
        If(verdict == V_CONFLICT, D_HUMAN,
        If(verdict == V_UNKNOWN, If(test_dispo, D_TEST, D_HUMAN),
        If(Or(Not(reversible), cout > seuil), D_HUMAN, D_EXEC)))))

def check(name, formula):
    s = Solver(); s.add(formula)
    r = s.check()
    ok = r == unsat
    print(f"[{'PASS' if ok else 'FAIL'}] {name}")
    if r == sat: print(' ', s.model())
    return ok

def main():
    v, rev, c, th, td = Int('v'), Bool('rev'), Real('c'), Real('th'), Bool('td')
    d = abstract_arbitrer(v, rev, c, th, td)
    dom = And(v >= 0, v <= 3)
    tests = [
        ('I1 FAIL=>~EXEC', And(dom, v==V_FAIL, d==D_EXEC)),
        ('I2 CONFLICT=>~EXEC', And(dom, v==V_CONFLICT, d==D_EXEC)),
        ('I3 UNKNOWN=>~EXEC', And(dom, v==V_UNKNOWN, d==D_EXEC)),
        ('I4 EXEC=>PROOF', And(dom, d==D_EXEC, v!=V_PROOF)),
        ('I5 PROOF irreversible=>~EXEC', And(dom, v==V_PROOF, Not(rev), c>=0, d==D_EXEC)),
        ('I6 PROOF cost>th=>~EXEC', And(dom, v==V_PROOF, rev, c>th, c>=0, d==D_EXEC)),
        ('I7 PROOF ok=>EXEC', And(dom, v==V_PROOF, rev, c>=0, c<=th, d!=D_EXEC)),
        ('I8 FAIL=>NO', And(dom, v==V_FAIL, c>=0, d!=D_NO)),
        ('DEF Authorized=>conditions', And(dom, d==D_EXEC, Not(And(v==V_PROOF, rev, c>=0, c<=th)))),
    ]
    ok = all(check(n, f) for n, f in tests)
    print('===', 'ALL PASS' if ok else 'FAIL', '===')
    return 0 if ok else 1

if __name__ == '__main__':
    raise SystemExit(main())
