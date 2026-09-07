#!/usr/bin/env python3
"""Micro-campagne pré-S2 — filet avant le run confirmatoire 20 reps.

Usage:
  # circuit offline (NON opposable)
  PYTHONPATH=src python scripts/run_micro_s2.py --provider simule --reps 3

  # réel (opposable seulement si reps=20 + provider autorisé + pré-reg respecté)
  export ANTHROPIC_API_KEY=...
  PYTHONPATH=src python scripts/run_micro_s2.py --provider anthropic --reps 5 --max-calls 200 --max-usd 5

Ne modifie JAMAIS preenregistrement.json.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from aion.bench.cases import CAS  # noqa: E402
from aion.bench.runner import campagne  # noqa: E402
from aion.budget import Budget  # noqa: E402


def provider_from(name: str):
    name = name.lower()
    if name == "simule":
        from aion.providers.simule import SimuleProvider
        return SimuleProvider(bruit=0.08, casse=0.02, graine=42)
    if name == "mock":
        from aion.providers.mock import MockProvider
        return MockProvider()
    if name == "anthropic":
        from aion.providers.anthropic_provider import AnthropicProvider
        return AnthropicProvider()
    if name == "openai":
        from aion.providers.openai_provider import OpenAIProvider
        return OpenAIProvider()
    if name == "ollama":
        from aion.providers.ollama_provider import OllamaProvider
        return OllamaProvider()
    raise SystemExit(f"provider inconnu: {name}")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--provider", default="simule")
    ap.add_argument("--reps", type=int, default=3)
    ap.add_argument("--entree", default="paraphrase", choices=["drapeaux", "texte", "paraphrase"])
    ap.add_argument("--extracteur", default="llm", choices=["lexical", "llm"])
    ap.add_argument("--max-calls", type=int, default=200)
    ap.add_argument("--max-usd", type=float, default=0.0, help="0 = désactivé")
    ap.add_argument("--graine", type=int, default=42)
    args = ap.parse_args()

    pre_path = ROOT / "preenregistrement.json"
    pre = json.loads(pre_path.read_text(encoding="utf-8"))
    pre_sha = hashlib.sha256(pre_path.read_bytes()).hexdigest()
    corpus_sha = hashlib.sha256(
        json.dumps(
            [{"id": c.id, "famille": c.famille, "attendu": c.attendu.value} for c in CAS],
            sort_keys=True,
        ).encode()
    ).hexdigest()

    opposable = (
        args.reps >= pre["repetitions"]
        and args.entree == pre["entree_de_reference"]
        and args.extracteur == pre["extracteur_de_reference"]
        and args.provider in pre["providers_autorises"]
    )

    print(f"provider={args.provider} reps={args.reps} entree={args.entree} extracteur={args.extracteur}")
    print(f"pre_sha={pre_sha[:16]}… corpus_sha={corpus_sha[:16]}…")
    print(f"opposable_s2={opposable}")
    if args.provider in ("anthropic", "openai") and not (
        os.environ.get("ANTHROPIC_API_KEY") or os.environ.get("OPENAI_API_KEY")
    ):
        print("ERREUR: clé API absente dans l'environnement", file=sys.stderr)
        return 2

    prov = provider_from(args.provider)
    budget = Budget(appels_max=args.max_calls, cout_max_usd=args.max_usd)
    rows = {}
    for bras in pre["bras"]:
        r = campagne(
            bras,
            prov,
            repetitions=args.reps,
            graine=args.graine,
            entree=args.entree,
            extracteur=args.extracteur,
            budget=budget,
        )
        rows[bras] = {
            "bar_moyen": r.bar_moyen,
            "bar_ecart_type": r.bar_ecart_type,
            "faux_succes": r.resume.get("taux_faux_succes"),
            "bar_par_famille": r.resume.get("bar_par_famille"),
            "appels_extraction": r.appels_extraction,
            "n_echecs": len(r.echecs),
        }
        print(f"  {bras:10} BAR={r.bar_moyen:.3f} fs={r.resume.get('taux_faux_succes')}")

    out_dir = ROOT / "results" / f"micro_{args.provider}"
    out_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S")
    payload = {
        "opposable_s2": opposable,
        "horodatage": datetime.now(timezone.utc).isoformat(),
        "preenregistrement_sha256": pre_sha,
        "corpus_sha256": corpus_sha,
        "params": vars(args),
        "budget": {
            "appels": budget.appels,
            "tokens_in": budget.tokens_entree,
            "tokens_out": budget.tokens_sortie,
            "cout_usd": budget.cout_cumule_usd,
        },
        "rows": rows,
        "ecarts": {
            "AION_minus_RAW": rows["AION"]["bar_moyen"] - rows["RAW"]["bar_moyen"],
            "AION_minus_SCAFFOLD": rows["AION"]["bar_moyen"] - rows["SCAFFOLD"]["bar_moyen"],
        },
    }
    path = out_dir / f"micro_{stamp}.json"
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"→ {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
