"""CLI AION : selftest, bench, pipeline, perf, audit, status."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .audit import auditer, charger_corpus, ecrire_rapport, resume_audit
from .bench import comparer, couverture, ecrire
from .bench.cases import CAS, LEDGER_SEED, MONDE
from .ledger import Ledger
from .preenregistrement import charger as charger_pre, empreinte


def _ledger():
    led = Ledger()
    for fait, statut, justification, source in LEDGER_SEED:
        led.append(fait, statut, justification=justification, source=source)
    return led


def _selftest(_args: argparse.Namespace) -> int:
    from .behavior import Situation, selectionner, Action
    from .veritas import check, Evidence, Verdict
    from .arbitre import arbitrer, Stake, Decision

    c = selectionner(Situation("test"), Ledger())
    assert c.action is Action.ANSWER
    r = check("x", [Evidence("s", True)])
    assert r.verdict is Verdict.PROOF
    a = arbitrer(r, Stake(reversible=True, cout=1))
    assert a.decision is Decision.EXECUTER
    print("selftest OK")
    return 0


def _status(_args: argparse.Namespace) -> int:
    pre = charger_pre()
    rapport = auditer(CAS, MONDE, _ledger())
    print(f"version             aion")
    print(f"preenreg            {pre.get('version')} gel={pre.get('date_gel')}")
    print(f"empreinte           {empreinte()[:16]}…")
    print(f"audit corpus        {rapport.verdict}")
    print(f"cas                 {rapport.cas}")
    return 0


def _pipeline(args: argparse.Namespace) -> int:
    from .pipeline import run_pipeline

    evidences = []
    if args.evidence:
        for item in args.evidence:
            if ":" in item:
                src, side = item.rsplit(":", 1)
                evidences.append(
                    {"source": src, "supports": side.lower() in ("pour", "true", "1", "oui")}
                )
            else:
                evidences.append({"source": item, "supports": True})

    flags = {
        "consequence_reelle": args.consequence,
        "premisse_fausse": args.premisse_fausse,
        "ambigu": args.ambigu,
        "hors_domaine": args.hors_domaine,
        "connaissance_datee": args.datee,
        "sources_divergentes": args.divergentes,
    }
    result = run_pipeline(
        question=args.question,
        flags=flags,
        claim=args.claim,
        evidences=evidences or None,
        stake={"cout": args.cout, "reversible": args.reversible} if args.consequence else None,
    )
    if args.json:
        print(json.dumps(result.to_dict(), ensure_ascii=False, indent=2))
    else:
        for step in result.chain:
            print(f"  → {step}")
        print(f"  FINAL: {result.final}")
        if result.behavior:
            print(f"  ({result.behavior.get('motif', '')})")
        if result.veritas:
            print(f"  Veritas: {result.veritas.get('verdict')} — {result.veritas.get('reason')}")
        if result.arbitre:
            print(f"  Arbitre: {result.arbitre.get('decision')} — {result.arbitre.get('motif')}")
        print(f"  {result.principle}")
    return 0


def _perf(args: argparse.Namespace) -> int:
    from .providers import charger
    from .perf import measure_provider

    try:
        provider = charger(args.provider)
    except Exception as exc:
        print(f"FAIL provider: {exc}")
        return 1
    report = measure_provider(provider, n=args.n)
    if args.json:
        print(json.dumps(report.to_dict(), ensure_ascii=False, indent=2))
    else:
        print(f"provider   {report.provider} / {report.modele}")
        print(f"samples    {report.ok}/{report.n} ok  ({report.fail} fail)")
        print(f"p50        {report.p50_ms} ms")
        print(f"p95        {report.p95_ms} ms")
        print(f"mean       {report.mean_ms} ms  [{report.min_ms} – {report.max_ms}]")
    return 0 if report.fail == 0 else 2


def _audit(args: argparse.Namespace) -> int:
    corpus = CAS
    if args.corpus:
        corpus = charger_corpus(args.corpus)
    rapport = auditer(corpus, MONDE, _ledger())
    print(json.dumps(resume_audit(corpus, MONDE, _ledger()), ensure_ascii=False, indent=2))
    if args.out:
        ecrire_rapport(rapport, args.out)
    return 0 if rapport.verdict == "TESTABLE" else 1


def _bench(args: argparse.Namespace) -> int:
    from .providers import charger

    provider = charger(args.provider)
    rapports = comparer(
        provider,
        bras=args.bras or None,
        entree=args.entree,
        extracteur=args.extracteur,
        repetitions=3 if args.micro else 20,
        max_cas=5 if args.micro else None,
    )
    out = Path(args.out) if args.out else Path("results")
    ecrire(rapports, out)
    print(f"écrit → {out}")
    return 0


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="aion")
    sub = p.add_subparsers(dest="cmd", required=True)
    sub.add_parser("selftest", help="verifie kernel + ledger + arbitre")
    sub.add_parser("status", help="etat des verrous")

    pl = sub.add_parser("pipeline", help="INTENTION → Behavior → Veritas → Arbitre")
    pl.add_argument("question")
    pl.add_argument("--claim", default=None)
    pl.add_argument("--evidence", action="append", default=[])
    pl.add_argument("--consequence", action="store_true")
    pl.add_argument("--premisse-fausse", action="store_true")
    pl.add_argument("--ambigu", action="store_true")
    pl.add_argument("--hors-domaine", action="store_true")
    pl.add_argument("--datee", action="store_true")
    pl.add_argument("--divergentes", action="store_true")
    pl.add_argument("--cout", type=float, default=10000.0)
    pl.add_argument("--reversible", action="store_true")
    pl.add_argument("--json", action="store_true")

    pf = sub.add_parser("perf", help="latence provider p50/p95")
    pf.add_argument("--provider", default="local")
    pf.add_argument("-n", type=int, default=5)
    pf.add_argument("--json", action="store_true")

    a = sub.add_parser("audit", help="corpus testable ?")
    a.add_argument("--corpus", default=None)
    a.add_argument("--out", default=None)

    b = sub.add_parser("bench", help="campagne RAW vs SCAFFOLD vs AION")
    b.add_argument("--provider", default="local")
    b.add_argument("--micro", action="store_true")
    b.add_argument("--entree", default="paraphrase")
    b.add_argument("--extracteur", default="lexical")
    b.add_argument("--bras", nargs="*")
    b.add_argument("--out", default="results")

    args = p.parse_args(argv)
    if args.cmd == "selftest":
        return _selftest(args)
    if args.cmd == "status":
        return _status(args)
    if args.cmd == "pipeline":
        return _pipeline(args)
    if args.cmd == "perf":
        return _perf(args)
    if args.cmd == "audit":
        return _audit(args)
    if args.cmd == "bench":
        return _bench(args)
    return 1


if __name__ == "__main__":
    sys.exit(main())
