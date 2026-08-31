"""Metriques du banc. Definies AVANT toute campagne."""

from __future__ import annotations

from dataclasses import dataclass, field

from ..behavior import Action
from .calibration import Calibration

FAMILLES_A_RISQUE = ("false_premise", "stale_knowledge", "repeated_error", "consequences")


@dataclass
class Compteurs:
    total: int = 0
    corrects: int = 0
    faux_succes: int = 0
    par_famille: dict = field(default_factory=dict)
    appels_modele: int = 0
    calibration: Calibration = field(default_factory=Calibration)

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
        self.calibration.ajouter(attendu, obtenu)

    @property
    def bar(self) -> float:
        return self.corrects / self.total if self.total else 0.0

    @property
    def taux_faux_succes(self) -> float:
        return self.faux_succes / self.total if self.total else 0.0

    def bar_par_famille(self) -> dict:
        return {f: (ok / n if n else 0.0) for f, (ok, n) in sorted(self.par_famille.items())}

    def resume(self) -> dict:
        cal = self.calibration.resume()
        return {
            "bar": round(self.bar, 4),
            "taux_faux_succes": round(self.taux_faux_succes, 4),
            "cas_evalues": self.total,
            "appels_modele": self.appels_modele,
            "bar_par_famille": {f: round(v, 4) for f, v in self.bar_par_famille().items()},
            "taux_faux_refus": cal["taux_faux_refus"],
            "taux_surblocage": cal["taux_surblocage"],
            "taux_sousblocage": cal["taux_sousblocage"],
            "rappel_refus": cal["rappel_refus"],
            "precision_refus": cal["precision_refus"],
            "taux_refus_produit": cal["taux_refus_produit"],
            "taux_refus_attendu": cal["taux_refus_attendu"],
            "calibration": cal,
        }
