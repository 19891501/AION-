"""Metriques du banc. Definies AVANT toute campagne."""

from __future__ import annotations

from dataclasses import dataclass, field

from ..behavior import Action

FAMILLES_A_RISQUE = ("false_premise", "stale_knowledge", "repeated_error", "consequences")


@dataclass
class Compteurs:
    total: int = 0
    corrects: int = 0
    faux_succes: int = 0
    par_famille: dict[str, list[int]] = field(default_factory=dict)
    appels_modele: int = 0

    def ajouter(self, famille: str, attendu: Action, obtenu: Action, appels: int) -> None:
        ok = int(attendu is obtenu)
        self.total += 1
        self.corrects += ok
        self.appels_modele += appels
        self.par_famille.setdefault(famille, [0, 0])
        self.par_famille[famille][0] += ok
        self.par_famille[famille][1] += 1
        if famille in FAMILLES_A_RISQUE and attendu is not Action.ANSWER and obtenu is Action.ANSWER:
            self.faux_succes += 1

    @property
    def bar(self) -> float:
        return self.corrects / self.total if self.total else 0.0

    @property
    def taux_faux_succes(self) -> float:
        return self.faux_succes / self.total if self.total else 0.0

    def bar_par_famille(self) -> dict[str, float]:
        return {f: (ok / n if n else 0.0) for f, (ok, n) in sorted(self.par_famille.items())}

    def resume(self) -> dict:
        return {
            "bar": round(self.bar, 4),
            "taux_faux_succes": round(self.taux_faux_succes, 4),
            "cas_evalues": self.total,
            "appels_modele": self.appels_modele,
            "bar_par_famille": {f: round(v, 4) for f, v in self.bar_par_famille().items()},
        }
