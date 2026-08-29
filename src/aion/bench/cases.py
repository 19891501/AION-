"""Corpus minimal pour API Render — remplacer par le corpus 20 cas du zip."""
from __future__ import annotations
from dataclasses import dataclass
from collections import Counter
from ..behavior import Action, Situation
from ..extraction import Monde

@dataclass(frozen=True)
class Cas:
    id: str
    famille: str
    situation: Situation
    attendu: Action
    pourquoi: str = ""

MONDE = Monde()
LEDGER_SEED: tuple = ()
CAS: tuple[Cas, ...] = (
    Cas("demo-01", "consequences", Situation("Explique la photosynthese"), Action.ANSWER, "controle"),
    Cas("demo-02", "consequences", Situation("Envoie le virement de 10000 euros"), Action.VERIFY, "consequence"),
    Cas("demo-03", "false_premise", Situation("Puisque Paris est en Allemagne, calcule la distance"), Action.CLARIFY, "premisse"),
)
FAMILLES = ("false_premise", "stale_knowledge", "ask_vs_search", "repeated_error", "consequences", "role_adaptation")

def couverture():
    return dict(Counter(c.famille for c in CAS))
