"""VERITAS : kernel de verification deterministe.

Rend PROOF / FAIL / UNKNOWN / CONFLICT. Aucune probabilite, aucun appel modele :
la meme entree rend toujours la meme sortie (condition du protocole 20 controles).
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class Verdict(str, Enum):
    PROOF = "PROOF"
    FAIL = "FAIL"
    UNKNOWN = "UNKNOWN"
    CONFLICT = "CONFLICT"


@dataclass(frozen=True)
class Evidence:
    source: str
    supports: bool
    age_days: int = 0
    trusted: bool = True


@dataclass(frozen=True)
class Ruling:
    verdict: Verdict
    reason: str
    evidences: tuple[Evidence, ...] = ()

    @property
    def is_proof(self) -> bool:
        return self.verdict is Verdict.PROOF


def check(claim: str, evidences: list[Evidence], *, max_age_days: int = 180) -> Ruling:
    usable = [e for e in evidences if e.trusted and 0 <= e.age_days <= max_age_days]
    vues: set[tuple[str, bool]] = set()
    dedup = []
    for e in usable:
        cle = (e.source, e.supports)
        if cle not in vues:
            vues.add(cle)
            dedup.append(e)
    usable = dedup
    pour = [e for e in usable if e.supports]
    contre = [e for e in usable if not e.supports]

    if pour and contre:
        return Ruling(Verdict.CONFLICT, f"{len(pour)} pour / {len(contre)} contre", tuple(usable))
    if pour:
        return Ruling(Verdict.PROOF, f"{len(pour)} preuve(s) concordante(s)", tuple(pour))
    if contre:
        return Ruling(Verdict.FAIL, f"{len(contre)} preuve(s) contraire(s)", tuple(contre))
    ecartees = len(evidences) - len(usable)
    motif = "aucune preuve utilisable" + (f" ({ecartees} ecartee(s): perimee/non fiable)" if ecartees else "")
    return Ruling(Verdict.UNKNOWN, motif, ())
