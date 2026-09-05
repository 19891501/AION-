"""Campagne = protocole des 20 controles.

Chaque repetition change l'ordre des cas ET l'environnement (bruit de surface
sur l'enonce). Un bras n'est PASS que si les 20 repetitions donnent le meme BAR :
instable = pas de preuve.
"""

from __future__ import annotations

import json
import platform
import random
import statistics
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path

from ..budget import Budget
from ..cache import Cache
from ..constitution import cite
from ..extraction import ecart_drapeaux, extraire
from ..extraction_llm import ExtracteurLLM
from ..ledger import Ledger
from ..preenregistrement import empreinte
from ..providers.base import ModelProvider
from .arms import BRAS
from .cases import CAS, LEDGER_SEED, MONDE, PARAPHRASES, couverture
from .metrics import Compteurs

ENTREES = ("drapeaux", "texte", "paraphrase")
EXTRACTEURS = ("lexical", "llm")
BRUITS = ("", "  ", "\n", "Bonjour, ", "Question rapide : ", "stp ")


def _ledger_initial() -> Ledger:
    led = Ledger()
    for fait, statut, justification, source in LEDGER_SEED:
        led.append(fait, statut, justification=justification, source=source)
    return led


def _perturber(question: str, rng: random.Random) -> str:
    return rng.choice(BRUITS) + question


@dataclass
class Rapport:
    bras: str
    provider: str
    modele: str
    entree: str
    extracteur: str
    repetitions: int
    graine: int
    drapeaux_exacts: float = 0.0
    bar_moyen: float = 0.0
    bar_ecart_type: float = 0.0
    bar_min: float = 0.0
    bar_max: float = 0.0
    echecs_parse: int = 0
    appels_extraction: int = 0
    cache_hits: int = 0
    bars: list[float] = field(default_factory=list)
    stable: bool = False
    pass_20_controles: bool = False
    resume: dict = field(default_factory=dict)
    echecs: list[dict] = field(default_factory=list)
    horodatage: str = ""
    environnement: str = ""

    def to_json(self) -> str:
        return json.dumps(asdict(self), ensure_ascii=False, indent=2)


def campagne(
    bras: str,
    provider: ModelProvider,
    *,
    repetitions: int = 20,
    graine: int = 0,
    entree: str = "drapeaux",
    extracteur: str = "lexical",
    cache: Cache | None = None,
    budget: Budget | None = None,
    max_cas: int | None = None,
    cas_override=None,
) -> Rapport:
    if bras not in BRAS:
        raise ValueError(f"bras inconnu: {bras}")
    if entree not in ENTREES:
        raise ValueError(f"entree inconnue: {entree}")
    if extracteur not in EXTRACTEURS:
        raise ValueError(f"extracteur inconnu: {extracteur}")

    llm = ExtracteurLLM(provider, cache=cache, budget=budget) if extracteur == "llm" else None
    joueur = BRAS[bras](provider)
    bars: list[float] = []
    dernier: Compteurs | None = None
    echecs: list[dict] = []
    dernier_exacts = 0
    n_cas = 0

    for rep in range(repetitions):
        rng = random.Random(graine + rep)
        exacts = 0
        pool = list(cas_override) if cas_override is not None else list(CAS)
        ordre = list(pool)
        rng.shuffle(ordre)
        if max_cas is not None:
            ordre = ordre[: max(1, max_cas)]
        ledger = _ledger_initial()
        c = Compteurs()
        n_cas = len(ordre)
        for cas in ordre:
            source_texte = (
                PARAPHRASES.get(cas.id, cas.situation.question) if entree == "paraphrase" else cas.situation.question
            )
            texte = _perturber(source_texte, rng)
            if entree == "drapeaux":
                situation = type(cas.situation)(**{**cas.situation.__dict__, "question": texte})
            elif llm is not None:
                situation = llm.extraire(texte)
                exacts += int(not ecart_drapeaux(cas.situation, situation))
            else:
                situation = extraire(texte, MONDE, ledger)
                exacts += int(not ecart_drapeaux(cas.situation, situation))
            sortie = joueur.jouer(situation, ledger)
            c.ajouter(cas.famille, cas.attendu, sortie.action, sortie.appels_modele)
            if rep == 0 and sortie.action is not cas.attendu:
                echecs.append({
                    "cas": cas.id, "famille": cas.famille,
                    "attendu": cas.attendu.value, "obtenu": sortie.action.value,
                    "motif_bras": sortie.motif, "pourquoi_attendu": cas.pourquoi,
                })
        bars.append(round(c.bar, 4))
        dernier = c
        dernier_exacts = exacts

    stable = len(set(bars)) == 1
    return Rapport(
        bras=bras,
        provider=getattr(provider, "nom", "?"),
        modele=getattr(provider, "modele", getattr(provider, "nom", "?")),
        entree=entree,
        extracteur=extracteur if entree != "drapeaux" else "aucun",
        drapeaux_exacts=round(dernier_exacts / n_cas, 4) if entree != "drapeaux" and n_cas else 1.0,
        bar_moyen=round(statistics.fmean(bars), 4),
        bar_ecart_type=round(statistics.pstdev(bars), 4) if len(bars) > 1 else 0.0,
        bar_min=min(bars) if bars else 0.0,
        bar_max=max(bars) if bars else 0.0,
        echecs_parse=llm.echecs_parse if llm else 0,
        appels_extraction=llm.appels if llm else 0,
        cache_hits=cache.hits if cache else 0,
        repetitions=repetitions,
        graine=graine,
        bars=bars,
        stable=stable,
        pass_20_controles=stable and repetitions >= 20,
        resume=(dernier.resume() if dernier else {}),
        echecs=echecs,
        horodatage=datetime.now(timezone.utc).isoformat(timespec="seconds"),
        environnement=f"python {platform.python_version()} / {platform.system()}",
    )


def comparer(provider: ModelProvider, *, repetitions: int = 20, graine: int = 0,
             entree: str = "drapeaux", extracteur: str = "lexical",
             cache: Cache | None = None, budget: Budget | None = None,
             max_cas: int | None = None, cas_override=None) -> dict[str, Rapport]:
    return {
        nom: campagne(nom, provider, repetitions=repetitions, graine=graine, entree=entree,
                      extracteur=extracteur, cache=cache, budget=budget, max_cas=max_cas,
                      cas_override=cas_override)
        for nom in BRAS
    }


def ecrire(rapports: dict[str, Rapport], dossier: str | Path = "results") -> Path:
    d = Path(dossier)
    d.mkdir(parents=True, exist_ok=True)
    tete = next(iter(rapports.values()))
    chemin = d / f"campagne_{tete.provider}_{tete.entree}_{datetime.now(timezone.utc):%Y%m%dT%H%M%S}.json"
    try:
        marque = empreinte()
    except FileNotFoundError:
        marque = ""
    micro = tete.repetitions < 20 or tete.resume.get("cas_evalues", 20) < 20
    charge = {
        "loi": cite("C4"),
        "preenregistrement_empreinte": marque,
        "corpus_externe": False,
        "micro_campagne": micro,
        "couverture_cas": couverture(),
        "cas_total": sum(couverture().values()),
        "cible_aion_100": 100,
        "rapports": {k: asdict(v) for k, v in rapports.items()},
        "avertissement": (
            "MICRO-CAMPAGNE : non opposable au pre-enregistrement S2."
            if micro else ""
        ),
    }
    chemin.write_text(json.dumps(charge, ensure_ascii=False, indent=2), encoding="utf-8")
    try:
        from ..rapport import ecrire_markdown
        ecrire_markdown(charge, chemin)
    except Exception:
        pass
    return chemin
