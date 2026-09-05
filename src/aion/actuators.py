"""Actuateurs lab — aucun effet hors Enforcer."""
from __future__ import annotations
from pathlib import Path
from typing import Any
from .enforcer import Transition

class LabWorld:
    def __init__(self, root: Path | None = None) -> None:
        self.root = root or Path("results/lab_world")
        self.root.mkdir(parents=True, exist_ok=True)
        self.journal: list[dict[str, Any]] = []
        self.mutations = 0

    def __call__(self, tau: Transition) -> None:
        self.mutations += 1
        entry = {"actor": tau.actor, "action": tau.action, "target": tau.target, "params": dict(tau.params), "hash": tau.hash()}
        self.journal.append(entry)
        (self.root / f"{tau.hash()[:16]}.json").write_text(__import__("json").dumps(entry, ensure_ascii=False, indent=2), encoding="utf-8")

def make_enforcer_for_lab(secret: bytes = b"lab-secret", root: Path | None = None):
    from .enforcer import Enforcer
    world = LabWorld(root)
    return Enforcer(secret, world=world), world
