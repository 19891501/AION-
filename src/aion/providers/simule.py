"""Provider qui SIMULE un modele reel : correct la plupart du temps, bruite parfois.

Sert a une seule chose : verifier hors ligne que le banc supporte un provider
NON deterministe. Aucun chiffre produit avec ce provider n'est un resultat.
"""

from __future__ import annotations

import json
import random

from .base import Reponse

CHAMPS = (
    "premisse_fausse", "ambigu", "connaissance_datee", "source_externe_possible",
    "sources_divergentes", "consequence_reelle", "autorite_utilisateur", "hors_domaine",
)


class SimuleProvider:
    """`bruit` = probabilite d'inverser un drapeau ; `casse` = probabilite de
    rendre une sortie non parsable (ce qu'un vrai modele fait aussi)."""

    nom = "simule"

    def __init__(self, bruit: float = 0.08, casse: float = 0.02, graine: int = 0) -> None:
        self.bruit = bruit
        self.casse = casse
        self._rng = random.Random(graine)
        self.modele = f"simule(bruit={bruit},casse={casse})"

    def complete(self, prompt: str, *, system: str = "", max_tokens: int = 512) -> Reponse:
        from ..bench.cases import MONDE
        from ..extraction import extraire

        s = extraire(prompt, MONDE)
        charge = {c: getattr(s, c) for c in CHAMPS}
        charge["age_connaissance_jours"] = s.age_connaissance_jours
        charge["fait_cle"] = s.fait_cle

        if self._rng.random() < self.casse:
            return Reponse(texte="Je pense que la demande est claire.", modele=self.modele)

        for c in CHAMPS:
            if self._rng.random() < self.bruit:
                charge[c] = not charge[c]

        return Reponse(texte=json.dumps(charge), modele=self.modele)
