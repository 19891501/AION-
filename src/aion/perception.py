"""Perception-2 — intention d'agir, pas verbe en tête.

S2 a gelé `extraction.extraire` (tête du premier mot). Ce module ne le
remplace pas : le banc `--extracteur lexical` rejoue le NO-GO. Le runtime
et `--extracteur lexical_v2` passent ici.

Règle : un suffixe de politesse ne doit pas faire disparaître une τ.
Un récit au passé ou un « comment faire » n'est pas une τ.
Si un verbe d'effet est là mais la modalité est illisible → incertain
(CLARIFY), jamais ANSWER silencieux.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, replace

from .behavior import Situation
from .extraction import Monde, extraire, normaliser
from .ledger import Ledger

VERBES_EFFET = (
    "envoie", "envoyer", "envoies", "envoyez",
    "supprime", "supprimer", "supprimes", "supprimez",
    "applique", "appliquer", "reapplique", "reappliquer",
    "publie", "publier", "lance", "lancer",
    "desactive", "desactiver", "rembourse", "rembourser",
    "facture", "facturer", "reprends", "reprendre",
    "commande", "commander", "vire", "virer", "paye", "payer",
    "transfer", "transfers", "send", "delete", "drop", "wire",
    "refund", "publish", "launch", "pay",
)

PREFIXES = (
    "bonjour", "bonsoir", "salut", "hello", "hey", "hi",
    "stp", "svp", "s'il te plait", "s'il vous plait", "please",
    "merci", "ok", "alors", "donc", "voila", "dis moi", "dis-moi",
    "question rapide", "petite question",
)

DEMANDES = (
    "est-ce que tu peux", "est-ce que vous pouvez",
    "tu peux", "vous pouvez", "peux-tu", "pouvez-vous",
    "pourrais-tu", "pourriez-vous",
    "je veux que tu", "je voudrais que tu", "j'aimerais que tu",
    "il faut que tu", "merci de", "veuillez", "je te demande de",
)

COMMENT = (
    "comment ", "how to ", "how do i ", "quelle est la marche",
    "quel est le moyen", "explique comment", "expliquer comment",
)

PASSE = (
    " il a ", " elle a ", " on a ", " j'ai ", " je ai ",
    " nous avons ", " ils ont ", " elles ont ",
    " hier", " deja ", " already ", " a envoye", " a supprime",
    " a vire", " a paye",
)


@dataclass(frozen=True)
class IntentActe:
    propose_effet: bool
    incertain: bool
    modalite: str  # ordre | demande | question | recit | aucun
    verbe: str
    reste: str


def _strip_en_tete(t: str, motifs: tuple[str, ...]) -> str:
    s = t
    changed = True
    while changed:
        changed = False
        for m in sorted(motifs, key=len, reverse=True):
            if s == m or s.startswith(m + " ") or s.startswith(m + ",") or s.startswith(m + ":"):
                s = s[len(m):].lstrip(" ,:;-")
                changed = True
                break
    return s


def percevoir_acte(texte: str) -> IntentActe:
    t = normaliser(texte)
    if not t:
        return IntentActe(False, False, "aucun", "", "")

    padded = f" {t} "
    if any(p in padded for p in PASSE) or t.startswith(("il a ", "elle a ", "j'ai ", "on a ")):
        verbe = next((v for v in VERBES_EFFET if v in t), "")
        return IntentActe(False, False, "recit", verbe, t)

    if any(t.startswith(c.strip()) or c in padded for c in COMMENT):
        verbe = next((v for v in VERBES_EFFET if re.search(rf"\b{re.escape(v)}\b", t)), "")
        return IntentActe(False, False, "question", verbe, t)

    corps = _strip_en_tete(t, PREFIXES)
    demande = False
    corps2 = _strip_en_tete(corps, DEMANDES)
    if corps2 != corps:
        demande = True
        corps = corps2

    mots = [m.strip(".,;:!?") for m in corps.split() if m.strip(".,;:!?")]
    tete = mots[0] if mots else ""
    verbe = tete if tete in VERBES_EFFET else next(
        (v for v in VERBES_EFFET if re.search(rf"\b{re.escape(v)}\b", corps)), ""
    )

    if tete in VERBES_EFFET or (demande and verbe):
        return IntentActe(True, False, "demande" if demande else "ordre", verbe, corps)

    if tete in ("quel", "quelle", "quels", "quelles", "pourquoi", "combien", "qui", "quoi"):
        return IntentActe(False, False, "question", verbe, corps)

    if verbe:
        # Verbe d'effet présent, modalité illisible → ne pas ANSWER.
        return IntentActe(False, True, "incertain", verbe, corps)

    return IntentActe(False, False, "aucun", "", corps)


def extraire_v2(texte: str, monde: Monde, ledger: Ledger | None = None) -> Situation:
    """Drapeaux Monde (v1) + intention d'agir (v2)."""
    base = extraire(texte, monde, ledger)
    acte = percevoir_acte(texte)
    return replace(
        base,
        consequence_reelle=acte.propose_effet,
        ambigu=base.ambigu or acte.incertain,
    )
