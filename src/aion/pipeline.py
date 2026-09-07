"""Pipeline AION unifié — INTENTION → Behavior → Veritas → Arbitre.

Une seule entrée, une trace complète, zéro magie.
La preuve décide, pas l'intention.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any

from .arbitre import Arbitrage, Decision, Stake, arbitrer
from .behavior import Action, Choix, Situation, selectionner
from .ledger import Ledger
from .veritas import Evidence, Ruling, Verdict, check


@dataclass(frozen=True)
class EvidenceIn:
    source: str
    supports: bool
    age_days: int = 0
    trusted: bool = True


@dataclass
class PipelineResult:
    """Trace complète d'une décision AION — rejouable et auditable."""

    question: str
    intention: str
    behavior: dict[str, Any]
    veritas: dict[str, Any] | None
    arbitre: dict[str, Any] | None
    final: str
    principle: str = "La preuve décide, pas l'intention."
    chain: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _situation_from(body: dict[str, Any]) -> Situation:
    return Situation(
        question=str(body.get("question", "")),
        premisse_fausse=bool(body.get("premisse_fausse", False)),
        ambigu=bool(body.get("ambigu", False)),
        consequence_reelle=bool(body.get("consequence_reelle", False)),
        connaissance_datee=bool(body.get("connaissance_datee", False)),
        age_connaissance_jours=int(body.get("age_connaissance_jours", 0) or 0),
        source_externe_possible=bool(body.get("source_externe_possible", True)),
        sources_divergentes=bool(body.get("sources_divergentes", False)),
        autorite_utilisateur=bool(body.get("autorite_utilisateur", False)),
        hors_domaine=bool(body.get("hors_domaine", False)),
        fait_cle=str(body.get("fait_cle", "") or ""),
    )


def run_pipeline(
    *,
    question: str,
    flags: dict[str, Any] | None = None,
    claim: str | None = None,
    evidences: list[dict[str, Any]] | None = None,
    stake: dict[str, Any] | None = None,
    ledger: Ledger | None = None,
    max_age_days: int = 180,
) -> PipelineResult:
    """Exécute la chaîne complète et renvoie une trace structurée.

    - Si aucune preuve n'est fournie et que l'action n'exige pas de vérification
      lourde, l'Arbitre peut rester None (décision purement comportementale).
    - Si consequence_reelle ou des evidences sont fournies, Veritas+Arbitre s'appliquent.
    """
    flags = dict(flags or {})
    flags["question"] = question
    sit = _situation_from(flags)
    led = ledger if ledger is not None else Ledger()
    choix: Choix = selectionner(sit, led)

    behavior = {
        "action": choix.action.value,
        "regle": choix.regle,
        "motif": choix.motif,
    }
    chain = [f"INTENTION:{question[:60]}", f"BEHAVIOR:{choix.action.value}:{choix.regle}"]

    veritas_out: dict[str, Any] | None = None
    arbitre_out: dict[str, Any] | None = None
    final = choix.action.value

    needs_proof = (
        choix.action in (Action.VERIFY, Action.COMPARE, Action.SEARCH)
        or bool(sit.consequence_reelle)
        or bool(evidences)
        or bool(claim)
    )

    if needs_proof:
        claim_text = claim or f"Autorisation d'exécuter: {question[:120]}"
        evs: list[Evidence] = []
        for e in evidences or []:
            evs.append(
                Evidence(
                    source=str(e.get("source", "")),
                    supports=bool(e.get("supports", True)),
                    age_days=int(e.get("age_days", 0) or 0),
                    trusted=bool(e.get("trusted", True)),
                )
            )
        ruling: Ruling = check(claim_text, evs, max_age_days=max_age_days)
        veritas_out = {
            "claim": claim_text,
            "verdict": ruling.verdict.value,
            "reason": ruling.reason,
            "n_evidences": len(evs),
        }
        chain.append(f"VERITAS:{ruling.verdict.value}")

        st = stake or {}
        stake_obj = Stake(
            reversible=bool(st.get("reversible", not sit.consequence_reelle)),
            cout=float(st.get("cout", 10000.0 if sit.consequence_reelle else 0.0)),
            seuil_humain=float(st.get("seuil_humain", 50.0)),
            test_disponible=bool(st.get("test_disponible", True)),
            echecs_precedents=int(st.get("echecs_precedents", 0) or 0),
        )
        arb: Arbitrage = arbitrer(ruling, stake_obj)
        arbitre_out = {
            "decision": arb.decision.value,
            "motif": arb.motif,
            "stake": {
                "reversible": stake_obj.reversible,
                "cout": stake_obj.cout,
                "seuil_humain": stake_obj.seuil_humain,
            },
        }
        chain.append(f"ARBITRE:{arb.decision.value}")
        final = arb.decision.value
    else:
        chain.append("ARBITRE:SKIP")

    return PipelineResult(
        question=question,
        intention=question,
        behavior=behavior,
        veritas=veritas_out,
        arbitre=arbitre_out,
        final=final,
        chain=chain,
    )
