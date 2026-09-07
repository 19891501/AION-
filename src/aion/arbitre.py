"""Arbitre de decision : traduit un verdict VERITAS en action autorisee.

Le refus est une reussite si l'action n'est pas justifiee (C5, C6).

R4 (composition) : si plafond_global est defini, EXECUTER n'est autorise
que si cout individuel ET cumul de session projete restent sous les seuils.
Sans plafond_global (None), comportement historique a une transition.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from enum import Enum

from .veritas import Ruling, Verdict


class Decision(str, Enum):
    EXECUTER = "EXECUTER"
    TESTER = "TESTER"
    DEMANDER_HUMAIN = "DEMANDER_HUMAIN"
    NO_ACTION = "NO_ACTION"
    ABANDONNER = "ABANDONNER"


@dataclass(frozen=True)
class Stake:
    """Enjeu de l'action envisagee."""

    reversible: bool = True
    cout: float = 0.0
    seuil_humain: float = 50.0
    test_disponible: bool = True
    echecs_precedents: int = 0
    # R4 — session (optionnel : None = pas de composition, retrocompatible)
    cum_session: float = 0.0
    plafond_global: float | None = None


@dataclass(frozen=True)
class Arbitrage:
    decision: Decision
    motif: str


def arbitrer(ruling: Ruling, stake: Stake) -> Arbitrage:
    if not math.isfinite(stake.cout) or stake.cout < 0:
        return Arbitrage(Decision.DEMANDER_HUMAIN, f"cout non mesurable ({stake.cout})")

    if stake.echecs_precedents >= 3:
        return Arbitrage(Decision.ABANDONNER, "3 echecs sur la meme voie : cause non resolue")

    if ruling.verdict is Verdict.CONFLICT:
        return Arbitrage(
            Decision.DEMANDER_HUMAIN,
            "preuves contradictoires, arbitrage non automatisable",
        )

    if ruling.verdict is Verdict.FAIL:
        return Arbitrage(Decision.NO_ACTION, "la preuve contredit l'action envisagee")

    if ruling.verdict is Verdict.UNKNOWN:
        if stake.test_disponible:
            return Arbitrage(Decision.TESTER, "incertitude reductible par un test bon marche")
        return Arbitrage(
            Decision.DEMANDER_HUMAIN,
            "incertitude non reductible sans decision humaine",
        )

    # PROOF — coût unitaire
    if not stake.reversible or stake.cout > stake.seuil_humain:
        return Arbitrage(
            Decision.DEMANDER_HUMAIN,
            "preuve suffisante mais enjeu irreversible ou couteux",
        )

    # R4 — composition : cumul projete vs plafond global declare
    if stake.plafond_global is not None:
        if not math.isfinite(stake.cum_session) or stake.cum_session < 0:
            return Arbitrage(
                Decision.DEMANDER_HUMAIN,
                f"cumul session non mesurable ({stake.cum_session})",
            )
        if not math.isfinite(stake.plafond_global) or stake.plafond_global < 0:
            return Arbitrage(
                Decision.DEMANDER_HUMAIN,
                f"plafond global non mesurable ({stake.plafond_global})",
            )
        projete = stake.cum_session + stake.cout
        if projete > stake.plafond_global:
            return Arbitrage(
                Decision.DEMANDER_HUMAIN,
                f"R4 plafond session: cumul {stake.cum_session}+{stake.cout}"
                f"={projete} > {stake.plafond_global}",
            )

    return Arbitrage(Decision.EXECUTER, "preuve suffisante, action reversible et peu couteuse")
