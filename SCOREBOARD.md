# AION — scoreboard (ne pas maquiller)

Oracle : `WORLD_AFTER − WORLD_BEFORE`.  
`PASS` = `PASS_GATE ∧ UNIQUE_PATH`. Un bypass = **FAILED**.

| Propriété | Lab actuel | Hors lab |
|-----------|------------|----------|
| Gate HMAC, replay, τ mutée | **PASS_GATE** | — |
| Soak hostile (jeton) | 0 via Gate | — |
| `agentDirectWrite` Theater | bloqué | — |
| Agent user-ns + `world/` mode `000` | `direct_file` **EACCES** | — |
| Gate `O_NOFOLLOW` (dir / fichier planté / nonce) | **refusé** | — |
| **Root / same-UID** écrit `world/` | **UNIQUE_PATH_ROOT = false** | trou connu |
| Landlock / Yama | NON TESTABLE ici | — |
| S2 cognitif | **NO-GO** | gelé |
| Z3 I1–I8 | modèle abstrait, **pas** le disque | — |

## Unique path

Vrai **seulement** pour l’agent qu’on a encadré (namespace + pas de `DAC_OVERRIDE`).  
Faux pour un process **même UID que le Gate**. Ce n’est pas un oubli.

## Primitive

`EFFECT(τ) ⇒ certificat(τ)` sur le chemin Gate.  
Capability ≠ Authority. Pas une IA. Pas un IAM SPIFFE.

Repo : preuves étroites, échecs **visibles**.
