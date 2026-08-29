from aion import Evidence, Verdict, check


def test_aucune_preuve_donne_unknown_pas_proof():
    assert check("x", []).verdict is Verdict.UNKNOWN


def test_preuves_concordantes_donnent_proof():
    r = check("x", [Evidence("a", True), Evidence("b", True)])
    assert r.verdict is Verdict.PROOF


def test_preuves_opposees_donnent_conflict():
    r = check("x", [Evidence("a", True), Evidence("b", False)])
    assert r.verdict is Verdict.CONFLICT


def test_preuve_perimee_est_ecartee():
    r = check("x", [Evidence("a", True, age_days=999)])
    assert r.verdict is Verdict.UNKNOWN
    assert "ecartee" in r.reason


def test_preuve_non_fiable_est_ecartee():
    r = check("x", [Evidence("a", True, trusted=False)])
    assert r.verdict is Verdict.UNKNOWN
