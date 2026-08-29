import dataclasses

import pytest

from aion import ArcheViolation, Ledger


def test_a1_aucune_mutation_directe():
    led = Ledger()
    e = led.append("f", "HYPOTHESIS", justification="observe", source="web")
    with pytest.raises(dataclasses.FrozenInstanceError):
        e.status = "VERIFIED"


def test_a2_revision_exige_predecesseur():
    led = Ledger()
    with pytest.raises(ArcheViolation):
        led.revise("inconnu", "VERIFIED", justification="x", source="s")


def test_a3_transition_sans_justification_refusee():
    led = Ledger()
    with pytest.raises(ArcheViolation):
        led.append("f", "HYPOTHESIS", justification="   ")


def test_a4_unknown_vers_preuve_sans_source_refuse():
    led = Ledger()
    led.append("f", "UNKNOWN", justification="rien de connu")
    with pytest.raises(ArcheViolation):
        led.append("f", "VERIFIED", justification="je pense que oui")
    led.append("f", "VERIFIED", justification="facture recue", source="stripe")
    assert led.status_of("f") == "VERIFIED"


def test_historique_conserve_l_ancien_etat():
    led = Ledger()
    led.append("f", "HYPOTHESIS", justification="observe", source="web")
    led.revise("f", "REJECTED", justification="infirme par mesure", source="erp")
    hist = led.history("f")
    assert [e.status for e in hist] == ["HYPOTHESIS", "REJECTED"]
    assert hist[1].predecessor == hist[0].seq


def test_chaine_de_hash_detecte_la_falsification():
    led = Ledger()
    led.append("a", "HYPOTHESIS", justification="j1", source="s")
    led.append("b", "HYPOTHESIS", justification="j2", source="s")
    assert led.verify_chain()
    faux = type(led.entries[0])(**{**led.entries[0].__dict__, "fact": "a_modifie"})
    led._entries[0] = faux  # acces interne volontaire : simule une corruption disque
    assert not led.verify_chain()
