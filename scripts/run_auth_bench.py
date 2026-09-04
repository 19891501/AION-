#!/usr/bin/env python3
"""Runner minimal AION-AUTH-BENCH — Veritas + Arbitre vs oracles."""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT.parent / "src"))

from aion.arbitre import Decision, Stake, arbitrer  # noqa: E402
from aion.veritas import Evidence, check  # noqa: E402

CORPUS = ROOT.parent / "corpus" / "bench_auth_cases.json"


def stake_from(d: dict) -> Stake:
    cout = d.get("cout")
    c = float("nan") if cout is None else float(cout)
    return Stake(
        reversible=bool(d.get("reversible", True)),
        cout=c,
        seuil_humain=float(d.get("seuil_humain", 50)),
        test_disponible=bool(d.get("test_disponible", True)),
        echecs_precedents=int(d.get("echecs_precedents") or 0),
    )


def main() -> int:
    data = json.loads(CORPUS.read_text(encoding="utf-8"))
    cases = data["cases"]
    ok = fail = 0
    rows = []
    pre_action_hits = pre_action_total = 0
    for c in cases:
        evs = [
            Evidence(
                source=str(e["source"]),
                supports=bool(e["supports"]),
                age_days=int(e.get("age_days") or 0),
                trusted=bool(e.get("trusted", True)),
            )
            for e in c.get("evidences") or []
        ]
        ruling = check(c["claim"], evs)
        arb = arbitrer(ruling, stake_from(c["stake"]))
        v_ok = ruling.verdict.value == c["oracle_veritas"]
        d_ok = arb.decision.value == c["oracle_arbitre"]
        passed = v_ok and d_ok
        ok += int(passed)
        fail += int(not passed)
        if c.get("classic_risk") == "FALSE_EXECUTE":
            pre_action_total += 1
            if arb.decision is not Decision.EXECUTER:
                pre_action_hits += 1
        rows.append({
            "id": c["id"], "pass": passed,
            "V_star": c["oracle_veritas"], "V": ruling.verdict.value,
            "D_star": c["oracle_arbitre"], "D": arb.decision.value,
            "reason": arb.motif, "classic_risk": c.get("classic_risk"),
        })
    print(f"AION-AUTH-BENCH  cases={len(cases)}")
    print(f"PASS {ok}/{len(cases)}  FAIL {fail}")
    if pre_action_total:
        rate = pre_action_hits / pre_action_total
        print(f"pre-action discovery (vs FALSE_EXECUTE classic): {pre_action_hits}/{pre_action_total} = {rate:.0%}")
    print()
    print(f"{'id':4} {'ok':3} {'V*':10} {'V':10} {'D*':18} {'D':18}")
    for r in rows:
        mark = "✓" if r["pass"] else "✗"
        print(f"{r['id']:4} {mark:3} {r['V_star']:10} {r['V']:10} {r['D_star']:18} {r['D']:18}")
    out = ROOT.parent / "results" / "results_auth_bench.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps({
        "corpus": data.get("name"), "version": data.get("version"),
        "pass": ok, "fail": fail, "total": len(cases),
        "pre_action_discovery": {
            "hits": pre_action_hits, "total": pre_action_total,
            "rate": (pre_action_hits / pre_action_total) if pre_action_total else None,
        },
        "rows": rows,
    }, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n→ {out}")
    return 0 if fail == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
