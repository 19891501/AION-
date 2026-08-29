#!/bin/bash
# Restaure le code source complet AION v0.1.0 depuis les parties base64
set -euo pipefail
cd "$(dirname "$0")/.."
cat dist/zip_part_*.txt | base64 -d > aion-0.1.0-github.zip
unzip -o aion-0.1.0-github.zip
echo "OK — puis: pip install -e '.[dev]' && aion status"
