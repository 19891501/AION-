"""Gate process isolé — seul binaire/process autorisé à muter le monde lab.

Usage:
  AION_ENFORCER_SECRET=... python -m aion.gate <<'JSON'
  {"transition":{...},"auth":{...}|null}
  JSON

Même contrat que enforcer_rs (quand crates.io est dispo).
Exit 0 + effect=1 si OK ; exit 1 + effect=0 sinon.
"""
from __future__ import annotations

import hashlib
import hmac
import json
import os
import sys
from pathlib import Path


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


def _sign(secret: bytes, msg: str) -> str:
    return hmac.new(secret, msg.encode(), hashlib.sha256).hexdigest()


def _dirfd_nofollow(path: Path) -> int:
    """Ouvre un répertoire sans suivre de symlink (O_NOFOLLOW | O_DIRECTORY)."""
    path.mkdir(parents=True, exist_ok=True)
    flags = os.O_RDONLY | getattr(os, "O_DIRECTORY", 0) | os.O_NOFOLLOW
    return os.open(path, flags)


def _write_excl_in_dir(dirfd: int, name: str, data: bytes) -> None:
    if "/" in name or name in (".", "..") or "\\" in name:
        raise OSError("nom_interdit")
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW
    fd = os.open(name, flags, 0o644, dir_fd=dirfd)
    try:
        os.write(fd, data)
    finally:
        os.close(fd)


def _nonce_append_nofollow(path: Path, token: str) -> bool:
    """True si le nonce vient d'être enregistré ; False si déjà vu. OSError si symlink."""
    path.parent.mkdir(parents=True, exist_ok=True)
    flags = os.O_RDWR | os.O_CREAT | os.O_APPEND | os.O_NOFOLLOW
    fd = os.open(path, flags, 0o644)
    try:
        os.lseek(fd, 0, os.SEEK_SET)
        raw = b""
        while True:
            chunk = os.read(fd, 65536)
            if not chunk:
                break
            raw += chunk
        seen = {ln.strip() for ln in raw.decode().splitlines() if ln.strip()}
        if token in seen:
            return False
        os.write(fd, (token + "\n").encode())
        return True
    finally:
        os.close(fd)


def main(argv: list[str] | None = None) -> int:
    secret = os.environ.get("AION_ENFORCER_SECRET", "").encode()
    if not secret:
        print(json.dumps({"effect": 0, "reason": "secret_absent"}))
        return 1
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
    import time

    if time.time() > float(auth["expires_at"]):
        return deny("authorization_expiree")
    if auth.get("transition_hash") != th:
        return deny("transition_modifiee")

    try:
        added = _nonce_append_nofollow(nonce_db, auth["token_id"])
    except OSError:
        return deny("nonce_symlink")
    if not added:
        return deny("nonce_reutilise")

    body = json.dumps(
        {
            "actor": tau.get("actor"),
            "action": tau.get("action"),
            "target": tau.get("target"),
            "params": tau.get("params") or {},
            "hash": th,
        },
        ensure_ascii=False,
        indent=2,
    ).encode()
    dirfd = -1
    try:
        dirfd = _dirfd_nofollow(world)
        _write_excl_in_dir(dirfd, f"{th[:16]}.json", body)
    except OSError:
        return deny("world_symlink")
    finally:
        if dirfd >= 0:
            os.close(dirfd)

    print(json.dumps({"effect": 1, "reason": "execute", "transition_hash": th}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
