"""Arbitre de decision : traduit un verdict VERITAS en action autorisee."""

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
    reversible: bool = True
    cout: float = 0.0
    seuil_humain: float = 50.0
    test_disponible: bool = True
    echecs_precedents: int = 0


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
        return Arbitrage(Decision.DEMANDER_HUMAIN, "preuves contradictoires, arbitrage non automatisable")

    if ruling.verdict is Verdict.FAIL:
        return Arbitrage(Decision.NO_ACTION, "la preuve contredit l'action envisagee")

    if ruling.verdict is Verdict.UNKNOWN:
        if stake.test_disponible:
            return Arbitrage(Decision.TESTER, "incertitude reductible par un test bon marche")
        return Arbitrage(Decision.DEMANDER_HUMAIN, "incertitude non reductible sans decision humaine")

    if not stake.reversible or stake.cout > stake.seuil_humain:
        return Arbitrage(Decision.DEMANDER_HUMAIN, "preuve suffisante mais enjeu irreversible ou couteux")
    return Arbitrage(Decision.EXECUTER, "preuve suffisante, action reversible et peu couteuse")
