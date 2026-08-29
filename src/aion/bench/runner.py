"""Runner stub — campagne complète via le zip local."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any


@dataclass
class Rapport:
    bras: str = ""
    bar_moyen: float = 0.0
    details: dict = field(default_factory=dict)


def campagne(*args: Any, **kwargs: Any) -> dict:
    raise NotImplementedError("Installer le runner complet depuis aion-0.1.0-github.zip")


def comparer(*args: Any, **kwargs: Any) -> dict:
    raise NotImplementedError("Installer le runner complet depuis aion-0.1.0-github.zip")


def ecrire(*args: Any, **kwargs: Any) -> None:
    raise NotImplementedError("Installer le runner complet depuis aion-0.1.0-github.zip")
