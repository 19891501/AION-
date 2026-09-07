"""Issuer process — signe les Authorization. Ne mute JAMAIS le monde.

Séparé du gate : issue ≠ execute.

  AION_ENFORCER_SECRET=... python -m aion.issuer <<'JSON'
  {"transition": {...}, "ttl_sec": 60}
  JSON

Stdout: {"auth": {...}} ou {"error": "..."}.
"""
from __future__ import annotations

import hashlib
import hmac
import json
import os
import secrets
import sys
import time


def _canonical(t: dict) -> str:
    return json.dumps(
        {
            "actor": t["actor"],
            "action": t["action"],
            "target": t["target"],
            "params": t.get("params") or {},
        },
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    )


def _th(t: dict) -> str:
    return hashlib.sha256(_canonical(t).encode()).hexdigest()


def main(argv: list[str] | None = None) -> int:
    secret = os.environ.get("AION_ENFORCER_SECRET", "").encode()
    if not secret:
        print(json.dumps({"error": "secret_absent"}))
        return 1
    policy = os.environ.get("AION_POLICY_HASH", "policy-v0")
    raw = sys.stdin.read() if not (argv and len(argv) > 1) else argv[1]
    try:
        req = json.loads(raw)
    except json.JSONDecodeError:
        print(json.dumps({"error": "json_invalide"}))
        return 1
    tau = req.get("transition") or {}
    ttl = float(req.get("ttl_sec") or 60)
    th = _th(tau)
    tid = secrets.token_hex(16)
    now = time.time()
    exp = now + ttl
    msg = f"{tid}|{th}|{exp}|{policy}"
    sig = hmac.new(secret, msg.encode(), hashlib.sha256).hexdigest()
    auth = {
        "token_id": tid,
        "transition_hash": th,
        "issued_at": now,
        "expires_at": exp,
        "policy_hash": policy,
        "signature": sig,
    }
    print(json.dumps({"auth": auth}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
