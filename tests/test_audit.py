"""Audit : le corpus est-il testable ? Ces tests verrouillent le verdict porté
sur le banc interne, y compris quand il est défavorable.
"""

import json

from aion.audit import (
    auditer,
    charger_corpus,
    ecrire_rapport,
    points_de_rupture,
    resume_audit,
    valider,
)
from aion.behavior import Action
from aion.bench.cases import CAS, LEDGER_SEED, MONDE
from aion.ledger import Ledger


def _ledger():
    led = Ledger()
    for fait, statut, justification, source in LEDGER_SEED:
        led.append(fait, statut, justification=justification, source=source)
    return led


def test_le_banc_interne_passe_les_bloquants():
    """Les bloquants historiques sont corrigés. Les ALERTES restent."""
    r = resume_audit(CAS, MONDE, _ledger())
    assert r["testable"] is True
    assert r["verdict"] == "TESTABLE"
    assert r["bloquants"] == []


def test_des_cas_tiennent_encore_a_un_seul_mot():
    """Non corrigé : ajouter des synonymes pour faire taire l'alerte serait
    ajuster le banc à l'extracteur, c'est-à-dire tricher."""
    r = resume_audit(CAS, MONDE, _ledger())
    assert len(r["cas_a_un_seul_mot"]) >= 4


def test_ablation_detecte_le_mot_porteur():
    assert points_de_rupture("Envoie la campagne a toute la liste", MONDE) == ["Envoie"]


def test_enonce_sans_mot_porteur_est_robuste():
    assert points_de_rupture("Comment calcule-t-on l'aire d'un disque ?", MONDE) == []


def test_fuite_de_la_reponse_est_bloquante(tmp_path):
    corpus = {
        "cas": [
            {
                "id": "f-01",
                "famille": "consequences",
                "texte": "Verify que la commande est bonne avant",
                "attendu": "VERIFY",
                "pourquoi": "",
            },
        ]
    }
    f = tmp_path / "c.json"
    f.write_text(json.dumps(corpus), encoding="utf-8")
    problemes = valider(charger_corpus(str(f)), MONDE)
    assert any(p.code == "FUITE" for p in problemes)


def test_absence_de_controle_negatif_est_bloquante(tmp_path):
    cas = [
        {
            "id": f"n-{i}",
            "famille": "consequences",
            "texte": f"Supprime le produit numero {i} du catalogue",
            "attendu": "VERIFY",
            "pourquoi": "",
        }
        for i in range(3)
    ]
    f = tmp_path / "c.json"
    f.write_text(json.dumps({"cas": cas}), encoding="utf-8")
    problemes = valider(charger_corpus(str(f)), MONDE)
    assert any(p.code == "CONTROLE_NEGATIF" for p in problemes)


def test_gabarit_fourni_est_bien_forme():
    corpus = charger_corpus("cas_externes_gabarit.json")
    assert len(corpus) == 3
    assert corpus[1].attendu is Action.ANSWER


def test_rapport_structure_et_hashable():
    rapport = auditer(CAS, MONDE, _ledger())
    assert rapport.verdict in ("TESTABLE", "NON_TESTABLE")
    assert rapport.cas == 20
    assert rapport.corpus_hash
    assert len(rapport.empreinte()) == 64
    r2 = auditer(CAS, MONDE, _ledger())
    assert rapport.empreinte() == r2.empreinte()


def test_ecrire_rapport_json(tmp_path):
    rapport = auditer(CAS, MONDE, _ledger())
    chemin = ecrire_rapport(rapport, tmp_path / "audit.json")
    data = json.loads(chemin.read_text(encoding="utf-8"))
    assert data["verdict"] == rapport.verdict
    assert "empreinte" in data


def test_codes_problemes_stables():
    """Tout problème a un code machine stable."""
    problemes = valider(CAS, MONDE, _ledger())
    for p in problemes:
        assert p.code
