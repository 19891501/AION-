"""Gate process isolé — seul process autorisé à muter le monde lab."""
from __future__ import annotations
import hashlib, hmac, json, os, sys, time
from pathlib import Path

def _canonical(t: dict) -> str:
    return json.dumps({"actor": t["actor"], "action": t["action"], "target": t["target"], "params": t.get("params") or {}}, sort_keys=True, separators=(",", ":"), ensure_ascii=False)

def _th(t: dict) -> str:
    return hashlib.sha256(_canonical(t).encode()).hexdigest()

def _sign(secret: bytes, msg: str) -> str:
    return hmac.new(secret, msg.encode(), hashlib.sha256).hexdigest()

def main(argv=None) -> int:
    secret = os.environ.get("AION_ENFORCER_SECRET", "dev-secret").encode()
    policy = os.environ.get("AION_POLICY_HASH", "policy-v0")
    nonce_db = Path(os.environ.get("AION_NONCE_DB", "/tmp/aion_nonces"))
    world = Path(os.environ.get("AION_WORLD_DIR", "/tmp/aion_world"))
    raw = sys.stdin.read() if not (argv and len(argv) > 1) else argv[1]
    try:
        req = json.loads(raw)
    except json.JSONDecodeError:
        print(json.dumps({"effect": 0, "reason": "json_invalide"}))
        return 1
    tau = req.get("transition") or {}
    auth = req.get("auth")
    th = _th(tau)
    def deny(reason: str) -> int:
        print(json.dumps({"effect": 0, "reason": reason, "transition_hash": th}))
        return 1
    if not auth:
        return deny("authorization_absente")
    msg = f"{auth['token_id']}|{auth['transition_hash']}|{auth['expires_at']}|{auth['policy_hash']}"
    if not hmac.compare_digest(auth.get("signature", ""), _sign(secret, msg)):
        return deny("signature_invalide")
    if auth.get("policy_hash") != policy:
        return deny("policy_hash_modifie")
    if time.time() > float(auth["expires_at"]):
        return deny("authorization_expiree")
    if auth.get("transition_hash") != th:
        return deny("transition_modifiee")
    nonce_db.parent.mkdir(parents=True, exist_ok=True)
    seen = set()
    if nonce_db.exists():
        seen = {ln.strip() for ln in nonce_db.read_text().splitlines() if ln.strip()}
    if auth["token_id"] in seen:
        return deny("nonce_reutilise")
    with nonce_db.open("a") as f:
        f.write(auth["token_id"] + "\n")
    world.mkdir(parents=True, exist_ok=True)
    (world / f"{th[:16]}.json").write_text(json.dumps({"actor": tau.get("actor"), "action": tau.get("action"), "target": tau.get("target"), "params": tau.get("params") or {}, "hash": th}, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"effect": 1, "reason": "execute", "transition_hash": th}))
    return 0

if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
