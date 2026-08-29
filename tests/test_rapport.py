"""Rapport markdown généré à partir d'une campagne JSON."""

from aion.rapport import generer_markdown


def test_generer_markdown_contient_les_bras():
    campagne = {
        "micro_campagne": True,
        "preenregistrement_empreinte": "abc123",
        "cas_total": 5,
        "corpus_externe": False,
        "avertissement": "test",
        "rapports": {
            "RAW": {"bar_moyen": 0.2, "bar_ecart_type": 0.1, "bar_min": 0.1, "bar_max": 0.3,
                    "pass_20_controles": False, "echecs_parse": 0, "appels_extraction": 0, "echecs": []},
            "SCAFFOLD": {"bar_moyen": 0.25, "bar_ecart_type": 0.1, "bar_min": 0.1, "bar_max": 0.3,
                         "pass_20_controles": False, "echecs_parse": 0, "appels_extraction": 0, "echecs": []},
            "AION": {"bar_moyen": 0.5, "bar_ecart_type": 0.1, "bar_min": 0.4, "bar_max": 0.6,
                     "pass_20_controles": False, "echecs_parse": 0, "appels_extraction": 3,
                     "resume": {"taux_faux_succes": 0.1, "cas_evalues": 5, "bar_par_famille": {"x": 0.5}},
                     "echecs": [{"cas": "c1", "famille": "f", "attendu": "ANSWER", "obtenu": "VERIFY"}]},
        },
    }
    md = generer_markdown(campagne)
    assert "MICRO-CAMPAGNE" in md
    assert "AION" in md
    assert "0.500" in md or "0.5" in md
    assert "AION − RAW" in md
