# PROGRAMME AION — méthode chirurgicale (gelé)

**Règle unique :** aucune déviation, aucun module hors liste, ordre strict.

```text
🔒 NO NEW MODULE hors de ce programme
```

---

## Objectif domaine

Devenir la référence **Authorization Runtime for AI** :
intelligence propose → preuve → autorité → effet monde (chemin unique).

Critère de succès : **preuves expérimentales + enforcer obligatoire**, pas la taille de l’architecture.

---

## Horizon

### J0–J7 (cette semaine) — VERROU REPRO + MICRO RÉEL

| # | Action | Done when |
|---|--------|-----------|
| 1 | GitHub = local (runner, cases, calibration, CLI) | clone + `aion bench --micro` exécutable |
| 2 | Micro Anthropic réel | artifact JSON sur Actions |
| 3 | Corriger anomalies micro (budget partagé / appels extract) | 3 bras avec appels_extraction cohérents |
| 4 | Documenter micro (non opposable) | RESULTS.md mis à jour |
| 5 | Lancer **S2** (20 reps, paraphrase, llm, ≤800 appels) | rapport + empreinte pré-reg |

**Interdit cette semaine :** ORTHOGONAL, WWM, boîtier, téléphone, nouvelles règles R11+.

### S2–S4 (semaines 2–4) — VERROU NIVEAU 2

| # | Action | Done when |
|---|--------|-----------|
| 6 | Lire S2 vs seuils gelés | GO / SIMPLIFIER / NO-GO **écrit** |
| 7 | Si GO : réplication 2e provider | même protocole, 2e modèle |
| 8 | Si SIMPLIFIER : une seule correction ciblée | re-S2, pas 12 modules |
| 9 | Si NO-GO : post-mortem public | arrêt architecture, hypothèse révisée |
| 10 | Corpus externe (30–50 cas tiers) | `corpus_externe=true` possible |

### M2–M3 (mois 2–3) — VERROU NIVEAU 3 ENFORCER

| # | Action | Done when |
|---|--------|-----------|
| 11 | Contrat token d’autorisation (TTL, hash τ, usage unique) | spec + tests |
| 12 | Enforcer logiciel : **tout** tool_call passe par Authorization | 0 canal parallèle en lab |
| 13 | Bench Agent vs Agent+AION (même tâche) | tableau unsafe / useful / cost |
| 14 | Attack bench (ignore policy, replay, side-channel) | taux d’effet = 0 sur chemins protégés |

### M4–M6 (mois 4–6) — HARDWARE / PRODUIT

| # | Action | Done when |
|---|--------|-----------|
| 15 | Hardware gate (proxy / Pi) seulement si 11–14 verts | chemin physique unique |
| 16 | AION Box = support du même kernel | pas un nouveau cerveau |
| 17 | Multi-tool agent réel sous enforcer | démo 30 s Decision Theater + preuves |

---

## Décision S2 (rappels gelés — ne pas retoucher)

- AION−RAW ≥ 0.15 **et** AION−SCAFFOLD ≥ 0.10  
- faux succès ≤ 0.15 · faux refus ≤ 0.05  
- gain ≥ 3 familles dont `repeated_error`, `stale_knowledge`  
Sinon SIMPLIFIER ou NO-GO.

---

## Méthode d’exécution (sans te relancer)

À chaque session :

1. Lire ce fichier  
2. Faire **uniquement** la plus petite tâche non cochée  
3. Mesurer / commit / artifact  
4. Ne pas ouvrir une idée hors programme  

Si blocage technique : corriger le blocage, **pas** contourner par une nouvelle couche.

---

## État au 2026-09-05

| Item | Statut |
|------|--------|
| 1 Sync runner GitHub | Fait |
| 2 Micro Anthropic | **Fait** (run 33951082661) — non opposable |
| Micro chiffres (indicatifs) | RAW 0.30 · SCAFFOLD 0.35 · AION 0.32 |
| Anomalie | SCAFFOLD/AION `appels_extraction=0` — **à corriger avant S2** |
| 5 S2 20 reps | **Suivant après fix budget/extract** |

---

*Ce programme est la feuille de route unique. Toute demande hors liste = report après le verrou en cours.*
