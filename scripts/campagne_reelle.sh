#!/usr/bin/env bash
# campagne_reelle.sh — lance une micro ou une campagne S2 avec contrôles pré-vol
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

PROVIDER="${1:-}"
MODE="${2:-micro}"

usage() {
  echo "Usage: $0 <anthropic|grok|openai|ollama|local> [micro|full]"
  echo ""
  echo "  micro  — 5 cas × 3 reps  (validation circuit, ~0.3€)"
  echo "  full   — 20 cas × 20 reps (campagne S2 opposable, budget 800)"
  echo ""
  echo "Exemples:"
  echo "  $0 anthropic micro"
  echo "  $0 grok full"
  exit 1
}

[[ -z "$PROVIDER" ]] && usage
case "$PROVIDER" in anthropic|grok|openai|ollama|local) ;; *) usage ;; esac
case "$MODE" in micro|full) ;; *) usage ;; esac

echo "=== Contrôles pré-vol ==="

echo -n "  selftest ... "
PYTHONPATH=src python -m aion selftest >/dev/null
echo "OK"

echo -n "  preenreg ... "
PRE=$(PYTHONPATH=src python -m aion preenreg 2>&1)
echo "$PRE" | grep -q "v2" || { echo "FAIL (pas v2)"; exit 1; }
EMPREINTE=$(echo "$PRE" | grep -oE 'empreinte: [a-f0-9]+' | awk '{print $2}')
echo "OK (${EMPREINTE:0:16}…)"

echo -n "  audit ... "
PYTHONPATH=src python -m aion audit >/dev/null
echo "OK (TESTABLE)"

case "$PROVIDER" in
  anthropic)
    [[ -n "${ANTHROPIC_API_KEY:-}" ]] || { echo "FAIL: ANTHROPIC_API_KEY absente"; exit 1; }
    echo "  clé API ... OK (Anthropic)" ;;
  grok)
    [[ -n "${GROK_API_KEY:-}${OPENAI_API_KEY:-}" ]] || { echo "FAIL: GROK_API_KEY absente"; exit 1; }
    echo "  clé API ... OK (Grok)" ;;
  openai)
    [[ -n "${OPENAI_API_KEY:-}" ]] || { echo "FAIL: OPENAI_API_KEY absente"; exit 1; }
    echo "  clé API ... OK (OpenAI)" ;;
  ollama)
    echo "  clé API ... OK (aucune — Ollama local)" ;;
esac

echo -n "  dépendance ... "
if [[ "$PROVIDER" == "anthropic" ]]; then
  PYTHONPATH=src python -c "import anthropic" 2>/dev/null || { echo "FAIL — pip install -e '.[anthropic]'"; exit 1; }
elif [[ "$PROVIDER" == "ollama" ]]; then
  PYTHONPATH=src python -c "from aion.providers.ollama_provider import OllamaProvider; OllamaProvider()" 2>/dev/null || {
    echo "FAIL — Ollama non joignable (ollama serve + ollama pull llama3.2)"
    exit 1
  }
else
  PYTHONPATH=src python -c "import openai" 2>/dev/null || { echo "FAIL — pip install -e '.[openai]'"; exit 1; }
fi
echo "OK"

echo ""
echo "=== Lancement ($MODE / $PROVIDER) ==="
STAMP=$(date -u +%Y%m%dT%H%M%S)
OUTDIR="results/${MODE}_${PROVIDER}_${STAMP}"
mkdir -p "$OUTDIR"

if [[ "$MODE" == "micro" ]]; then
  PYTHONPATH=src python -m aion bench \
    --provider "$PROVIDER" --micro \
    --entree paraphrase --extracteur llm \
    --budget-appels 40 --cout-appel 0.01 \
    --out "$OUTDIR"
else
  echo "ATTENTION: campagne complète — jusqu'à 800 appels."
  read -r -p "Confirmer (oui/non) ? " CONFIRM
  [[ "$CONFIRM" == "oui" ]] || { echo "Annulé."; exit 0; }
  PYTHONPATH=src python -m aion bench \
    --provider "$PROVIDER" \
    --entree paraphrase --extracteur llm \
    --reps 20 --budget-appels 800 --cout-appel 0.01 \
    --out "$OUTDIR"
fi

echo ""
echo "=== Terminé ==="
echo "Dossier: $OUTDIR"
ls -la "$OUTDIR"
echo "Lire: cat $OUTDIR/*.md"
