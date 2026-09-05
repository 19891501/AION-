"""Pont Runtime → process gate isolé."""
from __future__ import annotations
import json, os, subprocess, sys
from pathlib import Path
from typing import Any
from .enforcer import Authorization, EffectResult, Transition

def _auth_dict(a: Authorization) -> dict[str, Any]:
    return {"token_id": a.token_id, "transition_hash": a.transition_hash, "expires_at": a.expires_at, "policy_hash": a.policy_hash, "signature": a.signature}

def _tau_dict(t: Transition) -> dict[str, Any]:
    return {"actor": t.actor, "action": t.action, "target": t.target, "params": dict(t.params)}

def invoke_gate(tau: Transition, auth: Authorization | None, *, secret: str = "dev-secret", world_dir: str | Path = "/tmp/aion_world", nonce_db: str | Path = "/tmp/aion_nonces", rust_bin: str | Path | None = None) -> EffectResult:
    payload = {"transition": _tau_dict(tau), "auth": _auth_dict(auth) if auth else None}
    env = os.environ.copy()
    env["AION_ENFORCER_SECRET"] = secret
    env["AION_WORLD_DIR"] = str(world_dir)
    env["AION_NONCE_DB"] = str(nonce_db)
    env["AION_POLICY_HASH"] = "policy-v0"
    cmd = [str(rust_bin)] if rust_bin and Path(rust_bin).exists() else [sys.executable, "-m", "aion.gate"]
    proc = subprocess.run(cmd, input=json.dumps(payload, ensure_ascii=False), capture_output=True, text=True, env=env, timeout=10)
    try:
        out = json.loads(proc.stdout.strip().splitlines()[-1] if proc.stdout.strip() else "{}")
    except json.JSONDecodeError:
        return EffectResult(False, 0, "gate_output_invalide")
    effect = int(out.get("effect", 0))
    return EffectResult(effect == 1, effect, str(out.get("reason", "unknown")))
