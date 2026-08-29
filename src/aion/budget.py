"""Budget d'appels modèle — arrêt avant dépassement."""

from __future__ import annotations


class BudgetDepasse(Exception):
    pass


class Budget:
    def __init__(self, appels_max: int, cout_appel: float = 0.0) -> None:
        self.appels_max = appels_max
        self.cout_appel = cout_appel
        self.appels = 0

    def consommer(self, n: int = 1) -> None:
        if self.appels + n > self.appels_max:
            raise BudgetDepasse(
                f"budget epuise: {self.appels}/{self.appels_max} appels "
                f"(cout estime {self.cout_estime():.2f})"
            )
        self.appels += n

    def cout_estime(self) -> float:
        return self.appels * self.cout_appel
