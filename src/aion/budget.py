"""Garde-fou de dépense — appels ET tokens.

Deux verrous indépendants : appels_max et cout_max_usd.
Tarifs de référence (USD/MTok) : haiku 1/5, sonnet 3/15, opus 5/25.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any


class BudgetDepasse(RuntimeError):
    pass


TARIFS: dict[str, tuple[float, float]] = {
    "haiku": (1.0, 5.0),
    "sonnet": (3.0, 15.0),
    "opus": (5.0, 25.0),
    "default": (1.0, 5.0),
}


def tarif_pour_modele(modele: str) -> tuple[float, float]:
    m = (modele or "").lower()
    if "haiku" in m:
        return TARIFS["haiku"]
    if "sonnet" in m:
        return TARIFS["sonnet"]
    if "opus" in m:
        return TARIFS["opus"]
    return TARIFS["default"]


def cout_tokens(input_tokens: int, output_tokens: int, modele: str = "") -> float:
    pin, pout = tarif_pour_modele(modele)
    return (input_tokens * pin + output_tokens * pout) / 1_000_000.0


@dataclass
class AppelTrace:
    call_id: int
    arm: str
    case: str
    rep: int
    input_tokens: int
    output_tokens: int
    estimated_cost_usd: float
    cumulative_cost_usd: float
    modele: str = ""
    cached: bool = False
    ts: str = ""


@dataclass
class Budget:
    appels_max: int = 10_000
    cout_max_usd: float = 0.0
    cout_par_appel: float = 0.0
    modele: str = ""
    appels: int = 0
    tokens_entree: int = 0
    tokens_sortie: int = 0
    cout_cumule_usd: float = 0.0
    journal: list = field(default_factory=list)

    def consommer(self, n: int = 1) -> None:
        if self.appels + n > self.appels_max:
            raise BudgetDepasse(
                f"MAX_CALLS: {self.appels}/{self.appels_max} (cout ${self.cout_estime():.4f})"
            )
        if self.cout_max_usd > 0 and self.cout_estime() >= self.cout_max_usd:
            raise BudgetDepasse(
                f"MAX_ESTIMATED_COST: ${self.cout_estime():.4f} >= ${self.cout_max_usd:.2f}"
            )
        self.appels += n

    def enregistrer(
        self,
        *,
        input_tokens: int = 0,
        output_tokens: int = 0,
        arm: str = "",
        case: str = "",
        rep: int = 0,
        modele: str = "",
        cached: bool = False,
    ) -> AppelTrace:
        m = modele or self.modele
        if cached:
            cost = 0.0
        elif input_tokens or output_tokens:
            cost = cout_tokens(input_tokens, output_tokens, m)
        else:
            cost = self.cout_par_appel
        self.tokens_entree += max(0, input_tokens)
        self.tokens_sortie += max(0, output_tokens)
        self.cout_cumule_usd += cost
        if self.cout_max_usd > 0 and self.cout_cumule_usd > self.cout_max_usd:
            raise BudgetDepasse(
                f"MAX_ESTIMATED_COST dépassé: ${self.cout_cumule_usd:.4f} > ${self.cout_max_usd:.2f}"
            )
        tr = AppelTrace(
            call_id=len(self.journal) + 1,
            arm=arm,
            case=case,
            rep=rep,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            estimated_cost_usd=round(cost, 6),
            cumulative_cost_usd=round(self.cout_cumule_usd, 6),
            modele=m,
            cached=cached,
            ts=datetime.now(timezone.utc).isoformat(timespec="seconds"),
        )
        self.journal.append(tr)
        return tr

    def cout_estime(self) -> float:
        if self.cout_cumule_usd > 0:
            return self.cout_cumule_usd
        return self.appels * self.cout_par_appel

    def resume(self) -> dict[str, Any]:
        return {
            "appels": self.appels,
            "appels_max": self.appels_max,
            "tokens_entree": self.tokens_entree,
            "tokens_sortie": self.tokens_sortie,
            "cout_cumule_usd": round(self.cout_cumule_usd, 6),
            "cout_max_usd": self.cout_max_usd,
            "cout_estime": round(self.cout_estime(), 6),
            "n_traces": len(self.journal),
            "modele": self.modele,
        }

    def journal_dicts(self) -> list[dict[str, Any]]:
        return [asdict(t) for t in self.journal]
