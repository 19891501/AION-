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
from dataclasses import dataclass, field, replace

from .behavior import Situation
from .ledger import Ledger

# Verbes d'action a consequence reelle. Ne comptent QU'EN TETE d'enonce :
# "Supprime les produits..." est un ordre, "...pour lancer sur le marche" ne l'est pas.
# Perception-2 (`extraire_v2` plus bas) lève ce plafond sans modifier ce lexique :
# le banc S2 `--extracteur lexical` reste rejouable.
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


# --- Perception-2 (runtime / --extracteur lexical_v2). extraire() ci-dessus reste S2. ---

VERBES_EFFET = VERBES_CONSEQUENCE + (
    "envoies", "envoyez", "supprimes", "supprimez",
    "vire", "virer", "paye", "payer",
    "transfer", "transfers", "send", "delete", "drop", "wire",
    "refund", "publish", "launch", "pay",
    "diffuse", "diffuser", "transmets", "transmettre", "expedie", "expedier",
    "retire", "retirer", "enleve", "enlever", "efface", "effacer",
    "remets", "remettre", "restaure", "restaurer",
)

_PREFIXES = (
    "bonjour", "bonsoir", "salut", "hello", "hey", "hi",
    "stp", "svp", "s'il te plait", "s'il vous plait", "please",
    "merci", "ok", "alors", "donc", "voila", "dis moi", "dis-moi",
    "question rapide", "petite question",
)
_DEMANDES = (
    "est-ce que tu peux", "est-ce que vous pouvez",
    "tu peux", "vous pouvez", "peux-tu", "pouvez-vous",
    "pourrais-tu", "pourriez-vous",
    "je veux que tu", "je voudrais que tu", "j'aimerais que tu",
    "il faut que tu", "merci de", "veuillez", "je te demande de",
)
_COMMENT = (
    "comment ", "how to ", "how do i ", "quelle est la marche",
    "quel est le moyen", "explique comment", "expliquer comment",
)
_PASSE = (
    " il a ", " elle a ", " on a ", " j'ai ", " je ai ",
    " nous avons ", " ils ont ", " elles ont ",
    " hier", " deja ", " already ", " a envoye", " a supprime",
)
_INTERRO = ("quel", "quelle", "quels", "quelles", "pourquoi", "combien", "qui", "quoi")


@dataclass(frozen=True)
class IntentActe:
    propose_effet: bool
    incertain: bool
    modalite: str
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
    if any(p in padded for p in _PASSE) or t.startswith(("il a ", "elle a ", "j'ai ", "on a ")):
        verbe = next((v for v in VERBES_EFFET if v in t), "")
        return IntentActe(False, False, "recit", verbe, t)
    if any(t.startswith(c.strip()) or c in padded for c in _COMMENT):
        verbe = next((v for v in VERBES_EFFET if re.search(rf"\b{re.escape(v)}\b", t)), "")
        return IntentActe(False, False, "question", verbe, t)
    corps = _strip_en_tete(t, _PREFIXES)
    demande = False
    corps2 = _strip_en_tete(corps, _DEMANDES)
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
    if tete in _INTERRO:
        return IntentActe(False, False, "question", verbe, corps)
    if verbe:
        return IntentActe(False, True, "incertain", verbe, corps)
    return IntentActe(False, False, "aucun", "", corps)


def extraire_v2(texte: str, monde: Monde, ledger: Ledger | None = None) -> Situation:
    """Drapeaux Monde (v1) + intention d'agir + fail-noisy. Ne remplace pas extraire().

    Couche v2 volontairement séparée du Monde gelé : on n'enrichit pas
    `cases.MONDE` après les paraphrases (anti-triche S2). Les synonymes
    ci-dessous sont un lexique d'acte / de présupposition, pas un recollage
    des 18 paraphrases.
    """
    t = normaliser(texte)
    base = extraire(texte, monde, ledger)
    acte = percevoir_acte(texte)

    premisse = base.premisse_fausse or _premisse_elargie(t, monde)
    datee, age, capteur = _connaissance_elargie(t, monde, base)
    hors = base.hors_domaine or _hors_domaine_elargi(t)
    fait = base.fait_cle or _fait_elargi(t, monde)

    # Présupposition d'événement (« pourquoi X a… », « depuis l'incident »)
    # sans prémisse tranchée → CLARIFY, jamais ANSWER.
    presuppose = (not premisse) and _presuppose_evenement(t)
    ambigu = base.ambigu or acte.incertain or presuppose

    return replace(
        base,
        premisse_fausse=premisse,
        connaissance_datee=datee,
        age_connaissance_jours=age if datee else base.age_connaissance_jours,
        source_externe_possible=capteur,
        hors_domaine=hors,
        fait_cle=fait,
        consequence_reelle=acte.propose_effet,
        ambigu=ambigu,
    )


def _contient_stem(t: str, stem: str) -> bool:
    return stem in t


# stems Monde → formes courantes. PAS les paraphrases du banc.
_SYNONYMES_STEM = {
    "supprim": ("supprim", "retir", "enlev", "aboli", "delete"),
    "webhook": ("webhook",),
    "bug": ("bug", "incident", "panne"),
    "mardi": ("mardi",),
    "prix": ("prix", "tarif", "coute"),
    "taux de conversion": ("taux de conversion", "taux de transformation", "conversion du tunnel"),
    "part de marche": ("part de marche", "part du marche"),
    "remise": ("remise", "rabais", "30%"),
    "fournisseur": ("fournisseur",),
    "stock": ("stock", "unites du produit"),
}


def _elargi(stem: str, t: str) -> bool:
    formes = _SYNONYMES_STEM.get(stem, (stem,))
    return any(_contient_stem(t, f) for f in formes)


def _premisse_elargie(t: str, monde: Monde) -> bool:
    for motif in monde.refutations:
        if all(_elargi(tok, t) or tok in t for tok in motif):
            return True
    return False


def _connaissance_elargie(t: str, monde: Monde, base: Situation) -> tuple[bool, int, bool]:
    if base.connaissance_datee:
        return True, base.age_connaissance_jours, base.source_externe_possible
    for sujet, age in monde.ages.items():
        if _elargi(sujet, t) or normaliser(sujet) in t:
            return True, age, sujet not in monde.sans_capteur
    return False, 0, base.source_externe_possible


def _hors_domaine_elargi(t: str) -> bool:
    return any(s in t for s in ("posolog", "patient", "administr", "prescrire", "infection", "dose "))


def _fait_elargi(t: str, monde: Monde) -> str:
    for mot, fait in monde.faits.items():
        if _elargi(mot, t) or normaliser(mot) in t:
            return fait
    return ""


_PRESUP = (
    "pour quelle raison",
    "depuis le",
    "depuis la",
    "depuis l'",
    "lors du",
    "a-t-elle",
    "a-t-il",
    "ont-ils",
)


def _presuppose_evenement(t: str) -> bool:
    if any(p in t for p in _PRESUP):
        return True
    # « pourquoi » seulement s'il présuppose un événement passé
    if t.startswith("pourquoi ") and any(
        m in t for m in (" a ", " a-t-", " ont ", " supprim", " retir", " perdu", " bug", " incident")
    ):
        return True
    return False

