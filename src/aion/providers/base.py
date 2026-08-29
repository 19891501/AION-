"""Abstraction ModelProvider : mesurer l'apport de l'architecture, pas du modele."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol, runtime_checkable


@dataclass(frozen=True)
class Reponse:
    texte: str
    modele: str
    tokens_entree: int = 0
    tokens_sortie: int = 0


@runtime_checkable
class ModelProvider(Protocol):
    nom: str

    def complete(self, prompt: str, *, system: str = "", max_tokens: int = 512) -> Reponse: ...
