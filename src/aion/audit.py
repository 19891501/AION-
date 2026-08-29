"""Audit stub — remplacer par le module complet depuis le zip local."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any
from .behavior import Action
from .extraction import Monde
from .ledger import Ledger

@dataclass
class RapportAudit:
    verdict: str
    cas: int
    corpus_hash: str
    familles: dict
    actions: dict
    bloquants: list = field(default_factory=list)
    alertes: list = field(default_factory=list)
    part_un_seul_mot: float = 0.0
    testable: bool = True

def auditer(corpus, monde: Monde, ledger: Ledger | None = None) -> RapportAudit:
    cas_list = list(corpus)
    return RapportAudit(
        verdict="TESTABLE",
        cas=len(cas_list),
        corpus_hash="stub",
        familles={},
        actions={},
        testable=True,
    )

def resume_audit(corpus, monde: Monde, ledger: Ledger | None = None) -> dict:
    r = auditer(corpus, monde, ledger)
    return {
        "verdict": r.verdict,
        "cas": r.cas,
        "corpus_hash": r.corpus_hash,
        "testable": True,
        "bloquants": [],
        "alertes": [],
        "familles": {},
        "actions": {},
    }

def charger_corpus(chemin: str):
    return []
