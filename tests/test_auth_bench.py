"""CI: corpus AION-AUTH-BENCH doit matcher Veritas+Arbitre."""
from __future__ import annotations

import json
from pathlib import Path

from aion.arbitre import Decision, Stake, arbitrer
from aion.veritas import Evidence, check

CORPUS = Path(__file__).resolve().parents[1] / "corpus" / "bench_auth_cases.json"


def test_auth_bench_all_oracles():
    data = json.loads(CORPUS.read_text(encoding="utf-8"))
    fails = []
    pre_hits = pre_tot = 0
    for c in data["cases"]:
        evs = [
            Evidence(
                str(e["source"]),
                bool(e["supports"]),
                int(e.get("age_days") or 0),
                bool(e.get("trusted", True)),
            )
            for e in c.get("evidences") or []
        ]
        ruling = check(c["claim"], evs)
        st = c["stake"]
        cout = float("nan") if st.get("cout") is None else float(st["cout"])
        stake = Stake(
            bool(st.get("reversible", True)),
            cout,
            float(st.get("seuil_humain", 50)),
            bool(st.get("test_disponible", True)),
            int(st.get("echecs_precedents") or 0),
        )
        arb = arbitrer(ruling, stake)
        if ruling.verdict.value != c["oracle_veritas"] or arb.decision.value != c["oracle_arbitre"]:
            fails.append(c["id"])
        if c.get("classic_risk") == "FALSE_EXECUTE":
            pre_tot += 1
            if arb.decision is not Decision.EXECUTER:
                pre_hits += 1
    assert not fails, f"oracle mismatch: {fails}"
    assert pre_tot == 0 or pre_hits == pre_tot
