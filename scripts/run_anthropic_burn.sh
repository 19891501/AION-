#!/usr/bin/env bash
# Consommer le crédit Anthropic avant expiration — AION mesure réelle.
# Usage:
#   export ANTHROPIC_API_KEY="sk-ant-..."
#   bash scripts/run_anthropic_burn.sh
#
# Ne jamais committer la clé.

set -euo pipefail
cd "$(dirname "$0")/.."
export PYTHONPATH="${PYTHONPATH:-}:src"

if [[ -z "${ANTHROPIC_API_KEY:-}" ]]; then
  echo "ERROR: export ANTHROPIC_API_KEY avant de lancer."
  exit 1
fi

MODELE="${AION_MODEL:-claude-3-5-haiku-latest}"
OUT="results/anthropic_burn_$(date +%Y%m%d_%H%M%S)"
mkdir -p "$OUT" results/cache_anthropic

echo "=== AION burn Anthropic ==="
echo "modele=$MODELE out=$OUT"

echo ">>> Phase 0 preflight"
python - <<PY
import os
from aion.providers import charger
p = charger("anthropic", modele=os.environ.get("AION_MODEL", "claude-3-5-haiku-latest"))
r = p.complete("Réponds uniquement: OK", max_tokens=8)
print("preflight:", r.modele, r.texte[:80], "tok", r.tokens_entree, r.tokens_sortie)
PY

echo ">>> Phase 1 MICRO"
python -m aion bench --provider anthropic --modele "$MODELE" --micro \
  --entree paraphrase --extracteur llm \
  --cache results/cache_anthropic \
  --budget-appels 150 --cout-appel 0.02 \
  --out "$OUT/micro" || true

echo ">>> Phase 2 ETENDUE"
python -m aion bench --provider anthropic --modele "$MODELE" \
  --entree paraphrase --extracteur llm \
  --reps 5 --max-cas 20 \
  --cache results/cache_anthropic \
  --budget-appels 800 --cout-appel 0.02 \
  --out "$OUT/etendue" || true

echo ">>> Phase 3 REPS+"
python -m aion bench --provider anthropic --modele "$MODELE" \
  --entree paraphrase --extracteur llm \
  --reps 10 --max-cas 20 \
  --cache results/cache_anthropic \
  --budget-appels 600 --cout-appel 0.02 \
  --out "$OUT/reps10" || true

echo "=== Terminé → $OUT"
ls -la "$OUT" 2>/dev/null || true
