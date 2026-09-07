"""Calibration des taux de refus / abstention.

Question scientifique (Q3, Q5) :
  - Le système refuse-t-il quand il le doit ?
  - Refuse-t-il trop souvent quand il devrait répondre ?

Actions regroupées :
  ABSTENTION  = REFUSE, CLARIFY, DEFER, WAIT   (ne pas répondre maintenant)
  PORTE       = VERIFY, SEARCH, COMPARE, ASK   (ne pas conclure sans étape)
  REPONSE     = ANSWER
  AUTRE       = EXPERIMENT, …

Matrices utiles (sur l'ensemble des cas évalués) :

  FA  faux succès     = attendu ≠ ANSWER  et obtenu = ANSWER
  FR  faux refus      = attendu = ANSWER  et obtenu ∈ ABSTENTION
  TA  vraie réponse   = attendu = ANSWER  et obtenu = ANSWER
  TR  vraie abstention= attendu ∈ ABSTENTION et obtenu ∈ ABSTENTION
  FG  fausse porte    = attendu = ANSWER  et obtenu ∈ PORTE
  TG  vraie porte     = attendu ∈ PORTE   et obtenu ∈ PORTE
  MG  mauvaise porte  = attendu ∈ PORTE   et obtenu = ANSWER  (⊂ FA)

Taux :
  taux_refus_produit   = P(obtenu ∈ ABSTENTION)
  taux_refus_attendu   = P(attendu ∈ ABSTENTION)
  precision_refus      = TR / (TR+FR) si dénominateur > 0
  rappel_refus         = TR / (TR + cas abstention manqués)
  taux_faux_refus      = FR / n
  taux_surblocage      = (FR+FG) / n   # abstention OU porte alors qu'ANSWER attendu
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field
from typing import Iterable

from ..behavior import Action

ABSTENTION = frozenset({
    Action.REFUSE, Action.CLARIFY, Action.DEFER, Action.WAIT,
})
PORTE = frozenset({
    Action.VERIFY, Action.SEARCH, Action.COMPARE, Action.ASK,
})
REPONSE = frozenset({Action.ANSWER})


def _as_action(x) -> Action:
    if isinstance(x, Action):
        return x
    return Action(str(x).upper())


@dataclass
class Calibration:
    n: int = 0
    tr: int = 0   # vraie abstention
    fr: int = 0   # faux refus
    ta: int = 0   # vraie réponse
    fa: int = 0   # faux succès (répond alors qu'il ne faut pas)
    tg: int = 0   # vraie porte
    fg: int = 0   # fausse porte (porte alors qu'ANSWER)
    mg: int = 0   # porte manquée (ANSWER alors que PORTE)
    # distributions
    obtenu_abstention: int = 0
    attendu_abstention: int = 0
    obtenu_porte: int = 0
    attendu_porte: int = 0
    obtenu_answer: int = 0
    attendu_answer: int = 0
    par_action_obtenu: Counter = field(default_factory=Counter)
    par_action_attendu: Counter = field(default_factory=Counter)
    confusions: Counter = field(default_factory=Counter)  # (attendu, obtenu)

    def ajouter(self, attendu: Action | str, obtenu: Action | str) -> None:
        a = _as_action(attendu)
        o = _as_action(obtenu)
        self.n += 1
        self.par_action_attendu[a.value] += 1
        self.par_action_obtenu[o.value] += 1
        self.confusions[(a.value, o.value)] += 1

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
        if a in REPONSE and o in ABSTENTION:
            self.fr += 1
        if a in REPONSE and o in REPONSE:
            self.ta += 1
        if a not in REPONSE and o in REPONSE:
            self.fa += 1
        if a in PORTE and o in PORTE:
            self.tg += 1
        if a in REPONSE and o in PORTE:
            self.fg += 1
        if a in PORTE and o in REPONSE:
            self.mg += 1

    def etendre(self, paires: Iterable[tuple]) -> "Calibration":
        for a, o in paires:
            self.ajouter(a, o)
        return self

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
        # abstentions attendues correctement captées (obtenu aussi abstention)
        # manqués = attendu abstention, obtenu non abstention
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
        """ANSWER attendu mais système bloque (abstention ou porte)."""
        return (self.fr + self.fg) / self.n if self.n else 0.0

    @property
    def taux_sousblocage(self) -> float:
        """Non-ANSWER attendu mais système ANSWER (faux succès)."""
        return self.fa / self.n if self.n else 0.0

    def resume(self) -> dict:
        def r(x: float | None) -> float | None:
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
                "vraie_abstention_TR": self.tr,
                "faux_refus_FR": self.fr,
                "vraie_reponse_TA": self.ta,
                "faux_succes_FA": self.fa,
                "vraie_porte_TG": self.tg,
                "fausse_porte_FG": self.fg,
                "porte_manquee_MG": self.mg,
            },
            "distribution_obtenu": dict(self.par_action_obtenu),
            "distribution_attendu": dict(self.par_action_attendu),
        }


def calibrer_depuis_echecs(echecs: list[dict]) -> Calibration:
    """Calibre à partir d'une liste d'échecs {attendu, obtenu}. Biaisé si seuls les échecs sont listés."""

    cal = Calibration()
    for e in echecs:
        a, o = e.get("attendu"), e.get("obtenu")
        if a is not None and o is not None:
            cal.ajouter(a, o)
    return cal
