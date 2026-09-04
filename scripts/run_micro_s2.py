#!/usr/bin/env python3
"""Micro-campagne pré-S2. Voir results/SUITE_STATUS.md"""
from __future__ import annotations
import argparse, hashlib, json, os, sys
from datetime import datetime, timezone
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from aion.bench.cases import CAS
from aion.bench.runner import campagne
from aion.budget import Budget

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
    ap.add_argument("--max-usd", type=float, default=0.0)
    ap.add_argument("--graine", type=int, default=42)
    args = ap.parse_args()
    pre_path = ROOT / "preenregistrement.json"
    pre = json.loads(pre_path.read_text(encoding="utf-8"))
    pre_sha = hashlib.sha256(pre_path.read_bytes()).hexdigest()
    corpus_sha = hashlib.sha256(json.dumps([{"id": c.id, "famille": c.famille, "attendu": c.attendu.value} for c in CAS], sort_keys=True).encode()).hexdigest()
    opposable = (args.reps >= pre["repetitions"] and args.entree == pre["entree_de_reference"] and args.extracteur == pre["extracteur_de_reference"] and args.provider in pre["providers_autorises"])
    print(f"provider={args.provider} reps={args.reps} opposable_s2={opposable}")
    if args.provider in ("anthropic", "openai") and not (os.environ.get("ANTHROPIC_API_KEY") or os.environ.get("OPENAI_API_KEY")):
        print("ERREUR: clé API absente", file=sys.stderr); return 2
    prov = provider_from(args.provider)
    budget = Budget(appels_max=args.max_calls, cout_max_usd=args.max_usd)
    rows = {}
    for bras in pre["bras"]:
        r = campagne(bras, prov, repetitions=args.reps, graine=args.graine, entree=args.entree, extracteur=args.extracteur, budget=budget)
        rows[bras] = {"bar_moyen": r.bar_moyen, "faux_succes": r.resume.get("taux_faux_succes"), "appels_extraction": r.appels_extraction}
        print(f"  {bras:10} BAR={r.bar_moyen:.3f}")
    out_dir = ROOT / "results" / f"micro_{args.provider}"; out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / f"micro_{datetime.now(timezone.utc):%Y%m%dT%H%M%S}.json"
    path.write_text(json.dumps({"opposable_s2": opposable, "pre_sha": pre_sha, "corpus_sha": corpus_sha, "budget_appels": budget.appels, "rows": rows}, indent=2))
    print(f"→ {path}"); return 0

if __name__ == "__main__":
    raise SystemExit(main())
