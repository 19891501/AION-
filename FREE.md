# Mode gratuit (0 €)

Tout ce qui suit **ne consomme aucune API payante**.

## Ce qui tourne gratuitement

| Couche | Commande | Résultat type |
|--------|----------|---------------|
| Kernel drapeaux | `aion bench --provider mock --entree drapeaux --extracteur lexical --reps 1` | AION BAR=1.00 |
| Perception | paraphrase + lexical | AION BAR≈0.50 |
| Circuit bruit | `--provider simule` | non opposable |
| Auth-bench | `python scripts/run_auth_bench.py` | 23/23 |
| **Enforcer + attack** | `pytest tests/test_enforcer_free.py` | 0 effet non autorisé |

## Providers 0 €

- `mock` — déterministe CI
- `simule` — bruit offline
- `offline_mcp` — API locale style Ollama si dispo
- `ollama` — si tu installes Ollama + modèle local (gratuit, chez toi)

## Payant (optionnel)

`anthropic` / `openai` / `grok` — uniquement pour S2 opposable multi-LLM.

## Principe

> Preuve et enforcer d'abord en 0 €. Cloud seulement pour H1 multi-modèle.
