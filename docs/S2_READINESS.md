# S2 readiness — diagnostic ZIP vs workspace

## Verdict sur un ZIP « en retard »

| Dimension | Note |
|-----------|------|
| Prototype technique | 7.5/10 |
| Architecture | 8/10 |
| Maturité expérimentale | 5/10 |
| Prêt S2 opposable | **pas encore** (ZIP) |

## Écarts typiques d’un ZIP incomplet

1. `runner.py` → `NotImplementedError` (campagne/comparer/ecrire manquants)
2. `cases.py` → 3 demos au lieu de **20 cas** S2
3. Pas de `Calibration` (faux_refus, surblocage, rappel)
4. `preenregistrement.json` sans gain multi-familles
5. SCAFFOLD trop faible (1 ligne) → contestable vs AION

## Workspace / hub (corrigé)

- Runner complet présent
- **20 cas** (6 familles)
- `Compteurs` publie calibration complète
- H1 : familles_gain_minimum=3 + repeated_error + stale_knowledge
- SCAFFOLD : prompt prudent (VERIFY/CLARIFY/REFUSE explicites)
- Empreinte S2 **change** après MAJ prereg → voulu

## Ne pas brûler 800 appels avant

1. Dry-run mock/local (0 €)
2. Vérifier rapport JSON contient `taux_faux_refus`, `bar_par_famille`
3. Micro Anthropic (budget bas)
4. Puis S2 si circuit OK

## Question ultime (rappel)

SCAFFOLD doit être assez fort pour qu’on ne puisse pas dire :
« AION gagne parce que le baseline est sous-prompté. »
