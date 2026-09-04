# Marche 0 — Dry-run kernel (carte blanche)

**Date :** 2026-09-04  
**Provider :** offline (0 appel LLM payant)  
**Statut S2 :** `FROZEN_NOT_RUN` — non opposable au pré-enregistrement.

## Empreintes

| Objet | SHA256 |
|-------|--------|
| preenregistrement.json | `147838769f0cd730d2d4284630f40e62590a45436cb64f6dbcb2e6cf88166bb6` |
| Corpus 20 cas | `be55100a9349475bc6e8baf66abfb7b0346af71b32b4895e39db9540578ee4cf` |

## Mode A — drapeaux (plafond kernel)

| Bras | BAR | Faux succès |
|------|-----|-------------|
| RAW | 0.300 | 0.45 |
| SCAFFOLD | 0.300 | 0.45 |
| **AION** | **1.000** | **0.00** |

Écarts : AION−RAW = **+0.70** · AION−SCAFFOLD = **+0.70**

## Mode B — paraphrase + lexical (frontière perception)

| Bras | BAR | Faux succès |
|------|-----|-------------|
| RAW | 0.300 | 0.45 |
| SCAFFOLD | 0.300 | 0.45 |
| **AION** | **0.500** | **0.35** |

Écarts : AION−RAW = **+0.20** · AION−SCAFFOLD = **+0.20**

## Lecture

1. Observation parfaite → AION plafonne à 1.00 ; RAW/SCAFFOLD restent à 0.30.
2. Perception naïve → AION retombe à 0.50 (frontière connue).
3. S2 confirmatoire = paraphrase + llm + 20 reps sous budget 800 — **pas encore lancé**.
4. Pré-reg inchangé.
