"""Extraction par modele : parsing, budget, cache, variance.

Tout tourne sur `SimuleProvider` : un modele factice NON deterministe. Aucun
chiffre produit ici n'est un resultat, mais la mecanique testee est celle qui
servira sur modele reel.
"""

import json

import pytest

from aion.behavior import Situation
from aion.bench import campagne
from aion.budget import Budget, BudgetDepasse
from aion.cache import Cache
from aion.extraction_llm import ExtracteurLLM
from aion.providers import SimuleProvider
from aion.providers.base import Reponse


class ProviderFixe:
    nom = "fixe"

    def __init__(self, texte: str) -> None:
        self.texte = texte

    def complete(self, prompt: str, *, system: str = "", max_tokens: int = 512) -> Reponse:
        return Reponse(texte=self.texte, modele="fixe")


def test_json_entoure_de_texte_est_parse():
    charge = {
        "premisse_fausse": True, "ambigu": False, "connaissance_datee": False,
        "source_externe_possible": True, "sources_divergentes": False,
        "consequence_reelle": False, "autorite_utilisateur": False,
        "hors_domaine": False, "age_connaissance_jours": 0, "fait_cle": "",
    }
    brut = "Voici le resultat :\n```json\n" + json.dumps(charge) + "\n```"
    e = ExtracteurLLM(ProviderFixe(brut))
    assert e.extraire("q").premisse_fausse is True
    assert e.echecs_parse == 0


def test_sortie_non_parsable_est_comptee_pas_masquee():
    e = ExtracteurLLM(ProviderFixe("La demande me parait claire."))
    s = e.extraire("q")
    assert e.echecs_parse == 1
    assert s == Situation(question="q")   # repli explicite : aucune information


def test_cle_manquante_compte_comme_echec():
    e = ExtracteurLLM(ProviderFixe('{"ambigu": true}'))
    e.extraire("q")
    assert e.echecs_parse == 1


def test_budget_arrete_avant_de_depenser():
    e = ExtracteurLLM(SimuleProvider(graine=3), budget=Budget(appels_max=2))
    e.extraire("a")
    e.extraire("b")
    with pytest.raises(BudgetDepasse):
        e.extraire("c")


def test_cache_evite_le_second_appel(tmp_path):
    cache = Cache(tmp_path)
    e = ExtracteurLLM(SimuleProvider(graine=4), cache=cache)
    e.extraire("Envoie la campagne a toute la liste")
    e.extraire("Envoie la campagne a toute la liste")
    assert e.appels == 1
    assert cache.hits == 1


def test_modele_non_deterministe_fait_echouer_les_20_controles():
    """Resultat attendu et sain : un modele bruite ne peut PAS passer le protocole."""
    r = campagne("AION", SimuleProvider(graine=1), repetitions=20, entree="texte", extracteur="llm")
    assert r.stable is False
    assert r.pass_20_controles is False
    assert r.bar_ecart_type > 0.0


def test_le_cache_rend_la_campagne_rejouable_pas_robuste(tmp_path):
    """Deux modeles differents donnent le meme resultat en rejeu sur cache.
    C'est de la rejouabilite. La campagne reste instable : ce n'est pas de la
    robustesse, et les deux ne doivent jamais etre confondues.
    """
    a = campagne("AION", SimuleProvider(graine=1), repetitions=6, entree="texte",
                 extracteur="llm", cache=Cache(tmp_path))
    b = campagne("AION", SimuleProvider(graine=99), repetitions=6, entree="texte",
                 extracteur="llm", cache=Cache(tmp_path))
    assert a.bars == b.bars
    assert a.stable is False
