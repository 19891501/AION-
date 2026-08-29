"""Provider deterministe hors ligne. Sert au CI et au controle de reproductibilite."""

from __future__ import annotations

from .base import Reponse


class MockProvider:
    nom = "mock"

    def __init__(self, modele: str = "mock") -> None:
        self.modele = modele

    def complete(self, prompt: str, *, system: str = "", max_tokens: int = 512) -> Reponse:
        # Sortie fixe non parsable en JSON de drapeaux → force le repli ANSWER côté bras SCAFFOLD
        return Reponse(texte="[mock] ok", modele=self.modele)
