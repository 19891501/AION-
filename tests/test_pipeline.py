from aion.pipeline import run_pipeline
from aion.behavior import Action
from aion.arbitre import Decision


def test_pipeline_paiement_conflict():
    r = run_pipeline(
        question="Envoie le virement de 10000 €",
        flags={"consequence_reelle": True},
        claim="Le bénéficiaire est bien celui demandé",
        evidences=[
            {"source": "bank", "supports": True},
            {"source": "check", "supports": False},
        ],
        stake={"cout": 10000, "reversible": False},
    )
    assert r.behavior["action"] == Action.VERIFY.value
    assert r.behavior["regle"] == "R9"
    assert r.veritas["verdict"] == "CONFLICT"
    assert r.arbitre["decision"] == Decision.DEMANDER_HUMAIN.value
    assert r.final == Decision.DEMANDER_HUMAIN.value


def test_pipeline_answer_skip_arbitre():
    r = run_pipeline(question="Explique la photosynthèse")
    assert r.behavior["action"] == Action.ANSWER.value
    assert r.veritas is None
    assert r.final == Action.ANSWER.value
