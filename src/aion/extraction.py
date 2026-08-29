"""Extraction des drapeaux depuis un enonce brut (correctif de la faille M-02).

Tant que les drapeaux de `Situation` sont poses a la main, le banc evalue une
entree deja digeree. Ce module les derive du texte, de facon deterministe et
sans modele, a partir d'un `Monde` explicite (ce que le systeme sait deja).

Limite structurelle assumee : une premisse fausse n'est PAS detectable depuis le
texte seul. Elle exige une reference exterieure. Si le `Monde` ne contient pas la
refutation, l'extracteur ne peut pas lever le drapeau — et c'est le comportement
correct, pas un bug a masquer.
"""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass, field

from .behavior import Situation
from .ledger import Ledger

# Verbes d'action a consequence reelle. Ne comptent QU'EN TETE d'enonce :
# "Supprime les produits..." est un ordre, "...pour lancer sur le marche" ne l'est pas.
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
    """Minuscules, accents retires, espaces compactes. Neutralise le bruit de surface."""
    sans_accent = "".join(
        c for c in unicodedata.normalize("NFD", texte) if unicodedata.category(c) != "Mn"
    )
    return re.sub(r"\s+", " ", sans_accent.lower()).strip()


@dataclass(frozen=True)
class Monde:
    """Reference exterieure minimale. Ce que le systeme sait AVANT de lire l'enonce."""

    # affirmations refutees : chaque entree est un ensemble de mots qui doivent
    # tous apparaitre pour considerer la premisse comme invalidee
    refutations: tuple[tuple[str, ...], ...] = ()
    # sujet -> age de la derniere observation, en jours
    ages: dict[str, int] = field(default_factory=dict)
    # sujets pour lesquels aucun capteur externe n'existe
    sans_capteur: frozenset[str] = frozenset()
    # sujets ou les sources connues divergent
    divergents: frozenset[str] = frozenset()
    # lexique hors perimetre autorise
    hors_perimetre: tuple[str, ...] = ()
    # mot-cle -> identifiant de fait dans le ledger
    faits: dict[str, str] = field(default_factory=dict)


def _tete(t: str) -> str:
    mots = t.split()
    return mots[0].strip(",.;:!?'") if mots else ""


def extraire(texte: str, monde: Monde, ledger: Ledger | None = None) -> Situation:
    """Texte brut -> Situation. Deterministe : meme texte, memes drapeaux."""
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
    """Liste des drapeaux mal recuperes. Sert a mesurer la qualite d'extraction."""
    champs = (
        "premisse_fausse", "ambigu", "connaissance_datee", "source_externe_possible",
        "sources_divergentes", "consequence_reelle", "autorite_utilisateur",
        "hors_domaine", "fait_cle",
    )
    return [c for c in champs if getattr(attendue, c) != getattr(obtenue, c)]
