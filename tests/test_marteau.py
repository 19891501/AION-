"""MARTEAU — suite adverse. Objectif : casser le noyau, pas le valider.

Deux familles de tests :
  * `test_faille_*`  : trous CONNUS et NON corriges. Le test verrouille le trou
    pour qu'il reste visible (s'il disparait, le test casse et on le sait).
  * les autres       : attaques qui ONT casse le noyau et qui sont maintenant
    couvertes par une correction.
"""

from __future__ import annotations

import math

import pytest

from aion import (
    Action,
    ArcheViolation,
    Decision,
    Evidence,
    Ledger,
    Situation,
    Stake,
    Verdict,
    arbitrer,
    check,
    selectionner,
)
from aion.bench import campagne
from aion.bench.cases import CAS
from aion.providers import MockProvider

# --- A. empoisonnement du ledger -------------------------------------

def test_escalade_de_statut_sans_source_est_refusee():
    """HYPOTHESIS -> VERIFIED sans source : passait avant correction (A4 partielle)."""
    led = Ledger()
    led.append("f", "HYPOTHESIS", justification="intuition")
    with pytest.raises(ArcheViolation):
        led.append("f", "VERIFIED", justification="ca me parait juste")


def test_entrees_non_mutables_depuis_l_exterieur():
    """`led.entries[0] = faux` doit etre impossible (A1)."""
    led = Ledger()
    led.append("f", "HYPOTHESIS", justification="observe", source="web")
    with pytest.raises(TypeError):
        led.entries[0] = None


def test_faille_chaine_reforgeable_integralement():
    """LIMITE CONNUE : verify_chain detecte une retouche, pas une reecriture complete.

    Un attaquant qui reconstruit tout le ledger obtient une chaine valide.
    Correctif hors perimetre : ancrage externe (horodatage tiers). Documente
    dans ATTAQUES.md, non corrige.
    """
    vrai = Ledger()
    vrai.append("prix", "VERIFIED", justification="facture", source="stripe")
    faux = Ledger()
    faux.append("prix", "VERIFIED", justification="facture", source="stripe")
    faux.append("prix", "REJECTED", justification="fabrique par l'attaquant", source="stripe")
    assert faux.verify_chain() is True          # <-- le trou
    assert faux.status_of("prix") != vrai.status_of("prix")


def test_faille_justification_semantiquement_vide():
    """LIMITE CONNUE : A3 verifie la presence, pas le sens. '.' suffit."""
    led = Ledger()
    led.append("f", "HYPOTHESIS", justification=".")
    assert len(led) == 1                        # <-- le trou


# --- B. preuves forgees ----------------------------------------------

def test_preuve_datee_dans_le_futur_est_ecartee():
    """age_days negatif = horodatage forge : passait comme PROOF avant correction."""
    r = check("x", [Evidence("attaquant", True, age_days=-5000)])
    assert r.verdict is Verdict.UNKNOWN


def test_une_seule_source_repetee_ne_fait_pas_deux_preuves():
    """Fausse independance : la meme source citee 5 fois ne renforce rien."""
    r = check("x", [Evidence("blog", True) for _ in range(5)])
    assert r.verdict is Verdict.PROOF
    assert len(r.evidences) == 1


def test_source_repetee_ne_masque_pas_un_conflit():
    r = check("x", [Evidence("a", True), Evidence("a", True), Evidence("b", False)])
    assert r.verdict is Verdict.CONFLICT


# --- C. arbitre : contournement du seuil humain -----------------------

def test_cout_nan_ne_passe_pas_le_seuil():
    """NaN > seuil vaut False en Python : l'action passait en EXECUTER."""
    r = check("x", [Evidence("s", True)])
    assert arbitrer(r, Stake(cout=math.nan)).decision is Decision.DEMANDER_HUMAIN


def test_cout_negatif_ne_passe_pas_le_seuil():
    r = check("x", [Evidence("s", True)])
    assert arbitrer(r, Stake(cout=-1000.0)).decision is Decision.DEMANDER_HUMAIN


def test_cout_infini_ne_passe_pas_le_seuil():
    r = check("x", [Evidence("s", True)])
    assert arbitrer(r, Stake(cout=math.inf)).decision is Decision.DEMANDER_HUMAIN


def test_seuil_exact_reste_executable():
    """Controle negatif : le durcissement ne doit pas bloquer le cas nominal."""
    r = check("x", [Evidence("s", True)])
    assert arbitrer(r, Stake(cout=50.0, seuil_humain=50.0)).decision is Decision.EXECUTER


# --- D. behavior engine : conflits de regles --------------------------

def test_hors_domaine_prime_sur_tout():
    s = Situation("q", hors_domaine=True, premisse_fausse=True, consequence_reelle=True)
    assert selectionner(s).action is Action.REFUSE


def test_faille_premisse_fausse_masque_la_consequence_reelle():
    """LIMITE CONNUE : R1 passe avant R9. Une action a cout reel batie sur une
    premisse fausse rend CLARIFY, jamais VERIFY. C'est defendable, mais l'ordre
    des regles est FIGE jusqu'au premier chiffre reel : on documente, on ne
    reordonne pas (regle anti-triche).
    """
    s = Situation("q", premisse_fausse=True, consequence_reelle=True)
    assert selectionner(s).action is Action.CLARIFY   # <-- choix assume


def test_ledger_vide_ne_declenche_pas_de_verify_fantome():
    s = Situation("q", fait_cle="fait_inexistant")
    assert selectionner(s, Ledger()).action is Action.ANSWER


# --- E. metriques : le banc est-il jouable ? --------------------------

class BrasToujoursVerify:
    """Bras degenere : ne repond jamais, verifie toujours."""

    nom = "PARANO"

    def __init__(self, provider):
        self.provider = provider

    def jouer(self, s, ledger):
        from aion.bench.arms import Sortie

        return Sortie(Action.VERIFY, "toujours verifier", 0)


def test_faille_taux_de_faux_succes_est_jouable(monkeypatch):
    """LIMITE CONNUE : un bras qui ne repond JAMAIS obtient 0 faux succes.

    La metrique 'faux succes' ne penalise que l'exces de confiance, pas
    l'exces de prudence. Elle ne doit donc jamais etre lue seule.
    """
    from aion.bench import arms

    monkeypatch.setitem(arms.BRAS, "PARANO", BrasToujoursVerify)
    r = campagne("PARANO", MockProvider(), repetitions=20)
    assert r.resume["taux_faux_succes"] == 0.0    # <-- le trou
    assert r.resume["bar"] < 0.5                  # le BAR, lui, le sanctionne


def test_faille_perturbation_invisible_pour_aion():
    """LIMITE CONNUE ET MAJEURE : le behavior engine ne lit jamais `question`.

    Le bruit de surface applique par le protocole des 20 controles ne peut donc
    RIEN faire varier pour le bras AION. Sa stabilite 20/20 est vraie par
    construction et ne prouve aucune robustesse.
    """
    base = CAS[0].situation
    bruite = type(base)(**{**base.__dict__, "question": "n'importe quoi " + base.question})
    assert selectionner(base).action is selectionner(bruite).action

    vide = type(base)(**{**base.__dict__, "question": ""})
    assert selectionner(vide).action is selectionner(base).action   # <-- le trou
