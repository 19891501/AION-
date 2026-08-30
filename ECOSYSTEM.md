# Écosystème AION — multi-hébergement + fusion chirurgicale

## Carte des dépôts

| Dépôt | URL | Rôle |
|-------|-----|------|
| **AION-** (hub) | https://github.com/19891501/AION- | Fusion opérationnelle + Render |
| **aion-core** | https://github.com/19891501/aion-core | Kernel (behavior, veritas, arbitre) |
| **aion-bench** | https://github.com/19891501/aion-bench | Mesure S2, BAR, corpus |
| **aion-vision** | https://github.com/19891501/aion-vision | Vision **gelée** (docs) |
| **aion-archive** | https://github.com/19891501/aion-archive | Apps / ZIP hors preuve |
| Aion (privé) | https://github.com/19891501/Aion | Historique / miroir |

```
        aion-vision (GELÉ)
              │
              │  docs only
              ▼
 aion-core ◄──── AION- (hub + deploy) ────► aion-bench
              │
              ✗ pas d'import
              ▼
        aion-archive
```

## Règles de fusion

1. **Core ← lignée noyau ZIP** uniquement (s1…x-final, synapse, noyau).
2. **Bench ← aion-100 + research + pré-enregistrement** ; importe core, ne le réécrit pas.
3. **Vision** : zéro code exécutable de production jusqu’à verdict S2.
4. **Archive** : pas d’import vers core/bench ; extraction chirurgicale max 1 idée / PR.
5. **Hub AION-** : assemble core+bench pour l’API/UI Render ; reste la source de deploy.

## Prochaines greffes (ordre)

1. Extraire `src/aion/{behavior,veritas,arbitre,ledger,pipeline}.py` → `aion-core`
2. Extraire `bench/`, `preenregistrement`, `audit` → `aion-bench`
3. Déposer MAP/PROTOCOL des ZIP vision → `aion-vision/docs/`
4. Lister les ZIP business dans `aion-archive/INVENTORY.md`
5. Garder Render branché sur **AION-** jusqu’à stabilisation des packages

## Anti-patterns

- Un monorepo géant type atlas **maintenant**
- Fusionner platform-engine-v2 dans le kernel
- Modifier les seuils S2 depuis core
- « Tout mettre dans un repo pour simplifier »
