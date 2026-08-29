"""AION — noyau de confiance deterministe + banc d'essai comportemental.

Facade publique stable : tout le reste est detail d'implementation.
"""

from .arbitre import Arbitrage, Decision, Stake, arbitrer
from .behavior import Action, Choix, Situation, selectionner
from .constitution import ARCHE, CONSTITUTION, cite
from .ledger import ArcheViolation, Entry, Ledger
from .veritas import Evidence, Ruling, Verdict, check

__version__ = "0.1.0"

__all__ = [
    "ARCHE",
    "CONSTITUTION",
    "Action",
    "Arbitrage",
    "ArcheViolation",
    "Choix",
    "Decision",
    "Entry",
    "Evidence",
    "Ledger",
    "Ruling",
    "Situation",
    "Stake",
    "Verdict",
    "__version__",
    "arbitrer",
    "check",
    "cite",
    "selectionner",
]
