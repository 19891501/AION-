"""Pre-enregistrement : les seuils sont geles et leur modification est detectable."""

import json

import pytest

from aion.preenregistrement import charger, decision, empreinte, verifier


def _campagne(bar_aion: float, bar_raw: float = 0.30, **extra) -> dict:
    aion = {
        "bar_moyen": bar_aion, "bar_ecart_type": 0.0, "bar_min": bar_aion, "bar_max": bar_aion,
        "entree": "paraphrase", "extracteur": "lexical", "echecs_parse": 0,
        "appels_extraction": 0, "resume": {"taux_faux_succes": 0.0},
    }
    aion.update(extra)
    autre = {**aion, "bar_moyen": bar_raw}
    return {
        "cas_total": 20,
        "corpus_externe": True,
        "preenregistrement_empreinte": empreinte(),
        "rapports": {"AION": aion, "RAW": autre, "SCAFFOLD": autre},
    }


def test_empreinte_change_si_un_seuil_change(tmp_path):
    pre = charger()
    f = tmp_path / "p.json"
    pre["criteres"]["ecart_aion_raw_minimum"] = 0.05
    f.write_text(json.dumps(pre), encoding="utf-8")
    assert empreinte(f) != empreinte()


def test_empreinte_insensible_a_la_mise_en_forme(tmp_path):
    f = tmp_path / "p.json"
    f.write_text(json.dumps(charger(), indent=8, sort_keys=False), encoding="utf-8")
    assert empreinte(f) == empreinte()


def test_criteres_modifies_apres_campagne_rendent_la_campagne_non_conforme():
    c = _campagne(0.60)
    c["preenregistrement_empreinte"] = "0" * 64
    v = next(x for x in verifier(c) if x.critere == "empreinte")
    assert v.conforme is False


@pytest.mark.parametrize(
    ("bar_aion", "attendu"),
    [
        (0.35, "NO_GO"),       # écart 0.05 < 0.10
        (0.42, "SIMPLIFIER"),  # écart 0.12 ∈ [0.10, 0.15)
        (0.50, "GO"),          # écart 0.20 ≥ 0.15
    ],
)
def test_regle_de_decision_sans_interpretation(bar_aion, attendu):
    assert decision(_campagne(bar_aion)) == attendu


def test_campagne_conforme_quand_toutes_les_conditions_sont_remplies():
    assert all(v.conforme for v in verifier(_campagne(0.60)))


def test_corpus_de_l_auteur_rend_la_campagne_non_conforme():
    c = _campagne(0.60)
    c["corpus_externe"] = False
    assert not all(v.conforme for v in verifier(c))


def test_modele_instable_est_rejete():
    # Seuil S2 écart-type modèle = 0.12 ; amplitude max = 0.30
    c = _campagne(0.60, extracteur="llm", bar_ecart_type=0.15, bar_min=0.40, bar_max=0.85)
    noms = {v.critere for v in verifier(c) if not v.conforme}
    assert "stabilite (ecart-type)" in noms
    assert "amplitude" in noms
