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

# Modèle économique pour maximiser les appels (change en sonnet si tu préfères qualité)
MODELE="${AION_MODEL:-claude-haiku-4-5-20251001}"
# Fallback noms courants si haiku id différent chez toi :
#   claude-3-5-haiku-latest | claude-3-haiku-20240307 | claude-sonnet-4-6

OUT="results/anthropic_burn_$(date +%Y%m%d_%H%M%S)"
mkdir -p "$OUT" results/cache_anthropic

echo "=== AION burn Anthropic ==="
echo "modele=$MODELE"
echo "out=$OUT"
echo "cache=results/cache_anthropic"
echo

# --- Phase 0 : preflight (2 appels) ---
echo ">>> Phase 0 preflight"
python - <<'PY'
import os
from aion.providers import charger
p = charger("anthropic", modele=os.environ.get("AION_MODEL", "claude-haiku-4-5-20251001"))
r = p.complete("Réponds uniquement: OK", max_tokens=8)
print("preflight:", r.modele, r.texte[:80], "tok", r.tokens_entree, r.tokens_sortie)
PY

# --- Phase 1 : micro (circuit + premier BAR réel) ---
# ~5 cas × 3 reps × bras + extractions LLM — ordre de grandeur 40–120 appels
echo ">>> Phase 1 MICRO"
python -m aion bench --provider anthropic --modele "$MODELE" --micro \
  --entree paraphrase --extracteur llm \
  --cache results/cache_anthropic \
  --budget-appels 150 --cout-appel 0.02 \
  --out "$OUT/micro" || true

# --- Phase 2 : campagne élargie (reste du budget) ---
# 20 cas × reps limitées, cache ON pour ne pas rejouer les mêmes prompts
echo ">>> Phase 2 ETENDUE (20 cas, reps=5, budget restant)"
python -m aion bench --provider anthropic --modele "$MODELE" \
  --entree paraphrase --extracteur llm \
  --reps 5 --max-cas 20 \
  --cache results/cache_anthropic \
  --budget-appels 800 --cout-appel 0.02 \
  --out "$OUT/etendue" || true

# --- Phase 3 : si crédit reste, encore des reps ---
echo ">>> Phase 3 REPS SUPPLEMENTAIRES (si budget OK)"
python -m aion bench --provider anthropic --modele "$MODELE" \
  --entree paraphrase --extracteur llm \
  --reps 10 --max-cas 20 \
  --cache results/cache_anthropic \
  --budget-appels 600 --cout-appel 0.02 \
  --out "$OUT/reps10" || true

echo
echo "=== Terminé ==="
echo "Rapports: $OUT"
ls -la "$OUT" 2>/dev/null || true
