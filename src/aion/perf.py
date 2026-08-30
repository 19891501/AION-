"""Mesure de latence providers (Ollama / local / cloud)."""

from __future__ import annotations

import statistics
import time
from dataclasses import asdict, dataclass, field
from typing import Any

from .providers.base import ModelProvider


@dataclass
class LatencySample:
    ms: float
    ok: bool
    error: str = ""
    tokens_out: int = 0


@dataclass
class PerfReport:
    provider: str
    modele: str
    n: int
    ok: int
    fail: int
    p50_ms: float
    p95_ms: float
    mean_ms: float
    min_ms: float
    max_ms: float
    samples: list[dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _percentile(sorted_vals: list[float], p: float) -> float:
    if not sorted_vals:
        return 0.0
    k = (len(sorted_vals) - 1) * p
    f = int(k)
    c = min(f + 1, len(sorted_vals) - 1)
    if f == c:
        return sorted_vals[f]
    return sorted_vals[f] + (sorted_vals[c] - sorted_vals[f]) * (k - f)


def measure_provider(
    provider: ModelProvider,
    *,
    prompt: str = 'Réponds UNIQUEMENT: {"ok": true}',
    system: str = "Tu es un extracteur JSON minimal.",
    n: int = 5,
    max_tokens: int = 64,
) -> PerfReport:
    samples: list[LatencySample] = []
    for _ in range(n):
        t0 = time.perf_counter()
        try:
            rep = provider.complete(prompt, system=system, max_tokens=max_tokens)
            ms = (time.perf_counter() - t0) * 1000
            samples.append(
                LatencySample(ms=ms, ok=True, tokens_out=int(getattr(rep, "tokens_sortie", 0) or 0))
            )
        except Exception as exc:
            ms = (time.perf_counter() - t0) * 1000
            samples.append(LatencySample(ms=ms, ok=False, error=str(exc)[:200]))

    ok_ms = sorted(s.ms for s in samples if s.ok)
    modele = getattr(provider, "modele", getattr(provider, "nom", "?"))
    return PerfReport(
        provider=getattr(provider, "nom", type(provider).__name__),
        modele=str(modele),
        n=n,
        ok=sum(1 for s in samples if s.ok),
        fail=sum(1 for s in samples if not s.ok),
        p50_ms=round(_percentile(ok_ms, 0.50), 1) if ok_ms else 0.0,
        p95_ms=round(_percentile(ok_ms, 0.95), 1) if ok_ms else 0.0,
        mean_ms=round(statistics.mean(ok_ms), 1) if ok_ms else 0.0,
        min_ms=round(min(ok_ms), 1) if ok_ms else 0.0,
        max_ms=round(max(ok_ms), 1) if ok_ms else 0.0,
        samples=[asdict(s) for s in samples],
    )
