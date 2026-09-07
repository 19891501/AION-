"""Serveur MCP stdio — l'agent n'a pas d'outil d'effet, seulement aion_propose.

Usage:
  PYTHONPATH=src python -m aion.mcp_stdio

Claude Desktop / Cursor :
  { "mcpServers": { "aion-gate": { "command": "python", "args": ["-m", "aion.mcp_stdio"] } } }
"""

from __future__ import annotations

import json
import sys
from typing import Any

from .arbitre import Decision, Stake, arbitrer
from .behavior import Situation, selectionner
from .veritas import Evidence, check

PROTOCOL = "2024-11-05"
TOOLS = [
    {
        "name": "aion_get_cadre",
        "description": "Lit le contrat d'autonomie. L'agent ne l'écrit pas.",
        "inputSchema": {"type": "object", "properties": {}},
    },
    {
        "name": "aion_propose",
        "description": "Propose une transition. Aucun effet sans autorisation AION.",
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
]

CADRE = {
    "objectif": "Agir dans le périmètre métier, sans toucher le réel hors cadre.",
    "interdit": ["pirater", "exfiltrer", "drop_database"],
    "validationHumaine": ["transfer", "virement", "delete"],
    "principe": "Tout le reste est libre.",
}


def _read_message() -> dict[str, Any] | None:
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
    body = sys.stdin.buffer.read(n)
    return json.loads(body.decode("utf-8"))


def _write(msg: dict[str, Any]) -> None:
    blob = json.dumps(msg, ensure_ascii=False).encode("utf-8")
    sys.stdout.buffer.write(f"Content-Length: {len(blob)}\r\n\r\n".encode("ascii"))
    sys.stdout.buffer.write(blob)
    sys.stdout.buffer.flush()


def _ok(mid: Any, result: Any) -> dict[str, Any]:
    return {"jsonrpc": "2.0", "id": mid, "result": result}


def _tool_text(obj: Any, is_error: bool = False) -> dict[str, Any]:
    return {
        "content": [{"type": "text", "text": json.dumps(obj, ensure_ascii=False, indent=2)}],
        "isError": is_error,
    }


def _propose(args: dict[str, Any]) -> dict[str, Any]:
    intent = str(args.get("intent", ""))
    action = str(args.get("action", "")).lower()
    target = str(args.get("target", ""))
    amount = float(args.get("amount") or 0)
    hay = f"{intent} {action} {target}".lower()
    if any(x in hay for x in CADRE["interdit"]):
        return {
            "effect": 0,
            "decision": "NO_ACTION",
            "motif": "Cadre · interdit",
        }
    if any(x in hay for x in CADRE["validationHumaine"]) or amount > 50:
        return {
            "effect": 0,
            "decision": "DEMANDER_HUMAIN",
            "motif": "Cadre · validation humaine ou plafond",
        }
    sit = Situation(
        question=intent,
        consequence_reelle=amount > 0 or action in {"transfer", "email", "delete"},
    )
    choix = selectionner(sit)
    ruling = check(intent, [Evidence(source="mcp", supports=True, trusted=True)])
    stake = Stake(reversible=bool(args.get("reversible", True)), cout=amount, seuil_humain=50)
    if choix.action.value == "REFUSE":
        decision = Decision.NO_ACTION
        motif = choix.motif
    else:
        arb = arbitrer(ruling, stake)
        decision, motif = arb.decision, arb.motif
    effect = 1 if decision == Decision.EXECUTER else 0
    return {
        "effect": effect,
        "decision": decision.value,
        "veritas": ruling.verdict.value,
        "behavior": choix.action.value,
        "motif": motif,
        "target": target,
        "action": action,
    }


def handle(msg: dict[str, Any]) -> dict[str, Any] | None:
    mid = msg.get("id")
    method = msg.get("method") or ""
    params = msg.get("params") or {}
    if method == "initialize":
        return _ok(
            mid,
            {
                "protocolVersion": PROTOCOL,
                "capabilities": {"tools": {}},
                "serverInfo": {"name": "aion-gate", "version": "0.2.0"},
                "instructions": "Utilise aion_propose. N'appelle jamais un outil d'effet réel.",
            },
        )
    if method.startswith("notifications/"):
        return None
    if method == "ping":
        return _ok(mid, {})
    if method == "tools/list":
        return _ok(mid, {"tools": TOOLS})
    if method == "tools/call":
        name = params.get("name")
        args = params.get("arguments") or {}
        if name == "aion_get_cadre":
            return _ok(mid, _tool_text(CADRE))
        if name == "aion_propose":
            out = _propose(args)
            return _ok(mid, _tool_text(out, is_error=out["effect"] == 0))
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


def main() -> int:
    while True:
        msg = _read_message()
        if msg is None:
            return 0
        resp = handle(msg)
        if resp is not None:
            _write(resp)


if __name__ == "__main__":
    raise SystemExit(main())
