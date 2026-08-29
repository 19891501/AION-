"""CLI AION : `aion selftest`, `aion bench`, `aion lois`."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .arbitre import Stake, arbitrer
from .audit import auditer, charger_corpus, ecrire_rapport, resume_audit
from .bench import comparer, couverture, ecrire
from .bench.cases import CAS, LEDGER_SEED, MONDE
from .budget import Budget, BudgetDepasse
from .cache import Cache
from .constitution import ARCHE, CONSTITUTION
from .euros import charger as charger_decisions
from .euros import rejouer, sensibilite
from .ledger import Ledger
from .preenregistrement import charger as charger_pre
from .preenregistrement import decision, empreinte, verifier
from .providers import charger
from .veritas import Evidence, check


def _selftest() -> int:
    led = Ledger()
    led.append("prix_plan_pro", "HYPOTHESIS", justification="observe sur la page publique", source="web")
    led.revise("prix_plan_pro", "VERIFIED", justification="confirme par facture", source="stripe")
    ruling = check("le prix est de 29 EUR", [Evidence("stripe", True, age_days=2)])
    arb = arbitrer(ruling, Stake(reversible=True, cout=0.0))
    ok = led.verify_chain() and ruling.is_proof and arb.decision.value == "EXECUTER"
    print(f"chaine ledger        : {'OK' if led.verify_chain() else 'CORROMPUE'}")
    print(f"verdict veritas      : {ruling.verdict.value} ({ruling.reason})")
    print(f"arbitrage            : {arb.decision.value} ({arb.motif})")
    print(f"selftest             : {'PASS' if ok else 'FAIL'}")
    return 0 if ok else 1


def _bench(args: argparse.Namespace) -> int:
    kwargs = {}
    if args.modele:
        kwargs["modele"] = args.modele
    provider = charger(args.provider, **kwargs)

    cache = Cache(args.cache) if args.cache else None
    budget = Budget(args.budget_appels, args.cout_appel) if args.budget_appels else None
    max_cas = args.max_cas if getattr(args, "max_cas", 0) else None
    cas_override = None
    if getattr(args, "corpus", ""):
        from .audit import charger_corpus
        from .bench.cases import Cas
        from dataclasses import replace
        # Adapter CasExterne -> objet compatible (id, famille, situation, attendu, pourquoi)
        bruts = charger_corpus(args.corpus)
        from .behavior import Situation
        from .bench.cases import Cas as CasBench
        cas_override = [
            CasBench(
                id=c.id,
                famille=c.famille,
                situation=Situation(c.texte),
                attendu=c.attendu,
                pourquoi=c.pourquoi,
            )
            for c in bruts
        ]
        print(f"corpus externe chargé: {len(cas_override)} cas depuis {args.corpus}")

    if getattr(args, "micro", False):
        # Micro-campagne : circuit check, non opposable
        if args.reps >= 20 and not max_cas:
            args.reps = 3
        max_cas = max_cas or 5
        print("MODE MICRO-CAMPAGNE — résultat non opposable au pré-enregistrement S2")
        print(f"  cas limités à {max_cas}, répétitions = {args.reps}")
    try:
        rapports = comparer(
            provider, repetitions=args.reps, graine=args.graine, entree=args.entree,
            extracteur=args.extracteur, cache=cache, budget=budget, max_cas=max_cas,
            cas_override=cas_override,
        )
    except BudgetDepasse as exc:
        print(f"ARRET: {exc}")
        return 2
    chemin = ecrire(rapports, args.out)
    cov = couverture()
    print(f"cas: {sum(cov.values())}/100 vises — {cov}")
    print(f"entree: {args.entree} — extracteur: {args.extracteur}")
    print(f"{'bras':<9}{'BAR moy':>9}{'ecart':>8}{'min':>6}{'max':>6}{'drapeaux':>10}{'20/20':>7}{'parse KO':>10}")
    for nom, r in rapports.items():
        print(
            f"{nom:<9}{r.bar_moyen:>9.3f}{r.bar_ecart_type:>8.3f}{r.bar_min:>6.2f}{r.bar_max:>6.2f}"
            f"{r.drapeaux_exacts:>10.2f}{r.pass_20_controles!s:>7}{r.echecs_parse:>10}"
        )
    if budget:
        print(f"appels consommes: {budget.appels}/{budget.appels_max} — cout estime {budget.cout_estime():.2f}")
    if cache:
        print(f"cache: {cache.hits} hits / {cache.hits + cache.miss} lectures (rejouabilite, PAS robustesse)")
    if args.provider in ("mock", "simule", "local"):
        print(
            f"\nAVERTISSEMENT provider={args.provider} : "
            "aucun chiffre ci-dessus n'est un résultat réel."
        )
    print(f"\nrapport écrit: {chemin}")
    return 0


def _audit(args: argparse.Namespace) -> int:
    led = Ledger()
    for fait, statut, justification, source in LEDGER_SEED:
        led.append(fait, statut, justification=justification, source=source)
    corpus = charger_corpus(args.fichier) if args.fichier else CAS
    rapport = auditer(corpus, MONDE, led)

    if args.json:
        print(json.dumps(rapport.to_dict(), ensure_ascii=False, indent=2))
    else:
        print(f"VERDICT     : {rapport.verdict}")
        print(f"corpus      : {rapport.cas} cas — hash {rapport.corpus_hash}")
        print(f"familles    : {rapport.familles}")
        print(f"actions     : {rapport.actions_attendues}")
        print(
            f"fragilité   : moyenne={rapport.fragilite_moyenne:.2f}  "
            f"un seul mot={rapport.part_un_seul_mot:.0%}  "
            f"sans porteur={rapport.part_sans_porteur:.0%}"
        )
        print(f"cas 1 mot   : {rapport.cas_a_un_seul_mot}")
        print(f"cas 0 mot   : {rapport.cas_sans_mot_porteur}")
        for b in rapport.bloquants:
            print(f"  BLOQUANT  [{b['code']}] {b['portee']} — {b['message']}")
        for a in rapport.alertes:
            print(f"  ALERTE    [{a['code']}] {a['portee']} — {a['message']}")
        print(f"empreinte rapport : {rapport.empreinte()[:16]}…")

    if args.out:
        chemin = ecrire_rapport(rapport, args.out)
        if not args.json:
            print(f"rapport écrit : {chemin}")

    return 0 if rapport.testable else 1


def _preenreg(args: argparse.Namespace) -> int:
    pre = charger_pre()
    if not args.verifier:
        print(f"pre-enregistrement v{pre['version']} — gele le {pre['date_gel']}")
        print(f"empreinte: {empreinte()}")
        print(f"entree de reference: {pre['entree_de_reference']}")
        for cle, val in pre["criteres"].items():
            print(f"  {cle:<45}{val}")
        for cle, val in pre["decision"].items():
            print(f"  [{cle}] {val}")
        return 0

    campagne = json.loads(Path(args.verifier).read_text(encoding="utf-8"))
    verdicts = verifier(campagne, pre)
    for v in verdicts:
        print(f"  {'OK  ' if v.conforme else 'NON '} {v.critere:<24}{v.detail}")
    conforme = all(v.conforme for v in verdicts)
    verdict_decision = decision(campagne, pre)
    print(f"\nconformite: {'CONFORME' if conforme else 'NON CONFORME'}")
    print(f"decision  : {verdict_decision}"
          + ("" if conforme else "  (non opposable : la campagne ne remplit pas ses conditions)"))
    return 0 if conforme else 1


def _euros(args: argparse.Namespace) -> int:
    decisions = charger_decisions(args.fichier)
    b = rejouer(decisions, cout_verification=args.cout_verification, rattrapage=args.rattrapage)
    r = b.resume()
    print(f"decisions rejouees   : {r['decisions']}")
    print(f"executions / verifs  : {r['executions']} / {r['verifications']}")
    print(f"perte evitee         : {r['perte_evitee']:.2f} EUR "
          f"(hypothese de rattrapage {args.rattrapage})")
    print(f"perte subie          : {r['perte_subie']:.2f} EUR")
    print(f"gain manque          : {r['gain_manque']:.2f} EUR (cout d'opportunite de l'hesitation)")
    print(f"friction             : {r['friction']:.2f} EUR "
          f"({r['verifications']} verifs x {args.cout_verification:g} EUR)")
    print(f"RATIO DE PRUDENCE    : {r['ratio_de_prudence']}")
    print(f"seuil d'equilibre    : {r['seuil_equilibre_par_verification']:.2f} EUR par verification")
    print("  (au-dela de ce cout, le kernel ne vaut plus rien)")

    print("\nsensibilite — ratio selon les deux hypotheses")
    lignes = sensibilite(decisions)
    entetes = [k for k in lignes[0] if k != "rattrapage"]
    print(f"{'rattrapage':<12}" + "".join(f"{e:>10}" for e in entetes))
    for ligne in lignes:
        print(f"{ligne['rattrapage']:<12}" + "".join(f"{ligne[e]:>10}" for e in entetes))

    if len(decisions) < 30:
        print(f"\nNON CONFORME: {len(decisions)} decisions, minimum 30 (preenregistrement-euros.json)")
        return 1
    return 0


def _lois() -> int:
    for loi in CONSTITUTION + ARCHE:
        print(f"{loi.code}  {loi.enonce}")
    return 0


def _status() -> int:
    """État des verrous du projet (pré-enregistrement, audit, tests)."""
    from .audit import auditer
    from .bench.cases import CAS, LEDGER_SEED, MONDE
    from .preenregistrement import charger as charger_pre, empreinte

    pre = charger_pre()
    print("=== AION — état des verrous ===")
    print(f"pré-enregistrement  v{pre['version']}  gelé le {pre['date_gel']}")
    print(f"  empreinte         {empreinte()}")
    print(f"  entrée référence  {pre['entree_de_reference']}")
    print(f"  écart AION-RAW    ≥ {pre['criteres']['ecart_aion_raw_minimum']}")
    print(f"  budget appels max {pre['criteres']['appels_maximum_par_campagne']}")
    print(f"  corpus hash       {pre.get('corpus_hash_ids', '?')}")
    print()

    led = Ledger()
    for fait, statut, justification, source in LEDGER_SEED:
        led.append(fait, statut, justification=justification, source=source)
    rapport = auditer(CAS, MONDE, led)
    print(f"audit corpus        {rapport.verdict}")
    print(f"  cas               {rapport.cas}")
    print(f"  hash corpus       {rapport.corpus_hash}")
    print(f"  un seul mot       {rapport.part_un_seul_mot:.0%}")
    print(f"  bloquants         {len(rapport.bloquants)}")
    print(f"  alertes           {len(rapport.alertes)}")
    print()

    print("prochaine étape     micro-campagne réelle (clé API requise)")
    print("  commande type     aion bench --provider anthropic --micro \\")
    print("                      --entree paraphrase --extracteur llm \\")
    print("                      --budget-appels 40 --out results/micro.json")
    return 0 if rapport.testable else 1



def _corpus(args: argparse.Namespace) -> int:
    """Stats / validation d'un corpus externe avant intégration."""
    from .corpus import stats, valider_externe

    if args.action == "stats":
        s = stats(args.fichier)
        print(f"fichier   : {s['fichier']}")
        print(f"total     : {s['total']}  (vides: {s['n_vides']})")
        print(f"familles  : {s['familles']}")
        print(f"actions   : {s['actions']}")
        if s["vides"]:
            print(f"slots vides: {s['vides']}")
        return 0

    # validate
    r = valider_externe(args.fichier)
    print(f"VERDICT   : {r['verdict']}")
    print(f"stats     : {r['stats']['total']} cas, vides={r['stats']['n_vides']}")
    if r.get("corpus_hash"):
        print(f"hash      : {r['corpus_hash']}")
    for e in r["erreurs"]:
        print(f"  ERREUR  {e}")
    for a in r["alertes"]:
        print(f"  ALERTE  {a}")
    if r["ok"]:
        print("→ structure OK. Si rédigé par l'équipe projet, garder corpus_externe=false.")
    else:
        print("→ refusé. Corriger avant toute campagne.")
    return 0 if r["ok"] else 1



def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="aion", description="Noyau AION")
    sub = p.add_subparsers(dest="cmd", required=True)
    sub.add_parser("selftest", help="verifie kernel + ledger + arbitre")
    sub.add_parser("status", help="etat des verrous (preenreg, audit, corpus)")
    co = sub.add_parser("corpus", help="stats / validation corpus externe")
    co.add_argument("action", choices=["stats", "validate"], help="stats ou validate")
    co.add_argument("--fichier", required=True, help="chemin JSON corpus")
    sub.add_parser("lois", help="affiche la constitution et les lois ARCHE")
    pr = sub.add_parser("preenreg", help="criteres geles avant campagne / verification")
    pr.add_argument("--verifier", default="", help="rapport de campagne JSON a confronter aux criteres")
    e = sub.add_parser("euros", help="rejouer le kernel sur des decisions passees, compter en euros")
    e.add_argument("--fichier", default="decisions-gabarit.json")
    e.add_argument("--cout-verification", type=float, default=4.0, dest="cout_verification")
    e.add_argument("--rattrapage", type=float, default=0.7)
    a = sub.add_parser("audit", help="le corpus de cas est-il testable ?")
    a.add_argument("--fichier", default="", help="corpus externe JSON (défaut: banc interne)")
    a.add_argument("--json", action="store_true", help="sortie JSON brute")
    a.add_argument("--out", default="", help="écrire le rapport JSON (hashable)")
    b = sub.add_parser("bench", help="campagne AION-100 (RAW vs SCAFFOLD vs AION)")
    b.add_argument(
        "--provider",
        default="mock",
        choices=["mock", "simule", "local", "ollama", "anthropic", "openai", "grok"],
        help="mock/simule/ollama = local ; anthropic/openai/grok = cloud",
    )
    b.add_argument("--modele", default="", help="nom du modèle (sinon valeur par défaut du provider)")
    b.add_argument("--entree", default="drapeaux", choices=["drapeaux", "texte", "paraphrase"],
                   help="drapeaux = poses a la main ; texte/paraphrase = derives par l'extracteur")
    b.add_argument("--extracteur", default="lexical", choices=["lexical", "llm"],
                   help="lexical = regles ; llm = drapeaux lus par le modele")
    b.add_argument("--cache", default="", help="dossier de cache des reponses modele (rejouabilite)")
    b.add_argument("--budget-appels", type=int, default=0, dest="budget_appels",
                   help="arret avant depassement (0 = pas de garde-fou)")
    b.add_argument("--cout-appel", type=float, default=0.0, dest="cout_appel")
    b.add_argument("--reps", type=int, default=20)
    b.add_argument("--graine", type=int, default=0)
    b.add_argument("--max-cas", type=int, default=0, dest="max_cas",
                   help="limiter le nombre de cas (micro-campagne)")
    b.add_argument("--micro", action="store_true",
                   help="raccourci: 5 cas × 3 reps, non opposable (validation circuit)")
    b.add_argument("--corpus", default="", help="corpus JSON externe (sinon banc interne)")
    b.add_argument("--out", default="results")

    args = p.parse_args(argv)
    if args.cmd == "selftest":
        return _selftest()
    if args.cmd == "status":
        return _status()
    if args.cmd == "corpus":
        return _corpus(args)
    if args.cmd == "lois":
        return _lois()
    if args.cmd == "audit":
        return _audit(args)
    if args.cmd == "preenreg":
        return _preenreg(args)
    if args.cmd == "euros":
        return _euros(args)
    return _bench(args)


if __name__ == "__main__":
    sys.exit(main())
