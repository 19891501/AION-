# AION Transition Spec v0.1

**Status:** Normative draft · 2026-09-01  
**Category:** AI Transition Control — authorization runtime for proposed state changes

## Purpose

```
INTELLIGENCE ≠ AUTHORITY
α ⇏ EXECUTE
```

A proposer may **propose** a transition. Only an **authorized** transition may change the world outside an audit trace.

## Core

```
τ = ⟨ S, q, α★, c, κ ⟩
Authorized(τ) ⇔ Arbiter(Veritas(c,E), κ) = EXECUTER
```

## ARCHÉ (MUST)

- **A1** append-only (no in-place mutation)
- **A2** revise requires predecessor
- **A3** non-empty justification
- **A4** proof-status requires source

## Pipeline (MUST)

```
τ → Behavior → α → Veritas → V → Arbiter → δ → Gate
```

Trace required on every decision. `¬Authorized` must not be silent.

## Profiles

| Profile | Requirements |
|---------|----------------|
| AION-Kernel | A1–A4, Behavior, Veritas, Arbiter, Gate, Trace |
| AION-Bench | Kernel + RAW/SCAFFOLD/AION + pre-registration + BAR + calibration |
| AION-Runtime | Kernel + propose_transition API |

## Out of scope v0.1

S3 next-observation, model training, multi-agent product features.

Full text: repository `docs/AION_TRANSITION_SPEC_v0.1.md` / `TRANSITION_LOGIC.md`.
