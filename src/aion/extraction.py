"""Extraction des drapeaux depuis un enonce brut."""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass, field

from .behavior import Situation
from .ledger import Ledger

VERBES_CONSEQUENCE = (
    "envoie", "envoyer", "supprime", "supprimer", "applique", "appliquer",
    "reapplique", "reappliquer", "publie", "publier", "lance", "lancer",
    "desactive", "desactiver", "rembourse", "rembourser", "facture", "facturer",
    "reprends", "reprendre", "commande", "commander",
)

MARQUEURS_VAGUES = (
    "optimise", "optimiser", "ameliore", "ameliorer", "compare", "comparer",
    "aide-moi", "aide moi", "arrange", "rends mieux", "revois", "retravaille",
)

POSSESSIFS = (" ma ", " mon ", " mes ", " notre ", " nos ")


def normaliser(texte: str) -> str:
    sans_accent = "".join(
        c for c in unicodedata.normalize("NFD", texte) if unicodedata.category(c) != "Mn"
    )
    return re.sub(r"\s+", " ", sans_accent.lower()).strip()


@dataclass(frozen=True)
class Monde:
    refutations: tuple[tuple[str, ...], ...] = ()
    ages: dict[str, int] = field(default_factory=dict)
    sans_capteur: frozenset[str] = frozenset()
    divergents: frozenset[str] = frozenset()
    hors_perimetre: tuple[str, ...] = ()
    faits: dict[str, str] = field(default_factory=dict)


def _tete(t: str) -> str:
    mots = t.split()
    return mots[0].strip(",.;:!?'") if mots else ""


def extraire(texte: str, monde: Monde, ledger: Ledger | None = None) -> Situation:
    t = normaliser(texte)
    padded = f" {t} "
    hors_domaine = any(mot in t for mot in monde.hors_perimetre)
    premisse_fausse = any(all(mot in t for mot in motif) for motif in monde.refutations)
    sujet_date = next((s for s in monde.ages if normaliser(s) in t), "")
    age = monde.ages.get(sujet_date, 0)
    connaissance_datee = bool(sujet_date)
    source_externe_possible = sujet_date not in monde.sans_capteur
    sources_divergentes = sujet_date in monde.divergents if sujet_date else False
    vague = any(m in t for m in MARQUEURS_VAGUES)
    autorite = any(p in padded for p in POSSESSIFS)
    ambigu = vague
    consequence = _tete(t) in VERBES_CONSEQUENCE
    fait_cle = ""
    for mot, fait in monde.faits.items():
        if normaliser(mot) in t:
            fait_cle = fait
            break
    return Situation(
        question=texte,
        premisse_fausse=premisse_fausse,
        ambigu=ambigu,
        connaissance_datee=connaissance_datee,
        age_connaissance_jours=age,
        source_externe_possible=source_externe_possible,
        sources_divergentes=sources_divergentes,
        consequence_reelle=consequence,
        autorite_utilisateur=autorite,
        hors_domaine=hors_domaine,
        fait_cle=fait_cle,
    )


def ecart_drapeaux(attendue: Situation, obtenue: Situation) -> list[str]:
    champs = (
        "premisse_fausse", "ambigu", "connaissance_datee", "source_externe_possible",
        "sources_divergentes", "consequence_reelle", "autorite_utilisateur",
        "hors_domaine", "fait_cle",
    )
    return [c for c in champs if getattr(attendue, c) != getattr(obtenue, c)]
