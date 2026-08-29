"""Outils corpus externe : stats, validation stricte, refus des slots vides."""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

from .audit import auditer, charger_corpus
from .behavior import Action
from .bench.cases import FAMILLES, LEDGER_SEED, MONDE
from .ledger import Ledger

ACTIONS_OK = {a.value for a in Action}
MIN_CAS_FAMILLE = 3


def _ledger() -> Ledger:
    led = Ledger()
    for fait, statut, justification, source in LEDGER_SEED:
        led.append(fait, statut, justification=justification, source=source)
    return led


def charger_brut(chemin: str | Path) -> dict:
    return json.loads(Path(chemin).read_text(encoding="utf-8"))


def slots_vides(brut: dict) -> list[str]:
    """IDs dont le texte est vide ou trop court."""
    vides = []
    for c in brut.get("cas", []):
        texte = (c.get("texte") or "").strip()
        if len(texte.split()) < 3:
            vides.append(c.get("id", "?"))
    return vides


def stats(chemin: str | Path) -> dict:
    brut = charger_brut(chemin)
    cas = brut.get("cas", [])
    familles = Counter(c.get("famille") for c in cas)
    actions = Counter(c.get("attendu") for c in cas)
    vides = slots_vides(brut)
    return {
        "fichier": str(chemin),
        "total": len(cas),
        "vides": vides,
        "n_vides": len(vides),
        "familles": dict(sorted(familles.items())),
        "actions": dict(sorted(actions.items())),
        "familles_cibles": list(FAMILLES),
    }


def valider_externe(chemin: str | Path) -> dict:
    """Validation complète avant intégration.

    Refuse :
    - slots vides
    - audit NON_TESTABLE
    - familles inconnues / sous-peuplées
    - actions inconnues
    """
    brut = charger_brut(chemin)
    erreurs: list[str] = []
    alertes: list[str] = []

    vides = slots_vides(brut)
    if vides:
        erreurs.append(f"{len(vides)} slot(s) vide(s) ou < 3 mots: {vides}")

    for c in brut.get("cas", []):
        fam = c.get("famille")
        if fam not in FAMILLES:
            erreurs.append(f"{c.get('id')}: famille inconnue '{fam}'")
        att = c.get("attendu")
        if att not in ACTIONS_OK:
            erreurs.append(f"{c.get('id')}: action inconnue '{att}'")

    # Ne lancer l'audit structurel que si les textes sont remplis
    rapport_audit = None
    if not vides:
        try:
            corpus = charger_corpus(str(chemin))
            rapport_audit = auditer(corpus, MONDE, _ledger())
            if not rapport_audit.testable:
                for b in rapport_audit.bloquants:
                    erreurs.append(f"BLOQUANT [{b['code']}] {b['portee']}: {b['message']}")
            for a in rapport_audit.alertes:
                alertes.append(f"ALERTE [{a['code']}] {a['portee']}: {a['message']}")
        except Exception as exc:
            erreurs.append(f"échec audit: {exc}")

    s = stats(chemin)
    for fam in FAMILLES:
        n = s["familles"].get(fam, 0)
        if n < MIN_CAS_FAMILLE:
            erreurs.append(f"famille {fam}: {n} cas (minimum {MIN_CAS_FAMILLE})")

    ok = len(erreurs) == 0
    return {
        "ok": ok,
        "verdict": "PRET_INTEGRATION" if ok else "REFUSE",
        "erreurs": erreurs,
        "alertes": alertes,
        "stats": s,
        "audit_testable": None if rapport_audit is None else rapport_audit.testable,
        "corpus_hash": None if rapport_audit is None else rapport_audit.corpus_hash,
    }
