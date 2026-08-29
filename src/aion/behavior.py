"""Behavior Engine (stade AION-0) : choisir l'action cognitive, pas la reponse."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from .ledger import Ledger


class Action(str, Enum):
    ANSWER = "ANSWER"
    ASK = "ASK"
    SEARCH = "SEARCH"
    VERIFY = "VERIFY"
    COMPARE = "COMPARE"
    CLARIFY = "CLARIFY"
    WAIT = "WAIT"
    EXPERIMENT = "EXPERIMENT"
    REFUSE = "REFUSE"
    DEFER = "DEFER"


@dataclass(frozen=True)
class Situation:
    question: str
    premisse_fausse: bool = False
    ambigu: bool = False
    connaissance_datee: bool = False
    age_connaissance_jours: int = 0
    source_externe_possible: bool = True
    sources_divergentes: bool = False
    consequence_reelle: bool = False
    autorite_utilisateur: bool = False
    hors_domaine: bool = False
    fait_cle: str = ""


@dataclass(frozen=True)
class Choix:
    action: Action
    motif: str
    regle: str


DUREE_FRAICHEUR_JOURS = 90


def selectionner(s: Situation, ledger: Ledger | None = None) -> Choix:
    if s.hors_domaine:
        return Choix(Action.REFUSE, "demande hors perimetre autorise", "R0")
    if s.premisse_fausse:
        return Choix(Action.CLARIFY, "la question repose sur une premisse invalidee", "R1")
    if s.ambigu and s.autorite_utilisateur:
        return Choix(Action.ASK, "information manquante detenue par l'utilisateur seul", "R2")
    if s.ambigu:
        return Choix(Action.CLARIFY, "plusieurs lectures incompatibles de la demande", "R3")
    if s.sources_divergentes:
        return Choix(Action.COMPARE, "sources divergentes a confronter avant de repondre", "R4")
    if ledger is not None and s.fait_cle:
        statut = ledger.status_of(s.fait_cle)
        if statut in ("REJECTED", "CONFLICTED"):
            return Choix(Action.VERIFY, f"fait deja marque {statut} dans le ledger", "R5")
        if statut == "OBSOLETE":
            return Choix(Action.SEARCH, "fait marque OBSOLETE : reobserver avant de repondre", "R6")
    if s.connaissance_datee and s.age_connaissance_jours > DUREE_FRAICHEUR_JOURS:
        if s.source_externe_possible:
            return Choix(Action.SEARCH, "connaissance perimee, capteur externe disponible", "R7")
        return Choix(Action.DEFER, "connaissance perimee, aucun moyen de la rafraichir", "R8")
    if s.consequence_reelle:
        return Choix(Action.VERIFY, "consequence reelle : verifier avant d'agir", "R9")
    return Choix(Action.ANSWER, "aucune incertitude bloquante detectee", "R10")
