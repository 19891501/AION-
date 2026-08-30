# Écosystème AION — multi-hébergement

## Dépôts

| Dépôt | URL | État |
|-------|-----|------|
| **AION-** (hub + Render) | https://github.com/19891501/AION- | **Production** |
| **aion-core** | https://github.com/19891501/aion-core | **Kernel greffé** (behavior, veritas, arbitre, ledger, pipeline) |
| **aion-bench** | https://github.com/19891501/aion-bench | **Mesure greffée** (metrics, arms, S2 ref) |
| **aion-vision** | https://github.com/19891501/aion-vision | Vision gelée (docs) |
| **aion-archive** | https://github.com/19891501/aion-archive | Inventaire hors preuve |

## Flux de dépendance

```
aion-core  (stdlib only)
    ↑
aion-bench  (importe core pour bras AION)
    ↑
AION- hub   (assemble + web + deploy Render)
```

## Règles

1. Core ne dépend de rien d'autre.
2. Bench n'implémente pas le kernel.
3. Vision n'exporte pas de code prod.
4. Archive n'est jamais importée.
5. Render reste sur **AION-**.

## Greffe effectuée (2026-08-30)

- [x] Modules kernel → aion-core
- [x] Metrics / arms / S2 ref → aion-bench
- [x] Docs world/federation → aion-vision
- [x] Inventaire → aion-archive
- [ ] Découpage complet hub (optionnel, non bloquant pour S2)
