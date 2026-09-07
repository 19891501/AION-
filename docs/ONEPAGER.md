# AION — Authorization Infrastructure for Autonomous AI

**AI can think. AION decides whether it may act.**

---

## The problem after ChatGPT

Models generate decisions fluently. Agent stacks turn those decisions into **tool calls**.  
Nothing in the default loop asks:

> *Is this transition justified enough to change the world?*

Guardrails filter text. Allowlists filter tools.  
Neither formalizes **authority over state change**.

---

## The primitive

```
τ : S → S'     proposed transition
α ⇏ EXECUTE    intelligence ≠ authority
```

```
Authorized(τ)  ⇔  Arbiter( Veritas(c, E), κ ) = EXECUTER
```

under ARCHÉ invariants (append-only state, justified transitions, no silent proof).

| Layer | Role |
|-------|------|
| ChatGPT-class models | Human ↔ Intelligence |
| Grok-class models | Intelligence ↔ Truth |
| **AION** | Intelligence ↔ **Action / Authority** |

---

## What ships

| Artifact | Status |
|----------|--------|
| Deterministic kernel (R0–R10, Veritas, Arbiter, Ledger) | Implemented |
| Transition Spec v0.1 | Published |
| Decision Theater (30s demo) | Live HTML |
| Pre-registered bench RAW / SCAFFOLD / AION | Runnable |
| Kernel ceiling (exact flags, 20 cases) | **BAR AION = 1.00**, FA=FR=0 |
| Opposable S2 (real model, paraphrase) | Next — not claimed yet |

**Honest reading:** when observation is perfect, the authorization kernel is consistent.  
When observation is noisy, gain shrinks — that is a measurement result, not a marketing line.

---

## Integration model

```
YOUR AGENT  →  propose_transition(τ)  →  AION  →  AUTHORIZED | VERIFY | HUMAN | REFUSED
                                                      ↓
                                              only then: tool / world effect
```

Not a replacement for LangGraph, Temporal, or MCP.  
A **coprocessor of authority** in front of side effects.

---

## The standard we want in five years

Engineer question shifts from:

> “What prompt did you use?”

to:

> “What is the **authorization policy** for this transition?”

Answer: a runtime that treats **reality transitions** as first-class, auditable objects.

---

## Attack us

Spec · invariants · pre-registration · H0 publishable · open kernel.  
If S2 fails, AION changes — the claim does not get rewritten to survive.

`docs/AION_TRANSITION_SPEC_v0.1.md` · `docs/TRANSITION_LOGIC.md` · Theater · bench
