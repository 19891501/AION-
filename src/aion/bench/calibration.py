"""Calibration des taux de refus / abstention."""
from __future__ import annotations
from collections import Counter
from dataclasses import dataclass, field
from ..behavior import Action

ABSTENTION = frozenset({Action.REFUSE, Action.CLARIFY, Action.DEFER, Action.WAIT})
PORTE = frozenset({Action.VERIFY, Action.SEARCH, Action.COMPARE, Action.ASK})
REPONSE = frozenset({Action.ANSWER})

def _as_action(x) -> Action:
    if isinstance(x, Action):
        return x
    return Action(str(x).upper())

@dataclass
class Calibration:
    n: int = 0
    tr: int = 0
    fr: int = 0
    ta: int = 0
    fa: int = 0
    tg: int = 0
    fg: int = 0
    mg: int = 0
    obtenu_abstention: int = 0
    attendu_abstention: int = 0
    obtenu_porte: int = 0
    attendu_porte: int = 0
    obtenu_answer: int = 0
    attendu_answer: int = 0
    par_action_obtenu: Counter = field(default_factory=Counter)
    par_action_attendu: Counter = field(default_factory=Counter)

    def ajouter(self, attendu, obtenu) -> None:
        a, o = _as_action(attendu), _as_action(obtenu)
        self.n += 1
        self.par_action_attendu[a.value] += 1
        self.par_action_obtenu[o.value] += 1
        if a in ABSTENTION:
            self.attendu_abstention += 1
        if o in ABSTENTION:
            self.obtenu_abstention += 1
        if a in PORTE:
            self.attendu_porte += 1
        if o in PORTE:
            self.obtenu_porte += 1
        if a in REPONSE:
            self.attendu_answer += 1
        if o in REPONSE:
            self.obtenu_answer += 1
        if a in ABSTENTION and o in ABSTENTION:
            self.tr += 1
        elif a in REPONSE and o in ABSTENTION:
            self.fr += 1
        elif a in REPONSE and o in REPONSE:
            self.ta += 1
        elif a not in REPONSE and o in REPONSE:
            self.fa += 1
        if a in PORTE and o in PORTE:
            self.tg += 1
        elif a in REPONSE and o in PORTE:
            self.fg += 1
        elif a in PORTE and o in REPONSE:
            self.mg += 1

    @property
    def taux_refus_produit(self) -> float:
        return self.obtenu_abstention / self.n if self.n else 0.0

    @property
    def taux_refus_attendu(self) -> float:
        return self.attendu_abstention / self.n if self.n else 0.0

    @property
    def precision_refus(self) -> float | None:
        d = self.tr + self.fr
        return self.tr / d if d else None

    @property
    def rappel_refus(self) -> float | None:
        manques = self.attendu_abstention - self.tr
        d = self.tr + manques
        return self.tr / d if d else None

    @property
    def taux_faux_refus(self) -> float:
        return self.fr / self.n if self.n else 0.0

    @property
    def taux_faux_succes(self) -> float:
        return self.fa / self.n if self.n else 0.0

    @property
    def taux_surblocage(self) -> float:
        return (self.fr + self.fg) / self.n if self.n else 0.0

    @property
    def taux_sousblocage(self) -> float:
        return self.fa / self.n if self.n else 0.0

    def resume(self) -> dict:
        def r(x):
            return None if x is None else round(x, 4)
        return {
            "n": self.n,
            "taux_refus_produit": r(self.taux_refus_produit),
            "taux_refus_attendu": r(self.taux_refus_attendu),
            "precision_refus": r(self.precision_refus),
            "rappel_refus": r(self.rappel_refus),
            "taux_faux_refus": r(self.taux_faux_refus),
            "taux_faux_succes": r(self.taux_faux_succes),
            "taux_surblocage": r(self.taux_surblocage),
            "taux_sousblocage": r(self.taux_sousblocage),
            "comptages": {
                "vraie_abstention_TR": self.tr, "faux_refus_FR": self.fr,
                "vraie_reponse_TA": self.ta, "faux_succes_FA": self.fa,
                "vraie_porte_TG": self.tg, "fausse_porte_FG": self.fg,
                "porte_manquee_MG": self.mg,
            },
            "distribution_obtenu": dict(self.par_action_obtenu),
            "distribution_attendu": dict(self.par_action_attendu),
        }
