"""Audit du banc : dire objectivement si un corpus est TESTABLE, avant de mesurer un bras.

Aucun modèle. Tout déterministe.

Instruments :
* ablation mot à mot → fragilité (un seul mot porte-t-il la décision ?)
* contrôles structurels → fuites, doublons, contrôles négatifs, tailles
* score de testabilité → résumé chiffré et verdict binaire

Ce module n'améliore aucun score. Il dit si un score veut dire quelque chose.
"""

from __future__ import annotations

import hashlib
import json
from collections import Counter
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

from .behavior import Action, selectionner
from .extraction import Monde, extraire, normaliser
from .ledger import Ledger

# Mots qui, présents dans un énoncé, révèlent la réponse attendue.
FUITES = (
    "clarify", "verify", "search", "refuse", "defer", "answer", "compare",
    "premisse", "drapeau", "ambigu", "perime", "obsolete", "irreversible",
)

MIN_MOTS, MAX_MOTS = 3, 40
MIN_CAS_PAR_FAMILLE = 3
MAX_PART_UN_SEUL_MOT = 0.40          # au-delà → ALERTE corpus
MAX_PART_SANS_PORTEUR = 0.60         # trop de décisions purement ledger → ALERTE


@dataclass(frozen=True)
class CasExterne:
    """Cas rédigé par une personne extérieure au système."""

    id: str
    famille: str
    texte: str
    attendu: Action
    pourquoi: str = ""


@dataclass(frozen=True)
class Probleme:
    gravite: str          # "BLOQUANT" | "ALERTE"
    portee: str           # id de cas ou nom de famille
    message: str
    code: str = ""        # code machine stable (ex: FUITE, CONTROLE_NEGATIF)


@dataclass
class RapportAudit:
    """Rapport structuré, hashable, sans jugement manuel."""

    verdict: str                          # TESTABLE | NON_TESTABLE
    cas: int = 0
    familles: dict[str, int] = field(default_factory=dict)
    actions_attendues: dict[str, int] = field(default_factory=dict)
    cas_a_un_seul_mot: list[str] = field(default_factory=list)
    cas_sans_mot_porteur: list[str] = field(default_factory=list)
    part_un_seul_mot: float = 0.0
    part_sans_porteur: float = 0.0
    fragilite_moyenne: float = 0.0
    bloquants: list[dict] = field(default_factory=list)
    alertes: list[dict] = field(default_factory=list)
    corpus_hash: str = ""
    horodatage: str = ""
    regles_version: str = "2.0"

    @property
    def testable(self) -> bool:
        return self.verdict == "TESTABLE"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    def empreinte(self) -> str:
        """Hash stable du rapport (sans horodatage)."""
        d = self.to_dict()
        d.pop("horodatage", None)
        canonique = json.dumps(d, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
        return hashlib.sha256(canonique.encode()).hexdigest()


def _texte(cas) -> str:
    return getattr(cas, "texte", None) or cas.situation.question


def _decision(texte: str, monde: Monde, ledger: Ledger | None) -> Action:
    return selectionner(extraire(texte, monde, ledger), ledger).action


def points_de_rupture(texte: str, monde: Monde, ledger: Ledger | None = None) -> list[str]:
    """Mots dont la suppression, seule, change la décision."""
    reference = _decision(texte, monde, ledger)
    mots = texte.split()
    ruptures = []
    for i, _mot in enumerate(mots):
        ampute = " ".join(mots[:i] + mots[i + 1 :])
        if not ampute.strip():
            continue
        if _decision(ampute, monde, ledger) is not reference:
            ruptures.append(mots[i])
    return ruptures


def fragilite(texte: str, monde: Monde, ledger: Ledger | None = None) -> float:
    """1.0 = un seul mot porte la décision. 0.0 = aucun mot n'est indispensable."""
    n = len(points_de_rupture(texte, monde, ledger))
    if n == 0:
        return 0.0
    return 1.0 / n


def valider(corpus: Iterable, monde: Monde, ledger: Ledger | None = None) -> list[Probleme]:
    """Contrôles structurels. BLOQUANT empêche TESTABLE ; ALERTE informe."""
    problemes: list[Probleme] = []
    vus: dict[str, str] = {}
    par_famille: dict[str, list] = {}

    for cas in corpus:
        texte = _texte(cas)
        t = normaliser(texte)
        par_famille.setdefault(cas.famille, []).append(cas)

        if t in vus:
            problemes.append(Probleme(
                "BLOQUANT", cas.id, f"énoncé identique à {vus[t]}", "DOUBLON"
            ))
        vus[t] = cas.id

        n = len(t.split())
        if not MIN_MOTS <= n <= MAX_MOTS:
            problemes.append(Probleme(
                "BLOQUANT", cas.id, f"longueur hors bornes ({n} mots)", "LONGUEUR"
            ))

        fuite = [m for m in FUITES if m in t]
        if fuite:
            problemes.append(Probleme(
                "BLOQUANT", cas.id,
                f"la réponse attendue fuit dans l'énoncé: {fuite}", "FUITE"
            ))

        rupt = points_de_rupture(texte, monde, ledger)
        if len(rupt) == 1:
            problemes.append(Probleme(
                "ALERTE", cas.id,
                f"un seul mot porte la décision: {rupt[0]!r}", "FRAGILE"
            ))

    for famille, cas_f in sorted(par_famille.items()):
        if len(cas_f) < MIN_CAS_PAR_FAMILLE:
            problemes.append(Probleme(
                "BLOQUANT", famille,
                f"{len(cas_f)} cas (minimum {MIN_CAS_PAR_FAMILLE})", "FAMILLE_SOUS_PEUPLEE"
            ))
        if not any(c.attendu is Action.ANSWER for c in cas_f):
            problemes.append(Probleme(
                "BLOQUANT", famille,
                "aucun contrôle négatif (aucun cas où ANSWER est correct)", "CONTROLE_NEGATIF"
            ))
        fragiles = sum(
            1 for c in cas_f
            if len(points_de_rupture(_texte(c), monde, ledger)) == 1
        )
        if fragiles / len(cas_f) >= 0.5:
            problemes.append(Probleme(
                "ALERTE", famille,
                f"{fragiles}/{len(cas_f)} cas tiennent à un seul mot", "FAMILLE_FRAGILE"
            ))

    return problemes


def _corpus_hash(corpus) -> str:
    ids = sorted(c.id for c in corpus)
    return hashlib.sha256(",".join(ids).encode()).hexdigest()[:16]


def auditer(corpus, monde: Monde, ledger: Ledger | None = None) -> RapportAudit:
    """Produit un rapport complet et un verdict binaire objectif."""
    corpus = list(corpus)
    ruptures: dict[str, int] = {}
    frag_vals: list[float] = []

    for cas in corpus:
        texte = _texte(cas)
        r = points_de_rupture(texte, monde, ledger)
        ruptures[cas.id] = len(r)
        frag_vals.append(fragilite(texte, monde, ledger))

    problemes = valider(corpus, monde, ledger)
    bloquants = [p for p in problemes if p.gravite == "BLOQUANT"]
    alertes = [p for p in problemes if p.gravite == "ALERTE"]

    n = len(corpus) or 1
    un_seul = sorted(k for k, v in ruptures.items() if v == 1)
    sans = sorted(k for k, v in ruptures.items() if v == 0)
    part_un = len(un_seul) / n
    part_sans = len(sans) / n

    # Alertes globales supplémentaires (chiffres, pas de jugement)
    if part_un > MAX_PART_UN_SEUL_MOT:
        alertes.append(Probleme(
            "ALERTE", "corpus",
            f"{part_un:.0%} des cas tiennent à un seul mot (seuil {MAX_PART_UN_SEUL_MOT:.0%})",
            "PART_FRAGILE"
        ))
    if part_sans > MAX_PART_SANS_PORTEUR:
        alertes.append(Probleme(
            "ALERTE", "corpus",
            f"{part_sans:.0%} des cas n'ont aucun mot porteur "
            f"(décision purement ledger ou repli) — seuil {MAX_PART_SANS_PORTEUR:.0%}",
            "PART_SANS_PORTEUR"
        ))

    familles = Counter(c.famille for c in corpus)
    actions = Counter(c.attendu.value for c in corpus)

    verdict = "NON_TESTABLE" if bloquants else "TESTABLE"

    return RapportAudit(
        verdict=verdict,
        cas=len(corpus),
        familles=dict(sorted(familles.items())),
        actions_attendues=dict(sorted(actions.items())),
        cas_a_un_seul_mot=un_seul,
        cas_sans_mot_porteur=sans,
        part_un_seul_mot=round(part_un, 4),
        part_sans_porteur=round(part_sans, 4),
        fragilite_moyenne=round(sum(frag_vals) / n, 4),
        bloquants=[{"portee": p.portee, "message": p.message, "code": p.code} for p in bloquants],
        alertes=[{"portee": p.portee, "message": p.message, "code": p.code} for p in alertes],
        corpus_hash=_corpus_hash(corpus),
        horodatage=datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    )


def resume_audit(corpus, monde: Monde, ledger: Ledger | None = None) -> dict:
    """Compatibilité avec l'ancienne interface + champs enrichis."""
    r = auditer(corpus, monde, ledger)
    return {
        "cas": r.cas,
        "testable": r.testable,
        "verdict": r.verdict,
        "ruptures_par_cas": {
            c.id: len(points_de_rupture(_texte(c), monde, ledger)) for c in corpus
        },
        "cas_a_un_seul_mot": r.cas_a_un_seul_mot,
        "cas_sans_mot_porteur": r.cas_sans_mot_porteur,
        "part_un_seul_mot": r.part_un_seul_mot,
        "part_sans_porteur": r.part_sans_porteur,
        "fragilite_moyenne": r.fragilite_moyenne,
        "familles": r.familles,
        "actions_attendues": r.actions_attendues,
        "bloquants": [f"[{b['portee']}] {b['message']}" for b in r.bloquants],
        "alertes": [f"[{a['portee']}] {a['message']}" for a in r.alertes],
        "corpus_hash": r.corpus_hash,
        "empreinte_rapport": r.empreinte(),
    }


def charger_corpus(chemin: str) -> list[CasExterne]:
    """Charge un corpus externe au format JSON (voir KIT_REDACTION.md)."""
    charge = json.loads(Path(chemin).read_text(encoding="utf-8"))
    return [
        CasExterne(
            id=c["id"],
            famille=c["famille"],
            texte=c["texte"],
            attendu=Action(c["attendu"]),
            pourquoi=c.get("pourquoi", ""),
        )
        for c in charge["cas"]
    ]


def ecrire_rapport(rapport: RapportAudit, chemin: str | Path) -> Path:
    """Écrit le rapport JSON (rejouable, hashable)."""
    path = Path(chemin)
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = rapport.to_dict()
    payload["empreinte"] = rapport.empreinte()
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return path
