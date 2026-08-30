"""Extracteur de drapeaux délégué au modèle + comptage tokens."""

from __future__ import annotations

import json

from .behavior import Situation
from .budget import Budget
from .cache import Cache
from .ledger import Ledger
from .providers.base import ModelProvider

SYSTEME = (
    "Tu extrais des drapeaux d'une demande utilisateur. Reponds UNIQUEMENT par un objet "
    "JSON, sans texte autour, avec exactement ces cles booleennes : premisse_fausse, "
    "ambigu, connaissance_datee, source_externe_possible, sources_divergentes, "
    "consequence_reelle, autorite_utilisateur, hors_domaine. "
    "Ajoute age_connaissance_jours (entier) et fait_cle (chaine, vide si aucun). "
    "N'invente aucun fait : si tu ne sais pas, mets false."
)

BOOLEENS = (
    "premisse_fausse", "ambigu", "connaissance_datee", "source_externe_possible",
    "sources_divergentes", "consequence_reelle", "autorite_utilisateur", "hors_domaine",
)


def _nettoyer(brut: str) -> str:
    t = brut.strip()
    debut, fin = t.find("{"), t.rfind("}")
    if debut == -1 or fin == -1 or fin < debut:
        return t
    return t[debut : fin + 1]


class ExtracteurLLM:
    def __init__(
        self,
        provider: ModelProvider,
        *,
        cache: Cache | None = None,
        budget: Budget | None = None,
    ) -> None:
        self.provider = provider
        self.cache = cache
        self.budget = budget
        self.appels = 0
        self.echecs_parse = 0

    def _completer(self, prompt: str) -> str:
        modele = getattr(self.provider, "modele", getattr(self.provider, "nom", "?"))
        cle = Cache.cle(modele, SYSTEME, prompt)
        if self.cache is not None:
            en_cache = self.cache.lire(cle)
            if en_cache is not None:
                if self.budget is not None:
                    self.budget.enregistrer(
                        input_tokens=0, output_tokens=0,
                        arm="extracteur_llm", modele=modele, cached=True,
                    )
                return en_cache
        if self.budget is not None:
            self.budget.consommer()
        self.appels += 1
        rep = self.provider.complete(prompt, system=SYSTEME, max_tokens=256)
        texte = rep.texte
        if self.budget is not None:
            self.budget.enregistrer(
                input_tokens=getattr(rep, "tokens_entree", 0) or 0,
                output_tokens=getattr(rep, "tokens_sortie", 0) or 0,
                arm="extracteur_llm",
                modele=modele,
                cached=False,
            )
        if self.cache is not None:
            self.cache.ecrire(cle, texte)
        return texte

    def extraire(self, texte: str, ledger: Ledger | None = None) -> Situation:
        brut = self._completer(texte)
        try:
            charge = json.loads(_nettoyer(brut))
            drapeaux = {k: bool(charge[k]) for k in BOOLEENS}
        except (json.JSONDecodeError, KeyError, TypeError, AttributeError):
            self.echecs_parse += 1
            return Situation(question=texte)
        return Situation(
            question=texte,
            age_connaissance_jours=int(charge.get("age_connaissance_jours", 0) or 0),
            fait_cle=str(charge.get("fait_cle", "") or ""),
            **drapeaux,
        )
