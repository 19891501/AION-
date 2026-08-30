# Offline MCP — sans Ollama, sans cloud

Remplace le travail d’un modèle local/cloud **pour exercer le circuit de mesure**.

## Ce que c’est

| Mode | Commande |
|------|----------|
| Provider direct | `aion bench --provider offline` |
| Faux Ollama (port 11434) | `aion offline serve` puis `--provider ollama` |
| Test rapide | `aion offline ping` |

## Ce que ce n’est pas

- **Pas** un frontier model
- **Pas** un résultat opposable S2
- Heuristiques déterministes (extraction JSON + scaffold)

## Micro-campagne 2026-08-30 (offline + llm extracteur)

| Bras | BAR |
|------|-----|
| RAW | 0.200 |
| SCAFFOLD | 0.267 |
| AION | 0.267 |

Drapeaux exacts ≈ 0 : l’extracteur heuristique ne matche pas encore le corpus paraphrase — **signal utile** (le banc mesure vraiment l’extraction).

Même chiffre en passant par l’API Ollama fake → le drop-in fonctionne.

## Usage

```bash
# terminal 1
PYTHONPATH=src python -m aion offline serve --port 11434

# terminal 2
PYTHONPATH=src python -m aion bench --provider ollama --micro \
  --entree paraphrase --extracteur llm --out results/offline_mcp

# ou sans serveur
PYTHONPATH=src python -m aion bench --provider offline --micro \
  --entree paraphrase --extracteur llm
```
