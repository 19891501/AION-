# AION Transition Spec v0.1

**Status:** Normative draft · 2026-09-01  
**Implements:** AI Transition Control — authorization runtime for proposed state changes  
**Non-goals:** Model quality, multi-agent chat, RAG product features  

---

## 1. Purpose

AION mediates the boundary between **intelligence** (any proposer) and **reality** (effects on the world).

```
INTELLIGENCE ≠ AUTHORITY
α ⇏ EXECUTE
```

A proposer (LLM, robot, human, program) may **propose** a transition.  
Only an **authorized** transition may change the world outside an audit trace.

---

## 2. Core types

### 2.1 State `S`
Projection of facts relevant to decisions (ledger heads + observations).  
Facts carry status: `UNKNOWN | HYPOTHESIS | VERIFIED | REJECTED | CONFLICTED | OBSOLETE`.

### 2.2 Proposed transition `τ`

```
τ = ⟨ S, q, α★, c, κ ⟩
```

| Field | Meaning |
|-------|---------|
| `S` | Current state snapshot |
| `q` | Intention / natural-language request |
| `α★` | Candidate cognitive or effectful action |
| `c` | Claim to justify (“authorize execution of …”) |
| `κ` | Stake: reversible, cost, human threshold, test available |

### 2.3 Evidence set `E`
Each evidence: `source`, `supports: bool`, `age_days`, `trusted`.

### 2.4 Outcomes
- **Cognitive action** `α` ∈ {ANSWER, ASK, SEARCH, VERIFY, COMPARE, CLARIFY, WAIT, EXPERIMENT, REFUSE, DEFER}
- **Verdict** `V` ∈ {PROOF, FAIL, UNKNOWN, CONFLICT}
- **Decision** `δ` ∈ {EXECUTER, TESTER, DEMANDER_HUMAIN, NO_ACTION, ABANDONNER}

---

## 3. ARCHÉ invariants (MUST)

| ID | Rule | Enforcement |
|----|------|-------------|
| **A1** | No in-place mutation of recorded state | append-only ledger |
| **A2** | Revision requires explicit predecessor | `revise` fails if no head |
| **A3** | Every ledger transition has non-empty justification | reject empty justification |
| **A4** | Proof-status requires non-empty source | VERIFIED/REJECTED/CONFLICTED need `source` |

Implementations MUST raise on violation. Silent repair is non-conformant.

---

## 4. Decision pipeline (MUST)

```
τ → Behavior → α → Veritas → V → Arbiter → δ → Gate
```

### 4.1 Behavior
Deterministic map `(q, flags, L) → α` with ordered rules R0–R10  
(same inputs ⇒ same `α`). First matching rule wins.

### 4.2 Veritas
```
usable = trusted ∧ age ∈ [0, θ]
dedupe by (source, supports)
pour ∧ contre → CONFLICT
contre only → FAIL
pour only → PROOF
else → UNKNOWN
```
MUST NOT promote UNKNOWN to PROOF without new supporting evidence.

### 4.3 Arbiter
Maps `(V, κ) → δ`. High stakes or irreversible + PROOF still MAY require human.  
FAIL → NO_ACTION. CONFLICT → human or block. UNKNOWN → TESTER or human.

### 4.4 Gate (normative)

```
Authorized(τ)  ⇔  δ = EXECUTER
```

Only then MAY side effects outside audit logging occur.

---

## 5. Trace (MUST)

Every decision produces an auditable trace:

```
Trace = ⟨ q, α, rule, V, δ, motif, timestamp, hash ⟩
```

`¬Authorized` MUST NOT be silent.

---

## 6. Conformance profiles

| Profile | Requirements |
|---------|----------------|
| **AION-Kernel** | A1–A4, Behavior, Veritas, Arbiter, Gate, Trace |
| **AION-Bench** | Kernel + RAW/SCAFFOLD/AION arms + frozen pre-registration + BAR + calibration |
| **AION-Runtime** | Kernel + `propose_transition` API returning AUTHORIZED \| VERIFY \| HUMAN \| REFUSED |

---

## 7. API sketch (Runtime profile)

```
POST /v1/transitions
{
  "intention": "...",
  "flags": { ... },
  "claim": "...",
  "evidences": [ ... ],
  "stake": { "reversible": true, "cost": 0, "seuil_humain": 50 }
}

→ {
  "authorized": false,
  "decision": "DEMANDER_HUMAIN",
  "behavior": { "action": "VERIFY", "rule": "R9" },
  "veritas": { "verdict": "CONFLICT", ... },
  "trace_id": "..."
}
```

Side-effecting tools MUST be invoked only if `authorized: true`.

---

## 8. Explicitly out of scope (v0.1)

- Optimal next observation (S3)
- Multi-agent orchestration protocols (A2A as transport only)
- Training or fine-tuning models
- Guaranteeing model honesty (AION gates action, does not certify beliefs)

---

## 9. Versioning

Breaking changes to Authorized(τ) semantics or ARCHÉ bump major version.  
Additive calibration metrics or adapters: minor.

**v0.1** freezes the contract above. Implementation: this repository’s kernel modules.

