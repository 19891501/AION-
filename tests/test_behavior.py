from aion import Action, Ledger, Situation, selectionner


def test_premisse_fausse_declenche_clarify():
    assert selectionner(Situation("q", premisse_fausse=True)).action is Action.CLARIFY


def test_ambigu_avec_autorite_utilisateur_declenche_ask():
    assert selectionner(Situation("q", ambigu=True, autorite_utilisateur=True)).action is Action.ASK


def test_connaissance_perimee_declenche_search():
    s = Situation("q", connaissance_datee=True, age_connaissance_jours=400)
    assert selectionner(s).action is Action.SEARCH


def test_connaissance_perimee_sans_capteur_declenche_defer():
    s = Situation("q", connaissance_datee=True, age_connaissance_jours=400, source_externe_possible=False)
    assert selectionner(s).action is Action.DEFER


def test_fait_rejete_dans_le_ledger_declenche_verify():
    led = Ledger()
    led.append("f", "REJECTED", justification="marge negative", source="shopify")
    assert selectionner(Situation("q", fait_cle="f"), led).action is Action.VERIFY


def test_cas_neutre_donne_answer():
    assert selectionner(Situation("q")).action is Action.ANSWER


def test_deterministe_sur_100_appels():
    s = Situation("q", ambigu=True, autorite_utilisateur=True)
    assert len({selectionner(s).action for _ in range(100)}) == 1
