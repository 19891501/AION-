"""AION-€ : rejouer le kernel sur des decisions passees reelles, et compter en euros.

Le BAR mesure la conformite a une table de regles ecrite par son auteur. Ce
module mesure autre chose : ce que l'arbitrage aurait coute et rapporte, dans
l'unite du critere de reussite declare du projet.

Aucun appel modele, aucune depense : le calcul est retrospectif, sur des
decisions deja prises et dont l'issue est deja connue.

Honnetete du calcul : le resultat depend de deux hypotheses que personne ne peut
mesurer directement — le taux de rattrapage (une verification demandee aurait-elle
vraiment evite la perte ?) et le cout d'une verification. Le module ne rend donc
JAMAIS un chiffre seul : il rend le point d'equilibre, c'est-a-dire le cout de
verification au-dela duquel le kernel ne vaut plus rien.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from .arbitre import Decision as Verdict
from .arbitre import Stake, arbitrer
from .veritas import Evidence, check

ISSUES = ("perte", "neutre", "gain")
AGIR = (Verdict.EXECUTER,)


@dataclass(frozen=True)
class DecisionPassee:
    """Une decision reellement prise, dont l'issue est connue."""

    id: str
    libelle: str
    montant_engage: float          # euros engages par l'action
    reversible: bool
    issue: str                     # "perte" | "neutre" | "gain"
    perte_constatee: float = 0.0   # euros reellement perdus (0 si issue != perte)
    gain_constate: float = 0.0     # euros reellement gagnes (0 si issue != gain)
    preuve: str = "aucune"         # "pour" | "contre" | "aucune" | "contradictoire"
    date: str = ""

    def evidences(self) -> list[Evidence]:
        if self.preuve == "pour":
            return [Evidence("historique", True)]
        if self.preuve == "contre":
            return [Evidence("historique", False)]
        if self.preuve == "contradictoire":
            return [Evidence("source_a", True), Evidence("source_b", False)]
        return []


@dataclass(frozen=True)
class Bilan:
    decisions: int
    perte_evitee: float
    perte_subie: float
    gain_manque: float
    friction: float
    verifications: int
    executions: int
    ratio: float
    seuil_equilibre: float   # cout max par verification pour que le ratio reste >= 1
    detail: list[dict]

    def resume(self) -> dict:
        return {
            "decisions": self.decisions,
            "perte_evitee": round(self.perte_evitee, 2),
            "perte_subie": round(self.perte_subie, 2),
            "gain_manque": round(self.gain_manque, 2),
            "friction": round(self.friction, 2),
            "verifications": self.verifications,
            "executions": self.executions,
            "ratio_de_prudence": round(self.ratio, 3),
            "seuil_equilibre_par_verification": round(self.seuil_equilibre, 2),
        }


def rejouer(
    decisions: list[DecisionPassee],
    *,
    cout_verification: float = 4.0,   # euros : temps humain d'une verification
    rattrapage: float = 0.7,          # part des pertes qu'une verification aurait vraiment evitee
    part_gain_perdue: float = 0.2,    # part du gain perdue quand le kernel retarde une bonne action
    seuil_humain: float = 50.0,
) -> Bilan:
    """Rejoue l'arbitre sur des decisions passees. Deterministe."""
    if not 0.0 <= rattrapage <= 1.0:
        raise ValueError("rattrapage doit etre entre 0 et 1")

    perte_evitee = perte_subie = gain_manque = 0.0
    verifications = executions = 0
    detail: list[dict] = []

    for d in decisions:
        ruling = check(d.libelle, d.evidences())
        arb = arbitrer(
            ruling,
            Stake(reversible=d.reversible, cout=d.montant_engage, seuil_humain=seuil_humain),
        )
        agit = arb.decision in AGIR
        evitee = subie = manque = 0.0

        if agit:
            executions += 1
            if d.issue == "perte":
                subie = d.perte_constatee          # le kernel a laisse passer
        else:
            verifications += 1
            if d.issue == "perte":
                evitee = d.perte_constatee * rattrapage   # hypothese explicite
            elif d.issue == "gain":
                # cout d'opportunite : hesiter sur une bonne action retarde le gain.
                # Sans cette ligne, un kernel qui bloque TOUT parait infiniment rentable.
                manque = d.gain_constate * part_gain_perdue

        perte_evitee += evitee
        perte_subie += subie
        gain_manque += manque
        detail.append(
            {
                "id": d.id,
                "verdict_veritas": ruling.verdict.value,
                "decision_kernel": arb.decision.value,
                "issue_reelle": d.issue,
                "perte_evitee": round(evitee, 2),
                "perte_subie": round(subie, 2),
                "gain_manque": round(manque, 2),
            }
        )

    friction = verifications * cout_verification
    net = perte_evitee - perte_subie - gain_manque
    ratio = (net / friction) if friction > 0 else float("inf")
    seuil = (net / verifications) if verifications > 0 else float("inf")
    return Bilan(
        decisions=len(decisions),
        perte_evitee=perte_evitee,
        perte_subie=perte_subie,
        gain_manque=gain_manque,
        friction=friction,
        verifications=verifications,
        executions=executions,
        ratio=ratio,
        seuil_equilibre=seuil,
        detail=detail,
    )


def sensibilite(
    decisions: list[DecisionPassee],
    *,
    couts: tuple[float, ...] = (2.0, 4.0, 8.0, 16.0, 32.0),
    rattrapages: tuple[float, ...] = (0.3, 0.5, 0.7, 1.0),
) -> list[dict]:
    """Le ratio en fonction des deux hypotheses. Un seul chiffre ne veut rien dire."""
    lignes = []
    for r in rattrapages:
        ligne = {"rattrapage": r}
        for c in couts:
            ligne[f"{c:g} EUR"] = round(rejouer(decisions, cout_verification=c, rattrapage=r).ratio, 2)
        lignes.append(ligne)
    return lignes


def charger(chemin: str | Path) -> list[DecisionPassee]:
    charge = json.loads(Path(chemin).read_text(encoding="utf-8"))
    return [DecisionPassee(**{k: v for k, v in d.items() if not k.startswith("_")})
            for d in charge["decisions"]]
