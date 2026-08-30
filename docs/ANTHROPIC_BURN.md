# Burn crédit Anthropic (expire 1er septembre)

## Stratégie 29 USD

| Choix | Pourquoi |
|-------|----------|
| **Haiku** par défaut | ~10–50× moins cher que Sonnet → plus d’appels, meilleur signal statistique |
| **Cache** | Rejouabilité + pas de double facturation des mêmes prompts |
| **Budget-appels** | Stop avant explosion |
| Micro → étendu → reps | Toujours un rapport même si le crédit tombe à 0 |

## Lancer (chez toi)

```bash
export ANTHROPIC_API_KEY="sk-ant-..."   # JAMAIS dans le chat / git
pip install anthropic
cd AION-
bash scripts/run_anthropic_burn.sh
```

Sonnet (qualité, moins d’appels) :

```bash
export AION_MODEL="claude-sonnet-4-6"
bash scripts/run_anthropic_burn.sh
```

## Ordre de grandeur

- Micro (5 cas × 3 reps) : dizaines d’appels
- Étendu 20×5 : centaines d’appels
- Haiku : 29 $ = **beaucoup** d’extractions courtes
- Sonnet : plutôt **centaines** d’appels utiles

## Après

Envoie uniquement le tableau BAR (RAW / SCAFFOLD / AION) + `provider` + `modele` + n cas/reps — **pas** la clé.
