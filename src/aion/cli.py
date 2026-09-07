"""CLI AION : `aion selftest`, `aion bench`, `aion lois`."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .arbitre import Stake, arbitrer
try:
    from .audit import auditer, charger_corpus, ecrire_rapport, resume_audit
except ImportError:  # versions partielles du repo
    def auditer(*a, **k):
        raise RuntimeError("audit module incomplete")
    def charger_corpus(*a, **k):
        raise RuntimeError("audit module incomplete")
    def ecrire_rapport(*a, **k):
        raise RuntimeError("audit module incomplete")
    def resume_audit(*a, **k):
        raise RuntimeError("audit module incomplete")
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
    budget = None
    if args.budget_appels or getattr(args, "cout_max", 0):
        budget = Budget(
            appels_max=args.budget_appels or 100_000,
            cout_max_usd=getattr(args, "cout_max", 0) or 0.0,
            cout_par_appel=args.cout_appel,
            modele=args.modele or "",
        )
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
        r = budget.resume()
        print(f"appels: {r['appels']}/{r['appels_max']}  tokens in/out: {r['tokens_entree']}/{r['tokens_sortie']}")
        print(f"cout estime: ${r['cout_estime']:.4f}" + (f" / max ${r['cout_max_usd']:.2f}" if r['cout_max_usd'] else ""))
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



def _pipeline(args: argparse.Namespace) -> int:
    """Chaîne INTENTION → Behavior → Veritas → Arbitre."""
    from .pipeline import run_pipeline
    import json

    evidences = []
    if args.evidence:
        for item in args.evidence:
            # format source:pour|contre
            if ":" in item:
                src, side = item.rsplit(":", 1)
                evidences.append({"source": src, "supports": side.lower() in ("pour", "true", "1", "oui")})
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
        print(result.to_dict() and __import__("json").dumps(result.to_dict(), ensure_ascii=False, indent=2))
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
    """Latence provider (p50/p95) — distinct du BAR."""
    from .providers import charger
    from .perf import measure_provider
    import json

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


def _offline(args: argparse.Namespace) -> int:
    """Serveur offline compatible Ollama — zéro cloud."""
    from .providers.offline_mcp import servir, OfflineMCPProvider
    if args.cmd_offline == "serve":
        host, port = args.host, args.port
        print(f"offline-mcp écoute sur http://{host}:{port}")
        print("  compatible: aion bench --provider ollama")
        print("  ou:         aion bench --provider offline")
        print("Ctrl+C pour arrêter.")
        try:
            servir(host=host, port=port, bloquant=True)
        except KeyboardInterrupt:
            print("\narrêt.")
        return 0
    if args.cmd_offline == "ping":
        p = OfflineMCPProvider()
        r = p.complete("Envoie le virement de 10000 euros", system="Tu dois choisir UNE action parmi : ANSWER, ASK, SEARCH, VERIFY, COMPARE, CLARIFY, WAIT, EXPERIMENT, REFUSE, DEFER. Reponds par le seul mot-cle.")
        print(r.texte, r.modele)
        return 0
    print("usage: aion offline serve|ping")
    return 1


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="aion", description="Noyau AION")
    sub = p.add_subparsers(dest="cmd", required=True)
    off = sub.add_parser("offline", help="remplace Ollama/cloud en local (MCP offline)")
    off_sub = off.add_subparsers(dest="cmd_offline")
    off_serve = off_sub.add_parser("serve", help="API compatible Ollama sur :11434")
    off_serve.add_argument("--host", default="127.0.0.1")
    off_serve.add_argument("--port", type=int, default=11434)
    off_sub.add_parser("ping", help="test extraction/scaffold offline")
    sub.add_parser("mcp", help="serveur MCP stdio (aion_propose seulement, aucun outil d'effet)")
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
    pl = sub.add_parser("pipeline", help="chaine INTENTION → Behavior → Veritas → Arbitre")
    pl.add_argument("question", help="intention / demande utilisateur")
    pl.add_argument("--claim", default=None, help="affirmation a prouver (Veritas)")
    pl.add_argument("--evidence", action="append", default=[], help="source:pour|contre (repeatable)")
    pl.add_argument("--consequence", action="store_true", help="consequence reelle")
    pl.add_argument("--premisse-fausse", action="store_true")
    pl.add_argument("--ambigu", action="store_true")
    pl.add_argument("--hors-domaine", action="store_true")
    pl.add_argument("--datee", action="store_true")
    pl.add_argument("--divergentes", action="store_true")
    pl.add_argument("--cout", type=float, default=10000.0)
    pl.add_argument("--reversible", action="store_true")
    pl.add_argument("--json", action="store_true")
    pf = sub.add_parser("perf", help="latence provider p50/p95 (Ollama, local, ...)")
    pf.add_argument("--provider", default="local", help="local|ollama|mock|simule|...")
    pf.add_argument("-n", type=int, default=5, help="nombre d'echantillons")
    pf.add_argument("--json", action="store_true")
    b = sub.add_parser("bench", help="campagne AION-100 (RAW vs SCAFFOLD vs AION)")
    b.add_argument(
        "--provider",
        default="mock",
        choices=["mock", "simule", "local", "offline", "mcp", "ollama", "anthropic", "openai", "grok"],
        help="mock/simule/ollama = local ; anthropic/openai/grok = cloud",
    )
    b.add_argument("--modele", default="", help="nom du modèle (sinon valeur par défaut du provider)")
    b.add_argument("--entree", default="drapeaux", choices=["drapeaux", "texte", "paraphrase"],
                   help="drapeaux = poses a la main ; texte/paraphrase = derives par l'extracteur")
    b.add_argument("--extracteur", default="lexical", choices=["lexical", "lexical_v2", "llm"],
                   help="lexical = regles ; llm = drapeaux lus par le modele")
    b.add_argument("--cache", default="", help="dossier de cache des reponses modele (rejouabilite)")
    b.add_argument("--budget-appels", type=int, default=0, dest="budget_appels",
                   help="arret avant depassement (0 = pas de garde-fou)")
    b.add_argument("--cout-appel", type=float, default=0.0, dest="cout_appel")
    b.add_argument("--cout-max", type=float, default=0.0, dest="cout_max",
                   help="plafond USD estimé (tokens) — 0 = désactivé")
    b.add_argument("--reps", type=int, default=20)
    b.add_argument("--graine", type=int, default=0)
    b.add_argument("--max-cas", type=int, default=0, dest="max_cas",
                   help="limiter le nombre de cas (micro-campagne)")
    b.add_argument("--micro", action="store_true",
                   help="raccourci: 5 cas × 3 reps, non opposable (validation circuit)")
    b.add_argument("--corpus", default="", help="corpus JSON externe (sinon banc interne)")
    b.add_argument("--out", default="results")

    args = p.parse_args(argv)
    if args.cmd == "offline":
        return _offline(args)
    if args.cmd == "mcp":
        from .runtime import serve_mcp_stdio
        return serve_mcp_stdio()
    if args.cmd == "selftest":
        return _selftest()
    if args.cmd == "status":
        return _status()
    if args.cmd == "corpus":
        return _corpus(args)
    if args.cmd == "lois":
        return _lois()
    if args.cmd == "pipeline":
        return _pipeline(args)
    if args.cmd == "perf":
        return _perf(args)
    if args.cmd == "audit":
        return _audit(args)
    if args.cmd == "preenreg":
        return _preenreg(args)
    if args.cmd == "euros":
        return _euros(args)
    return _bench(args)


if __name__ == "__main__":
    sys.exit(main())
