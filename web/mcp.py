"""POST /mcp — JSON-RPC. L'agent propose, AION autorise."""
from __future__ import annotations
import json, os
from typing import Any
from fastapi import APIRouter
from aion.arbitre import Stake
from aion.enforcer import Enforcer, Transition
from aion.runtime import AionRuntime, Proposal

router = APIRouter()
_rt = AionRuntime(Enforcer(os.environ.get("AION_ENFORCER_SECRET", "render-dev").encode(), world=lambda t: None))
HUM = ("transfer", "virement", "delete")
BAN = ("pirater", "exfiltrer", "drop_database")
TOOLS = [
    {"name": "aion_get_cadre", "description": "Contrat d'autonomie", "inputSchema": {"type": "object", "properties": {}}},
    {"name": "aion_propose", "description": "Propose tau", "inputSchema": {"type": "object", "required": ["intent", "action", "target"], "properties": {"intent": {"type": "string"}, "action": {"type": "string"}, "target": {"type": "string"}, "amount": {"type": "number"}}}},
    {"name": "aion_journal", "description": "Journal", "inputSchema": {"type": "object", "properties": {}}},
]

def _ok(mid, obj, err=False):
    return {"jsonrpc": "2.0", "id": mid, "result": {"content": [{"type": "text", "text": json.dumps(obj, ensure_ascii=False)}], "isError": err}}

def handle(msg: dict[str, Any]) -> dict[str, Any]:
    mid, method, params = msg.get("id"), msg.get("method") or "", msg.get("params") or {}
    if method == "initialize":
        return {"jsonrpc": "2.0", "id": mid, "result": {"protocolVersion": "2024-11-05", "capabilities": {"tools": {}}, "serverInfo": {"name": "aion-gate", "version": "0.2.0"}}}
    if method == "tools/list":
        return {"jsonrpc": "2.0", "id": mid, "result": {"tools": TOOLS}}
    if method != "tools/call":
        return {"jsonrpc": "2.0", "id": mid, "error": {"code": -32601, "message": method}}
    name, args = params.get("name"), params.get("arguments") or {}
    if name == "aion_get_cadre":
        return _ok(mid, {"principe": "Tout le reste est libre.", "humain": list(HUM)})
    if name == "aion_journal":
        return _ok(mid, {"journal": [{"d": t.decision.value, "e": t.effect} for t in _rt.traces[-20:]]})
    intent, action, target = str(args.get("intent", "")), str(args.get("action", "")), str(args.get("target", ""))
    amount = float(args.get("amount") or 0)
    hay = f"{intent} {action} {target}".lower()
    if any(x in hay for x in BAN):
        return _ok(mid, {"effect": 0, "decision": "NO_ACTION"}, True)
    if any(x in hay for x in HUM) or amount > 50:
        return _ok(mid, {"effect": 0, "decision": "DEMANDER_HUMAIN"}, True)
    tau = Transition("mcp-agent", action, target, {"amount": amount})
    tr = _rt.submit(Proposal(claim=intent or action, tau=tau, evidences=[], stake=Stake(cout=amount, seuil_humain=50)))
    return _ok(mid, {"effect": tr.effect, "decision": tr.decision.value, "veritas": tr.ruling.verdict.value, "gate": tr.reason}, tr.effect == 0)

@router.get("/mcp")
def mcp_get():
    return {"service": "aion-gate", "tools": [t["name"] for t in TOOLS], "endpoint": "POST /mcp"}

@router.post("/mcp")
def mcp_post(body: dict[str, Any]):
    return handle(body)
