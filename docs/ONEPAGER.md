# AION — Authorization Infrastructure for Autonomous AI

**AI can think. AION decides whether it may act.**

## The problem after ChatGPT

Models generate decisions. Agents call tools. Nothing asks: *Is this transition justified enough to change the world?*

## The primitive

```
τ : S → S'
α ⇏ EXECUTE
Authorized(τ) ⇔ Arbiter(Veritas(c,E), κ) = EXECUTER
```

Intelligence ≠ Authority.

## Evidence (honest)

| Condition | BAR AION | Note |
|-----------|----------|------|
| Exact flags (kernel ceiling) | **1.00** | FA=FR=0, all families | 
| Paraphrase + lexical (noisy obs.) | ~0.50 | Gain shrinks — observation bottleneck |
| Opposable S2 (real model) | **not claimed** | Next experiment |

## Integration

```
agent → propose_transition(τ) → AION → AUTHORIZED | VERIFY | HUMAN | REFUSED → world
```

Coprocessor of authority. Not another agent framework.

## Five-year test

Engineers ask *authorization policy for this transition?* the way they ask about OAuth or TLS.

Spec: `AION_TRANSITION_SPEC_v0.1.md` · Attack the contract · H0 is publishable.
