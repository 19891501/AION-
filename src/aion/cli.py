"""CLI AION : aion selftest, aion bench."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .bench.arms import BRAS
from .bench.runner import campagne, ecrire
from .budget import Budget, BudgetDepasse
from .cache import Cache
from .ledger import Ledger
from .providers import charger
from .veritas import Evidence, check

try:
    from .audit import auditer, charger_corpus, ecrire_rapport, resume_audit
except ImportError:
    def auditer(*a, **k):
        raise RuntimeError("audit incomplete")
    def charger_corpus(*a, **k):
        raise RuntimeError("audit incomplete")
    def ecrire_rapport(*a, **k):
        raise RuntimeError("audit incomplete")
    def resume_audit(*a, **k):
        return {"testable": False}


def _selftest() -> int:
    led = Ledger()
    led.append("prix_plan_pro", "HYPOTHESIS", justification="observe", source="web")
    ruling = check("le prix est de 29 EUR", [Evidence("stripe", True, age_days=2)])
    from .arbitre import Stake, arbitrer
    a = arbitrer(ruling, Stake(cout=29.0))
    print("selftest OK", ruling.verdict.value, a.decision.value)
    return 0


def _bench(args: argparse.Namespace) -> int:
    provider = charger(args.provider, modele=getattr(args, "modele", None) or "")
    cache = Cache(Path(args.cache)) if getattr(args, "cache", None) else None
    reps = 3 if getattr(args, "micro", False) else int(getattr(args, "reps", 20) or 20)
    max_cas = int(args.max_cas) if getattr(args, "max_cas", None) else None
    appels_max = int(getattr(args, "budget_appels", 800) or 800)
    cout_max = float(getattr(args, "cout_max", 0) or 0)
    graine = int(getattr(args, "graine", 0) or 0)
    total = Budget(appels_max=appels_max * len(BRAS), cout_max_usd=cout_max)
    try:
        rapports = {}
        for nom in BRAS:
            b = Budget(appels_max=appels_max, cout_max_usd=cout_max)
            rapports[nom] = campagne(
                nom, provider,
                repetitions=reps,
                graine=graine,
                entree=args.entree,
                extracteur=args.extracteur,
                cache=cache,
                budget=b,
                max_cas=max_cas,
            )
            total.appels += b.appels
            total.tokens_entree += b.tokens_entree
            total.tokens_sortie += b.tokens_sortie
            total.cout_cumule_usd += b.cout_cumule_usd
    except BudgetDepasse as e:
        print("BUDGET:", e)
        return 2
    out = Path(args.out) if getattr(args, "out", None) else Path("results")
    path = ecrire(rapports, out)
    for nom, r in rapports.items():
        print(f"{nom:10} BAR={r.bar_moyen:.3f} fs={r.resume.get('taux_faux_succes')} appels={r.appels_extraction}")
    print(f"budget_total appels={total.appels} cout_usd~={total.cout_cumule_usd:.4f}")
    print("→", path)
    return 0


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="aion")
    sub = p.add_subparsers(dest="cmd")
    sub.add_parser("selftest")
    b = sub.add_parser("bench")
    b.add_argument("--provider", default="mock")
    b.add_argument("--modele", default="")
    b.add_argument("--entree", default="paraphrase", choices=["drapeaux", "texte", "paraphrase"])
    b.add_argument("--extracteur", default="llm", choices=["lexical", "llm"])
    b.add_argument("--reps", type=int, default=20)
    b.add_argument("--micro", action="store_true")
    b.add_argument("--max-cas", type=int, default=None)
    b.add_argument("--budget-appels", type=int, default=800)
    b.add_argument("--cout-max", type=float, default=0.0)
    b.add_argument("--cache", default=None)
    b.add_argument("--out", default="results")
    b.add_argument("--graine", type=int, default=0)
    args = p.parse_args(argv)
    if args.cmd == "selftest":
        return _selftest()
    if args.cmd == "bench":
        return _bench(args)
    p.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
