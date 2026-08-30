"""Cache disque des réponses modèle — rejouabilité, PAS robustesse."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path


class Cache:
    def __init__(self, dossier: str | Path) -> None:
        self.root = Path(dossier)
        self.root.mkdir(parents=True, exist_ok=True)
        self.hits = 0
        self.miss = 0

    @staticmethod
    def cle(modele: str, system: str, prompt: str) -> str:
        h = hashlib.sha256(f"{modele}\0{system}\0{prompt}".encode()).hexdigest()
        return h

    def _path(self, cle: str) -> Path:
        return self.root / f"{cle}.json"

    def lire(self, cle: str) -> str | None:
        p = self._path(cle)
        if not p.exists():
            self.miss += 1
            return None
        self.hits += 1
        return json.loads(p.read_text(encoding="utf-8")).get("texte")

    def ecrire(self, cle: str, texte: str) -> None:
        self._path(cle).write_text(
            json.dumps({"texte": texte}, ensure_ascii=False),
            encoding="utf-8",
        )
