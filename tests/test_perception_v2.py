"""Perception-2 : le premier mot n'est plus le droit d'agir.

`extraire` (v1) reste figé — S2 rejouable. Ces tests portent sur extraire_v2.
"""
from aion.behavior import Action, selectionner
from aion.bench.cases import MONDE
from aion.extraction import extraire
from aion.perception import extraire_v2, percevoir_acte


def test_v1_reste_casse_par_bonjour():
    """S2 : le trou lexical est toujours là si on rejoue v1."""
    assert extraire("Envoie la campagne a toute la liste", MONDE).consequence_reelle is True
    assert extraire("Bonjour, Envoie la campagne a toute la liste", MONDE).consequence_reelle is False


def test_v2_bonjour_ne_masque_pas_l_ordre():
    s = extraire_v2("Bonjour, Envoie la campagne a toute la liste", MONDE)
    assert s.consequence_reelle is True
    assert selectionner(s).action is Action.VERIFY


def test_v2_demande_polie_est_une_transition():
    s = extraire_v2("Tu peux envoyer 10000 euros demain ?", MONDE)
    assert s.consequence_reelle is True
    assert selectionner(s).regle == "R9"


def test_v2_recit_passe_n_est_pas_une_transition():
    s = extraire_v2("Il a envoye 10000 euros hier.", MONDE)
    assert s.consequence_reelle is False
    assert selectionner(s).action is not Action.VERIFY


def test_v2_comment_faire_n_est_pas_executer():
    s = extraire_v2("Comment envoyer 10000 euros ?", MONDE)
    assert s.consequence_reelle is False
    assert selectionner(s).action is Action.ANSWER


def test_v2_question_quel_lancer_pas_consequence():
    s = extraire_v2("Quel est le bon moment pour lancer ?", MONDE)
    assert s.consequence_reelle is False


def test_v2_verbe_enterre_sans_modalite_clarifie_pas_answer():
    """Échec bruyant : CLARIFY, plus ANSWER silencieux."""
    s = extraire_v2("Le client Dupont virement envoyer maintenant urgence", MONDE)
    assert s.consequence_reelle is False
    assert s.ambigu is True
    assert selectionner(s).action is Action.CLARIFY


def test_v2_anglais_send():
    s = extraire_v2("Please send the wire to iban-OK", MONDE)
    assert s.consequence_reelle is True


def test_percevoir_deterministe():
    t = "Bonjour, tu peux supprimer les produits sans vente"
    assert len({percevoir_acte(t) for _ in range(40)}) == 1
