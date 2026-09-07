"""R4 — plafond de session dans le vrai arbitrer()."""
from aion.arbitre import Decision, Stake, arbitrer
from aion.veritas import Ruling, Verdict


def _proof():
    return Ruling(verdict=Verdict.PROOF, reason="ok")


def test_r4_single_under_seuil_exec():
    st = Stake(reversible=True, cout=40, seuil_humain=50, plafond_global=None)
    assert arbitrer(_proof(), st).decision is Decision.EXECUTER


def test_r4_aggregation_blocked():
    """9 x 50 EUR avec plafond 50 : premiere OK, suivantes HUMAN (cumul)."""
    plafond = 50.0
    cum = 0.0
    decisions = []
    for _ in range(9):
        st = Stake(
            reversible=True,
            cout=50.0,
            seuil_humain=200.0,  # unitaire OK
            cum_session=cum,
            plafond_global=plafond,
        )
        d = arbitrer(_proof(), st).decision
        decisions.append(d)
        if d is Decision.EXECUTER:
            cum += 50.0
    assert decisions[0] is Decision.EXECUTER
    assert all(d is Decision.DEMANDER_HUMAIN for d in decisions[1:])


def test_r4_450_vs_plafond_50():
    """Reproduction empirique : 9*50 ne doit pas tous passer EXEC."""
    plafond = 50.0
    cum = 0.0
    total_exec = 0.0
    for _ in range(9):
        st = Stake(
            reversible=True,
            cout=50.0,
            seuil_humain=200.0,
            cum_session=cum,
            plafond_global=plafond,
        )
        if arbitrer(_proof(), st).decision is Decision.EXECUTER:
            cum += 50.0
            total_exec += 50.0
    assert total_exec <= plafond


def test_r4_without_plafond_legacy():
    """Sans plafond_global : 40 EUR reversible reste EXEC (retrocompat)."""
    st = Stake(reversible=True, cout=40, seuil_humain=50)
    assert st.plafond_global is None
    assert arbitrer(_proof(), st).decision is Decision.EXECUTER
