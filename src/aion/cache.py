"""Cache disque des reponses modele : rend une campagne reelle REJOUABLE.

Un modele n'est pas deterministe. Sans cache, une campagne sur modele reel ne
peut etre ni rejouee ni auditee : le chiffre publie ne serait verifiable par
personne, pas meme par son auteur.

Distinction a garder en tete : le cache donne la **rejouabilite**, pas la
**robustesse**. Rejouer un enregistrement ne prouve rien sur la stabilite du
modele — c'est la campagne SANS cache qui la mesure.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path


class Cache:
    def __init__(self, dossier: str | Path = ".cache_aion", actif: bool = True) -> None:
        self.dossier = Path(dossier)
        self.actif = actif
        self.hits = 0
        self.miss = 0
        if actif:
            self.dossier.mkdir(parents=True, exist_ok=True)

    @staticmethod
    def cle(modele: str, system: str, prompt: str) -> str:
        return hashlib.sha256(f"{modele}\x00{system}\x00{prompt}".encode()).hexdigest()

    def lire(self, cle: str) -> str | None:
        if not self.actif:
            return None
        f = self.dossier / f"{cle}.json"
        if f.exists():
            self.hits += 1
            return json.loads(f.read_text(encoding="utf-8"))["texte"]
        self.miss += 1
        return None

    def ecrire(self, cle: str, texte: str) -> None:
        if not self.actif:
            return
        (self.dossier / f"{cle}.json").write_text(
            json.dumps({"texte": texte}, ensure_ascii=False), encoding="utf-8"
        )
