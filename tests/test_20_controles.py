"""Protocole impose : 20 repetitions, ordre et environnement changes.
PASS uniquement si les 20 sont reproductibles. Instable = pas de preuve.
"""

import pytest

from aion.bench import campagne, comparer
from aion.providers import MockProvider


@pytest.mark.parametrize("bras", ["RAW", "SCAFFOLD", "AION"])
def test_campagne_stable_sur_20_controles(bras):
    r = campagne(bras, MockProvider(), repetitions=20)
    assert r.repetitions == 20
    assert r.stable, f"{bras} instable: {sorted(set(r.bars))}"
    assert r.pass_20_controles


def test_graines_differentes_donnent_le_meme_bar_pour_aion():
    a = campagne("AION", MockProvider(), repetitions=20, graine=0)
    b = campagne("AION", MockProvider(), repetitions=20, graine=997)
    assert a.resume["bar"] == b.resume["bar"]


def test_aion_ne_consomme_aucun_appel_modele_pour_decider():
    r = campagne("AION", MockProvider(), repetitions=20)
    assert r.resume["appels_modele"] == 0


def test_les_trois_bras_sont_evalues_sur_les_memes_cas():
    rapports = comparer(MockProvider(), repetitions=20)
    tailles = {r.resume["cas_evalues"] for r in rapports.values()}
    assert len(tailles) == 1
