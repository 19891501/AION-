# AION — Logique formelle des transitions

> Unité fondamentale : la **transition autorisée**.
> Aucune mutation du monde n'est exécutée sans satisfaire des conditions
> explicites de vérité, d'état, de politique et d'autorité.

Ce document formalise ce que le code mécanise déjà (constitution ARCHE,
ledger, behavior, veritas, arbitre) et ce que S2/S3 doivent mesurer.

---

## 0. Alphabet

| Symbole | Signification |
|---------|----------------|
| \(S\) | État du monde (projection via ledger + observations) |
| \(\tau\) | Transition proposée (intention + action candidate) |
| \(E\) | Ensemble d'évidences |
| \(V\) | Verdict Veritas : PROOF, FAIL, UNKNOWN, CONFLICT |
| \(\alpha\) | Action cognitive Behavior (ANSWER, ASK, SEARCH, VERIFY, …) |
| \(\delta\) | Décision Arbitre (EXECUTER, TESTER, DEMANDER_HUMAIN, NO_ACTION, ABANDONNER) |
| \(\kappa\) | Enjeu (stake) : réversibilité, coût, seuil humain, test disponible |
| \(L\) | Ledger append-only |

Statuts de fait dans L : UNKNOWN, HYPOTHESIS, VERIFIED, REJECTED, CONFLICTED, OBSOLETE.

Statuts de **preuve** (exigent une source, loi A4) : VERIFIED, REJECTED, CONFLICTED.

---

## 1. Lois ARCHÉ (invariants)

| Code | Énoncé | Forme opérationnelle |
|------|--------|----------------------|
| **A1** | Aucune mutation directe d'un état existant | Seul `append` ; jamais d'écrasement in-place |
| **A2** | Tout état possède un prédécesseur explicite | `revise(f)` exige `head(f) ≠ ⊥` |
| **A3** | Toute transition est justifiée | `justification ≠ ε` |
| **A4** | Aucun passage silencieux vers un statut de preuve | `status' ∈ Statuts_preuve ⇒ source ≠ ε` |

**Corollaire A4+** : même depuis HYPOTHESIS, passage à VERIFIED/REJECTED/CONFLICTED sans source interdit.

Intégrité de chaîne :

```
verify_chain(L) ⇔ ∀i: hash_i = H(payload_i) ∧ prev_hash_i = hash_{i-1}
```

---

## 2. Transition proposée

```
τ = ⟨ S, q, α★, c, κ ⟩
```

- `q` : intention / question
- `α★` : action candidate (non autorisée)
- `c` : claim (« autoriser l'exécution de … »)
- `κ` : stake

**Règle fondatrice :**

```
α★  ⇏  EXECUTER
```

L'intention ne confère aucun droit d'agir.

---

## 3. Pipeline de décision

```
τ  ─Behavior→  α  ─Veritas→  V  ─Arbitre→  δ  ─Gate→  S' ou S
```

### 3.1 Behavior (déterministe)

```
Behavior(q, flags, L) → ⟨α, règle R0–R10, motif⟩
```

Ordre strict (première règle vraie) :

| Règle | Condition | α |
|-------|-----------|---|
| R0 | hors_domaine | REFUSE |
| R1 | premisse_fausse | CLARIFY |
| R2 | ambigu ∧ autorité_utilisateur | ASK |
| R3 | ambigu | CLARIFY |
| R4 | sources_divergentes | COMPARE |
| R5 | fait ∈ {REJECTED, CONFLICTED} | VERIFY |
| R6 | fait = OBSOLETE | SEARCH |
| R7 | connaissance datée + source externe | SEARCH |
| R8 | connaissance datée sans source | DEFER |
| R9 | consequence_reelle | VERIFY |
| R10 | sinon | ANSWER |

Invariant : mêmes entrées ⇒ même α.

### 3.2 Veritas

```
Veritas(c, E, θ_âge) → V
```

1. Filtrer E* = trusted ∧ âge ∈ [0, θ]
2. Dédupliquer par (source, supports)
3. Règles :
   - pour ∧ contre → CONFLICT
   - contre seulement → FAIL
   - pour seulement → PROOF
   - sinon → UNKNOWN

Invariant : UNKNOWN n'est jamais promu en PROOF par défaut.

### 3.3 Arbitre

```
Arbitre(V, κ) → δ
```

| Condition | δ |
|-----------|---|
| coût non fini ou < 0 | DEMANDER_HUMAIN |
| V = FAIL | NO_ACTION |
| V = CONFLICT | DEMANDER_HUMAIN |
| V = UNKNOWN ∧ test dispo | TESTER |
| V = UNKNOWN ∧ ¬test | DEMANDER_HUMAIN |
| V = PROOF ∧ (¬réversible ∨ coût > seuil) | DEMANDER_HUMAIN |
| V = PROOF ∧ réversible ∧ coût ≤ seuil | EXECUTER |

### 3.4 Gate

```
Authorized(τ)  ⇔  δ(τ) = EXECUTER
```

Seul EXECUTER peut produire un effet monde hors append de trace.

---

## 4. Transitions de fait dans le ledger

`Transition_L(f, σ → σ', j, s)` est **légale** ssi :

1. σ' ∈ Statuts
2. j ≠ ε (A3)
3. σ' ∈ Statuts_preuve ⇒ s ≠ ε (A4)
4. revise ⇒ head(f) existe (A2)
5. opération = append (A1)

**Interdit :** UNKNOWN --(sans source)→ VERIFIED

---

## 5. Non-élision (trace obligatoire)

```
¬Authorized(τ)  ⇏  silence
```

Toute décision produit :

```
Trace(τ) = ⟨ q, α, R, V, δ, motif, t, H ⟩
```

C5–C6 : refus / humain = succès si l'action n'était pas justifiée.

---

## 6. Boucle épistémique (S3 — hors périmètre S2)

Quand δ ∈ {TESTER, VERIFY path, SEARCH, CLARIFY, DEMANDER_HUMAIN} :

```
U  = Uncertainty(S, τ)
o* = NextObservation(U)
E' = E ∪ Observe(o*)
S+ = Update(S, E')
     → reprendre le pipeline avec (S+, τ)
```

S2 mesure le gate à E et S **donnés**.  
S3 mesure le choix de o*.

---

## 7. Critères empiriques (S2)

```
BAR = |{τ : α(τ) = α_attendu(τ)}| / |T|
```

Calibration : FA, FR, surblocage, sousblocage (voir `bench/calibration.py`).

H1 : gain vs RAW et SCAFFOLD + familles + seuils de calibration (pré-enregistrement v3).

---

## 8. Théorèmes-cibles

| Id | Énoncé | Statut |
|----|--------|--------|
| **T1** | Séparation intention/autorité : ∃ τ où ReAct agirait et AION bloque | Démo + Theater |
| **T2** | Monotonie : évidence contre fiable ne crée pas PROOF | Mécanique Veritas |
| **T3** | Non-promotion UNKNOWN→VERIFIED sans source | Mécanique A4 / ledger |
| **T4** | Utilité : BAR_AION − BAR_SCAFFOLD ≥ θ sous S2 | **Objet de S2** |

---

## 9. Forme compacte

```
S' = S    sauf si Authorized(τ)

Authorized(τ)  ⇔  Arbitre( Veritas(c, E), κ ) = EXECUTER
```

sous contraintes ARCHÉ A1–A4 sur tout écrit dans L.

---

## 10. Lien code

| Formalisme | Module |
|------------|--------|
| A1–A4 | `constitution.py`, `ledger.py` |
| Behavior | `behavior.py` |
| Veritas | `veritas.py` |
| Arbitre | `arbitre.py` |
| Pipeline | `pipeline.py` |
| Calibration | `bench/calibration.py` |
| Pré-enregistrement | `preenregistrement.json` |

