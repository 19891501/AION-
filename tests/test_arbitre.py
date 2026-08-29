from aion import Decision, Evidence, Stake, arbitrer, check


def _proof():
    return check("x", [Evidence("s", True)])


def test_preuve_et_faible_enjeu_executent():
    assert arbitrer(_proof(), Stake(cout=1.0)).decision is Decision.EXECUTER


def test_preuve_mais_irreversible_demande_humain():
    assert arbitrer(_proof(), Stake(reversible=False)).decision is Decision.DEMANDER_HUMAIN


def test_preuve_mais_couteux_demande_humain():
    assert arbitrer(_proof(), Stake(cout=500.0)).decision is Decision.DEMANDER_HUMAIN


def test_inconnu_testable_donne_tester():
    assert arbitrer(check("x", []), Stake(test_disponible=True)).decision is Decision.TESTER


def test_inconnu_non_testable_donne_humain():
    assert arbitrer(check("x", []), Stake(test_disponible=False)).decision is Decision.DEMANDER_HUMAIN


def test_conflit_donne_humain():
    r = check("x", [Evidence("a", True), Evidence("b", False)])
    assert arbitrer(r, Stake()).decision is Decision.DEMANDER_HUMAIN


def test_echec_donne_no_action():
    r = check("x", [Evidence("a", False)])
    assert arbitrer(r, Stake()).decision is Decision.NO_ACTION


def test_trois_echecs_donnent_abandonner():
    assert arbitrer(_proof(), Stake(echecs_precedents=3)).decision is Decision.ABANDONNER
