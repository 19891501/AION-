"""AION Runtime — boucle unique : intention → preuve → autorité → effet.

Invention centrale du projet :
  l'intelligence peut proposer une transition τ ;
  seul ce runtime peut la rendre effective sur le chemin protégé.

Coût : 0 € (pas de LLM requis).
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .arbitre import Decision, Stake, arbitrer
from .enforcer import Authorization, EffectResult, Enforcer, Transition
from .veritas import Evidence, Ruling, check


@dataclass
class Proposal:
    """Ce que l'agent demande au monde."""

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
    """Porte unique.

    flow:
      proposal
        → Veritas(claim, evidences)
        → Arbitre(ruling, stake)
        → si EXECUTER : issue(token) → enforcer.execute
        → sinon : effect = 0
    """

    def __init__(self, enforcer: Enforcer) -> None:
        self.enforcer = enforcer
        self.traces: list[RuntimeTrace] = []

    def submit(self, proposal: Proposal) -> RuntimeTrace:
        ruling = check(proposal.claim, proposal.evidences)
        arb = arbitrer(ruling, proposal.stake)

        auth: Authorization | None = None
        auth_issued = False
        if arb.decision is Decision.EXECUTER:
            auth = self.enforcer.issue(proposal.tau)
            auth_issued = True
            result: EffectResult = self.enforcer.execute(proposal.tau, auth)
        else:
            # Toute tentative d'effet sans EXECUTER est refusée au niveau enforcer
            result = self.enforcer.execute(proposal.tau, None)

        trace = RuntimeTrace(
            ruling=ruling,
            decision=arb.decision,
            motif=arb.motif,
            auth_issued=auth_issued,
            effect=result.effect,
            reason=result.reason if not auth_issued else result.reason,
            transition_hash=proposal.tau.hash(),
        )
        self.traces.append(trace)
        return trace

    def bypass_attempt(self, tau: Transition, auth: Authorization | None = None) -> EffectResult:
        """L'agent essaie d'atteindre le monde sans repasser par submit()."""
        return self.enforcer.execute(tau, auth)


def serve_mcp_stdio() -> int:
    """MCP JSON-RPC. L'agent n'a pas d'outil d'effet — seulement aion_propose."""
    import json
    import os
    import sys

    secret = os.environ.get("AION_ENFORCER_SECRET", "mcp-dev-not-for-prod").encode()
    world: list[str] = []
    rt = AionRuntime(Enforcer(secret, world=lambda t: world.append(t.canonical())))
    cadre = {
        "interdit": ["pirater", "exfiltrer", "drop_database"],
        "humain": ["transfer", "virement", "delete"],
        "plafond": 50.0,
        "principe": "Tout le reste est libre.",
    }
    tools = [
        {
            "name": "aion_get_cadre",
            "description": "Lit le contrat d'autonomie. L'agent ne l'écrit pas.",
            "inputSchema": {"type": "object", "properties": {}},
        },
        {
            "name": "aion_propose",
            "description": "Propose une transition τ. Aucun effet sans autorisation.",
            "inputSchema": {
                "type": "object",
                "required": ["intent", "action", "target"],
                "properties": {
                    "intent": {"type": "string"},
                    "action": {"type": "string"},
                    "target": {"type": "string"},
                    "amount": {"type": "number"},
                    "reversible": {"type": "boolean"},
                },
            },
        },
        {
            "name": "aion_journal",
            "description": "Dernières décisions de cette session MCP.",
            "inputSchema": {"type": "object", "properties": {}},
        },
    ]

    def read_msg() -> dict[str, Any] | None:
        first = sys.stdin.buffer.readline()
        if not first:
            return None
        if first.lstrip().startswith(b"{"):
            return json.loads(first.decode("utf-8"))
        headers: dict[str, str] = {}
        line = first
        while True:
            if line in (b"\r\n", b"\n"):
                break
            raw = line.decode("utf-8").strip()
            if ":" in raw:
                k, v = raw.split(":", 1)
                headers[k.strip().lower()] = v.strip()
            line = sys.stdin.buffer.readline()
            if not line:
                return None
        n = int(headers.get("content-length", "0"))
        if n <= 0:
            return None
        return json.loads(sys.stdin.buffer.read(n).decode("utf-8"))

    def write_msg(msg: dict[str, Any]) -> None:
        blob = json.dumps(msg, ensure_ascii=False).encode("utf-8")
        sys.stdout.buffer.write(f"Content-Length: {len(blob)}\r\n\r\n".encode("ascii"))
        sys.stdout.buffer.write(blob)
        sys.stdout.buffer.flush()

    def tool_text(obj: Any, err: bool = False) -> dict[str, Any]:
        return {
            "content": [{"type": "text", "text": json.dumps(obj, ensure_ascii=False, indent=2)}],
            "isError": err,
        }

    def propose(args: dict[str, Any]) -> dict[str, Any]:
        intent = str(args.get("intent", ""))
        action = str(args.get("action", ""))
        target = str(args.get("target", ""))
        amount = float(args.get("amount") or 0)
        hay = f"{intent} {action} {target}".lower()
        if any(x in hay for x in cadre["interdit"]):
            return {"effect": 0, "decision": "NO_ACTION", "motif": "Cadre · interdit"}
        tau = Transition("mcp-agent", action, target, {"amount": amount} if amount else {})
        stake = Stake(
            reversible=bool(args.get("reversible", True)) and amount <= 50,
            cout=amount,
            seuil_humain=50.0,
            plafond_global=cadre["plafond"],
        )
        if any(x in hay for x in cadre["humain"]) or amount > float(cadre["plafond"]):
            rt.enforcer.execute(tau, None)
            return {
                "effect": 0,
                "decision": "DEMANDER_HUMAIN",
                "motif": "Cadre · validation humaine ou plafond",
                "action": action,
                "target": target,
            }
        tr = rt.submit(Proposal(claim=intent or action, tau=tau, evidences=[], stake=stake))
        return {
            "effect": tr.effect,
            "decision": tr.decision.value,
            "veritas": tr.ruling.verdict.value,
            "motif": tr.motif,
            "gate": tr.reason,
            "action": action,
            "target": target,
        }

    def handle(msg: dict[str, Any]) -> dict[str, Any] | None:
        mid = msg.get("id")
        method = msg.get("method") or ""
        params = msg.get("params") or {}
        if method == "initialize":
            return {
                "jsonrpc": "2.0",
                "id": mid,
                "result": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {"tools": {}},
                    "serverInfo": {"name": "aion-gate", "version": "0.2.0"},
                    "instructions": "Utilise aion_propose. N'appelle jamais un outil d'effet réel.",
                },
            }
        if method.startswith("notifications/"):
            return None
        if method == "ping":
            return {"jsonrpc": "2.0", "id": mid, "result": {}}
        if method == "tools/list":
            return {"jsonrpc": "2.0", "id": mid, "result": {"tools": tools}}
        if method == "tools/call":
            name = params.get("name")
            args = params.get("arguments") or {}
            if name == "aion_get_cadre":
                return {"jsonrpc": "2.0", "id": mid, "result": tool_text(cadre)}
            if name == "aion_journal":
                j = [
                    {"decision": t.decision.value, "effect": t.effect, "motif": t.motif}
                    for t in rt.traces[-20:]
                ]
                return {"jsonrpc": "2.0", "id": mid, "result": tool_text({"journal": j})}
            if name == "aion_propose":
                out = propose(args)
                return {"jsonrpc": "2.0", "id": mid, "result": tool_text(out, out["effect"] == 0)}
            return {
                "jsonrpc": "2.0",
                "id": mid,
                "error": {"code": -32601, "message": f"outil inconnu: {name}"},
            }
        return {
            "jsonrpc": "2.0",
            "id": mid,
            "error": {"code": -32601, "message": f"méthode inconnue: {method}"},
        }

    while True:
        msg = read_msg()
        if msg is None:
            return 0
        resp = handle(msg)
        if resp is not None:
            write_msg(resp)


def demo_transfer_10000() -> dict[str, Any]:
    """Scénario vitrine : virement 10k€ — preuve conflictuelle → 0 effet."""
    world: list[str] = []
    enf = Enforcer(b"aion-runtime-demo", world=lambda t: world.append(t.canonical()))
    rt = AionRuntime(enf)

    tau = Transition("agent", "transfer", "iban-BENEF", {"amount_eur": 10000})
    prop = Proposal(
        claim="Le beneficiaire IBAN est conforme au contrat",
        tau=tau,
        evidences=[
            Evidence("bank", True, age_days=0, trusted=True),
            Evidence("compliance", False, age_days=0, trusted=True),
        ],
        stake=Stake(reversible=False, cout=10000.0, seuil_humain=50.0),
    )
    tr = rt.submit(prop)
    # agent tries to force
    bypass = rt.bypass_attempt(tau, None)
    return {
        "scenario": "transfer_10000_conflict",
        "veritas": tr.ruling.verdict.value,
        "arbitre": tr.decision.value,
        "motif": tr.motif,
        "effect_via_runtime": tr.effect,
        "effect_bypass": bypass.effect,
        "world_mutations": len(world),
        "pass": tr.effect == 0 and bypass.effect == 0 and len(world) == 0,
    }
