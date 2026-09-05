"""AION Runtime — intention → preuve → autorité → effet (chemin unique)."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any
from .arbitre import Decision, Stake, arbitrer
from .enforcer import Authorization, EffectResult, Enforcer, Transition
from .veritas import Evidence, Ruling, check

@dataclass
class Proposal:
    claim: str
    tau: Transition
    evidences: list[Evidence] = field(default_factory=list)
    stake: Stake = field(default_factory=lambda: Stake(cout=0.0))

@dataclass
class RuntimeTrace:
    ruling: Ruling
    decision: Decision
    motif: str
    auth_issued: bool
    effect: int
    reason: str
    transition_hash: str

class AionRuntime:
    def __init__(self, enforcer: Enforcer) -> None:
        self.enforcer = enforcer
        self.traces: list[RuntimeTrace] = []

    def submit(self, proposal: Proposal) -> RuntimeTrace:
        ruling = check(proposal.claim, proposal.evidences)
        arb = arbitrer(ruling, proposal.stake)
        auth_issued = False
        if arb.decision is Decision.EXECUTER:
            auth = self.enforcer.issue(proposal.tau)
            auth_issued = True
            result = self.enforcer.execute(proposal.tau, auth)
        else:
            result = self.enforcer.execute(proposal.tau, None)
        trace = RuntimeTrace(ruling, arb.decision, arb.motif, auth_issued, result.effect, result.reason, proposal.tau.hash())
        self.traces.append(trace)
        return trace

    def bypass_attempt(self, tau: Transition, auth: Authorization | None = None) -> EffectResult:
        return self.enforcer.execute(tau, auth)

def demo_transfer_10000() -> dict[str, Any]:
    world: list[str] = []
    rt = AionRuntime(Enforcer(b"aion-runtime-demo", world=lambda t: world.append(t.canonical())))
    tau = Transition("agent", "transfer", "iban-BENEF", {"amount_eur": 10000})
    tr = rt.submit(Proposal(
        claim="Le beneficiaire IBAN est conforme au contrat",
        tau=tau,
        evidences=[Evidence("bank", True, 0, True), Evidence("compliance", False, 0, True)],
        stake=Stake(reversible=False, cout=10000.0, seuil_humain=50.0),
    ))
    bypass = rt.bypass_attempt(tau, None)
    return {
        "scenario": "transfer_10000_conflict",
        "veritas": tr.ruling.verdict.value,
        "arbitre": tr.decision.value,
        "effect_via_runtime": tr.effect,
        "effect_bypass": bypass.effect,
        "world_mutations": len(world),
        "pass": tr.effect == 0 and bypass.effect == 0 and len(world) == 0,
    }
