"""CLI AION : aion selftest, aion bench, aion lois."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .arbitre import Stake, arbitrer
from .bench import comparer, couverture, ecrire
from .bench.cases import CAS, LEDGER_SEED, MONDE
from .budget import Budget, BudgetDepasse
from .cache import Cache
from .constitution import ARCHE, CONSTITUTION
from .ledger import Ledger
from .preenregistrement import charger as charger_pre
from .preenregistrement import decision, empreinte, verifier
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
    led.revise("prix_plan_pro", "VERIFIED", justification="confirme", source="stripe")
    ruling = check("le prix est de 29 EUR", [Evidence("stripe", True, age_days=2)])
    from .arbitre import arbitrer as arb
    a = arb(ruling, Stake(cout=29.0))
    print("selftest OK", ruling.verdict.value, a.decision.value)
    return 0


def _bench(args: argparse.Namespace) -> int:
    provider = charger(args.provider, modele=getattr(args, "modele", None) or "")
    budget = Budget(
        appels_max=int(getattr(args, "budget_appels", 800) or 800),
        cout_max_usd=float(getattr(args, "cout_max", 0) or 0),
    )
    cache = Cache(Path(args.cache)) if getattr(args, "cache", None) else None
    reps = 3 if getattr(args, "micro", False) else int(getattr(args, "reps", 20) or 20)
    max_cas = int(args.max_cas) if getattr(args, "max_cas", None) else None
    try:
        rapports = comparer(
            provider,
            repetitions=reps,
            graine=int(getattr(args, "graine", 0) or 0),
            entree=args.entree,
            extracteur=args.extracteur,
            cache=cache,
            budget=budget,
            max_cas=max_cas,
        )
    except BudgetDepasse as e:
        print("BUDGET:", e)
        return 2
    out = Path(args.out) if getattr(args, "out", None) else Path("results")
    path = ecrire(rapports, out)
    for nom, r in rapports.items():
        print(f"{nom:10} BAR={r.bar_moyen:.3f} fs={r.resume.get('taux_faux_succes')} appels={r.appels_extraction}")
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
