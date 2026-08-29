"""Provider deterministe hors ligne. Sert au CI et au controle de reproductibilite.

Il NE produit PAS de chiffre reel : tout rapport genere avec MockProvider est
etiquete `provider=mock` et n'entre pas dans RESULTS.md comme resultat.
"""

from __future__ import annotations

import hashlib

from .base import Reponse


class MockProvider:
    nom = "mock"

    def __init__(self, biais_confiance: float = 1.0) -> None:
        # biais_confiance = 1.0 : le modele repond toujours avec assurance (baseline RAW realiste)
        self.biais_confiance = biais_confiance

    def complete(self, prompt: str, *, system: str = "", max_tokens: int = 512) -> Reponse:
        graine = hashlib.sha256((system + prompt).encode()).hexdigest()
        return Reponse(texte=f"[mock:{graine[:8]}] reponse directe", modele="mock-0")
