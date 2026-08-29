#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
PROVIDER="${1:-}"
MODE="${2:-micro}"
usage() { echo "Usage: $0 <anthropic|grok|openai|ollama|local> [micro|full]"; exit 1; }
[[ -z "$PROVIDER" ]] && usage
echo "=== Contrôles pré-vol ==="
PYTHONPATH=src python -m aion selftest >/dev/null && echo "  selftest OK"
PYTHONPATH=src python -m aion audit >/dev/null && echo "  audit OK"
STAMP=$(date -u +%Y%m%dT%H%M%S)
OUTDIR="results/${MODE}_${PROVIDER}_${STAMP}"
mkdir -p "$OUTDIR"
if [[ "$MODE" == "micro" ]]; then
  PYTHONPATH=src python -m aion bench --provider "$PROVIDER" --micro --entree paraphrase --extracteur llm --budget-appels 100 --out "$OUTDIR"
else
  PYTHONPATH=src python -m aion bench --provider "$PROVIDER" --entree paraphrase --extracteur llm --reps 20 --budget-appels 800 --out "$OUTDIR"
fi
echo "Dossier: $OUTDIR"
