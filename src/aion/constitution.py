"""Constitution AION : 7 lois de conduite + 4 lois ARCHE mecanisees."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Loi:
    code: str
    enonce: str


CONSTITUTION: tuple[Loi, ...] = (
    Loi("C1", "Realite avant elegance."),
    Loi("C2", "L'incertitude est une information, pas un bruit a masquer."),
    Loi("C3", "Construire seulement apres validation."),
    Loi("C4", "Chercher activement ses propres erreurs."),
    Loi("C5", "L'autonomie se merite, elle ne se postule pas."),
    Loi("C6", "L'humain garde le dernier mot."),
    Loi("C7", "Toute complexite doit etre justifiee."),
)

ARCHE: tuple[Loi, ...] = (
    Loi("A1", "Aucune mutation directe d'un etat existant."),
    Loi("A2", "Tout etat possede un predecesseur explicite."),
    Loi("A3", "Toute transition est justifiee."),
    Loi("A4", "Aucun passage silencieux de UNKNOWN a un statut de preuve."),
)

CODES = {loi.code: loi for loi in CONSTITUTION + ARCHE}


def cite(code: str) -> str:
    loi = CODES[code]
    return f"{loi.code}: {loi.enonce}"
