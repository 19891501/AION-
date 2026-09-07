"""Actuateurs lab — aucun effet hors Enforcer.

Règle d'architecture :
  Ces fonctions ne sont PAS des points d'entrée publics pour un agent.
  Elles sont passées comme `world=` à Enforcer. Sans jeton valide,
  Enforcer n'appelle jamais world() → effet = 0.

Attaque « canal parallèle » : si un agent importe write_lab et l'appelle
directement, c'est un trou d'architecture. En lab on documente que
le seul chemin supporté est Enforcer.execute → world.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

from .enforcer import Transition


class LabWorld:
    """Monde simulé : journal append-only + fichiers sous un répertoire sandbox."""

    def __init__(self, root: Path | None = None) -> None:
        self.root = root or Path("results/lab_world")
        self.root.mkdir(parents=True, exist_ok=True)
        self.journal: list[dict[str, Any]] = []
        self.mutations = 0

    def __call__(self, tau: Transition) -> None:
        """Callback Enforcer uniquement."""
        self.mutations += 1
        entry = {
            "actor": tau.actor,
            "action": tau.action,
            "target": tau.target,
            "params": dict(tau.params),
            "hash": tau.hash(),
        }
        self.journal.append(entry)
        # effet fichier lab (preuve matérielle minimale)
        path = self.root / f"{tau.hash()[:16]}.json"
        path.write_text(
            __import__("json").dumps(entry, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )


def make_enforcer_for_lab(secret: bytes = b"lab-secret", root: Path | None = None):
    """Construit Enforcer + LabWorld liés."""
    from .enforcer import Enforcer

    world = LabWorld(root)
    enf = Enforcer(secret, world=world)
    return enf, world
