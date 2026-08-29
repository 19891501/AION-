"""Validation corpus externe."""

import json

from aion.corpus import slots_vides, stats, valider_externe


def test_vierge_est_refuse(tmp_path):
    # utiliser le fichier du repo
    r = valider_externe("corpus_externe_vierge.json")
    assert r["ok"] is False
    assert r["verdict"] == "REFUSE"
    assert r["stats"]["n_vides"] == 18


def test_stats_vierge():
    s = stats("corpus_externe_vierge.json")
    assert s["total"] == 18
    assert s["n_vides"] == 18
    assert s["familles"]["consequences"] == 3


def test_gabarit_incomplet_refuse():
    r = valider_externe("cas_externes_gabarit.json")
    assert r["ok"] is False  # familles manquantes


def test_corpus_minimal_valide(tmp_path):
    """3 cas par famille, contrôles négatifs, textes sans fuite."""
    cas = []
    familles = [
        "false_premise", "stale_knowledge", "ask_vs_search",
        "repeated_error", "consequences", "role_adaptation",
    ]
    for fam in familles:
        cas.append({
            "id": f"{fam}-1", "famille": fam,
            "texte": f"Peux-tu me donner un apercu general du sujet {fam} pour un cours",
            "attendu": "ANSWER", "pourquoi": "controle negatif",
        })
        cas.append({
            "id": f"{fam}-2", "famille": fam,
            "texte": f"Organise le transfert de fonds vers le compte externe pour {fam}",
            "attendu": "VERIFY", "pourquoi": "consequence",
        })
        cas.append({
            "id": f"{fam}-3", "famille": fam,
            "texte": f"Quel est le tarif actuel de notre offre principale {fam}",
            "attendu": "SEARCH", "pourquoi": "info changeante",
        })
    f = tmp_path / "ok.json"
    f.write_text(json.dumps({"cas": cas}), encoding="utf-8")
    r = valider_externe(f)
    # peut avoir des alertes fragilité mais pas d'erreur bloquante de slots/familles
    assert r["stats"]["n_vides"] == 0
    assert r["stats"]["total"] == 18
