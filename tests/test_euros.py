"""AION-EUROS : le rejeu retrospectif compte-t-il honnetement ?"""

import pytest

from aion.euros import DecisionPassee, charger, rejouer, sensibilite


def _perte(preuve="aucune", montant=900.0, perte=600.0):
    return DecisionPassee("p", "action risquee", montant, False, "perte", perte, preuve=preuve)


def _gain(montant=40.0, gain=1000.0):
    return DecisionPassee("g", "action saine", montant, False, "gain", 0.0, gain, preuve="pour")


def test_une_perte_evitee_est_comptee_au_taux_de_rattrapage():
    b = rejouer([_perte()], rattrapage=0.5)
    assert b.perte_evitee == 300.0
    assert b.perte_subie == 0.0


def test_le_cout_d_opportunite_est_toujours_compte():
    """Sans lui, un kernel qui bloque tout parait infiniment rentable."""
    b = rejouer([_gain()], part_gain_perdue=0.2)
    assert b.gain_manque > 0 or b.executions == 1


def test_un_kernel_qui_bloque_tout_ne_peut_pas_avoir_un_ratio_infini():
    tout_gain = [_gain(montant=90.0 + i) for i in range(5)]   # au-dessus du seuil humain
    b = rejouer(tout_gain, part_gain_perdue=0.2)
    assert b.executions == 0
    assert b.ratio < 0        # il ne fait que retarder de bonnes actions


def test_le_verdict_s_inverse_avec_l_hypothese_de_rattrapage():
    lot = [_perte(), _gain()]
    optimiste = rejouer(lot, rattrapage=1.0).ratio
    pessimiste = rejouer(lot, rattrapage=0.2).ratio
    assert optimiste > pessimiste


def test_seuil_d_equilibre_independant_du_cout_suppose():
    lot = [_perte(), _gain()]
    a = rejouer(lot, cout_verification=2.0).seuil_equilibre
    b = rejouer(lot, cout_verification=40.0).seuil_equilibre
    assert a == b


def test_rattrapage_hors_bornes_refuse():
    with pytest.raises(ValueError):
        rejouer([_perte()], rattrapage=1.4)


def test_table_de_sensibilite_couvre_les_deux_hypotheses():
    lignes = sensibilite([_perte(), _gain()])
    assert len(lignes) == 4
    assert all("rattrapage" in ligne for ligne in lignes)


def test_gabarit_lisible():
    d = charger("decisions-gabarit.json")
    assert len(d) == 6
    assert sum(1 for x in d if x.issue == "perte") == 3
