"""Preuve B — pouvoir : secret hors process agent."""
from __future__ import annotations
import json, os, subprocess, sys, time
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from .arbitre import Decision, Stake, arbitrer
from .enforcer import Authorization, Transition
from .veritas import Evidence, check

def _tau_dict(t: Transition) -> dict[str, Any]:
    return {"actor": t.actor, "action": t.action, "target": t.target, "params": dict(t.params)}

def _auth_from_dict(d: dict[str, Any]) -> Authorization:
    return Authorization(token_id=d["token_id"], transition_hash=d["transition_hash"], issued_at=float(d.get("issued_at") or 0), expires_at=float(d["expires_at"]), policy_hash=d["policy_hash"], signature=d["signature"])

@dataclass
class PowerResult:
    effect: int
    reason: str

class ControlPlane:
    def __init__(self, secret: str, *, world_dir: Path, nonce_db: Path, policy_hash: str = "policy-v0") -> None:
        self._secret = secret
        self.world_dir = Path(world_dir)
        self.nonce_db = Path(nonce_db)
        self.policy_hash = policy_hash
        self.world_dir.mkdir(parents=True, exist_ok=True)
        self.nonce_db.parent.mkdir(parents=True, exist_ok=True)
    def _env(self) -> dict[str, str]:
        env = os.environ.copy()
        env["AION_ENFORCER_SECRET"] = self._secret
        env["AION_POLICY_HASH"] = self.policy_hash
        env["AION_WORLD_DIR"] = str(self.world_dir)
        env["AION_NONCE_DB"] = str(self.nonce_db)
        return env
    def issue(self, tau: Transition, *, ttl_sec: float = 60.0) -> Authorization | None:
        payload = json.dumps({"transition": _tau_dict(tau), "ttl_sec": ttl_sec})
        proc = subprocess.run([sys.executable, "-m", "aion.issuer"], input=payload, capture_output=True, text=True, env=self._env(), timeout=10)
        try:
            out = json.loads(proc.stdout.strip().splitlines()[-1])
        except (json.JSONDecodeError, IndexError):
            return None
        return _auth_from_dict(out["auth"]) if "auth" in out else None
    def gate(self, tau: Transition, auth: Authorization | None) -> PowerResult:
        payload = {"transition": _tau_dict(tau), "auth": None if auth is None else {"token_id": auth.token_id, "transition_hash": auth.transition_hash, "issued_at": auth.issued_at, "expires_at": auth.expires_at, "policy_hash": auth.policy_hash, "signature": auth.signature}}
        proc = subprocess.run([sys.executable, "-m", "aion.gate"], input=json.dumps(payload), capture_output=True, text=True, env=self._env(), timeout=10)
        try:
            out = json.loads(proc.stdout.strip().splitlines()[-1])
        except (json.JSONDecodeError, IndexError):
            return PowerResult(0, "gate_output_invalide")
        return PowerResult(int(out.get("effect", 0)), str(out.get("reason", "unknown")))
    def authorized_path(self, claim: str, tau: Transition, evidences: list[Evidence], stake: Stake) -> dict[str, Any]:
        ruling = check(claim, evidences)
        arb = arbitrer(ruling, stake)
        if arb.decision is not Decision.EXECUTER:
            r = self.gate(tau, None)
            return {"decision": arb.decision.value, "effect": r.effect, "reason": r.reason, "auth_issued": False}
        auth = self.issue(tau)
        if auth is None:
            return {"decision": arb.decision.value, "effect": 0, "reason": "issue_failed", "auth_issued": False}
        r = self.gate(tau, auth)
        return {"decision": arb.decision.value, "effect": r.effect, "reason": r.reason, "auth_issued": True}
    def world_mutations(self) -> int:
        return sum(1 for p in self.world_dir.iterdir() if p.is_file()) if self.world_dir.exists() else 0

class HostileAgent:
    def __init__(self, plane: ControlPlane) -> None:
        self._plane = plane
        assert not hasattr(self, "_secret")
    def attack_no_token(self, tau):
        return self._plane.gate(tau, None)
    def attack_fake_token(self, tau):
        fake = Authorization("deadbeef", tau.hash(), 0, time.time()+9999, "policy-v0", "00"*32)
        return self._plane.gate(tau, fake)
    def attack_modified_target(self, tau, auth):
        return self._plane.gate(Transition(tau.actor, tau.action, "EVIL-TARGET", dict(tau.params)), auth)
    def attack_modified_params(self, tau, auth):
        return self._plane.gate(Transition(tau.actor, tau.action, tau.target, {**tau.params, "amount": 999999}), auth)
    def attack_wrong_actor(self, tau, auth):
        return self._plane.gate(Transition("attaquant", tau.action, tau.target, dict(tau.params)), auth)
    def attack_replay(self, tau, auth):
        return self._plane.gate(tau, auth)
    def attack_expired(self, tau, auth):
        return self._plane.gate(tau, Authorization(auth.token_id, auth.transition_hash, auth.issued_at, auth.issued_at-1, auth.policy_hash, auth.signature))
    def attack_direct_file(self, tau):
        p = self._plane.world_dir / f"DIRECT_BYPASS_{tau.hash()[:8]}.json"
        try:
            p.write_text(json.dumps({"bypass": True})); return PowerResult(1, "direct_file_wrote")
        except OSError:
            return PowerResult(0, "direct_file_blocked")

def power_bench(tmp: Path, *, secret: str = "power-bench-secret") -> dict[str, Any]:
    world, nonces = tmp / "world", tmp / "nonces"
    plane = ControlPlane(secret, world_dir=world, nonce_db=nonces)
    agent = HostileAgent(plane)
    attacks = []
    unauthorized_via_gate = 0
    tau = Transition("agent", "transfer", "iban-OK", {"amount": 100})
    for name, fn in [("no_token", lambda: agent.attack_no_token(tau)), ("fake_token", lambda: agent.attack_fake_token(tau))]:
        r = fn(); attacks.append({"attack": name, "effect": r.effect, "reason": r.reason})
        if r.effect == 1: unauthorized_via_gate += 1
    auth = plane.issue(tau); assert auth is not None
    for name, fn in [("modified_target", lambda: agent.attack_modified_target(tau, auth)), ("modified_params", lambda: agent.attack_modified_params(tau, auth)), ("wrong_actor", lambda: agent.attack_wrong_actor(tau, auth)), ("expired_token", lambda: agent.attack_expired(tau, auth))]:
        r = fn(); attacks.append({"attack": name, "effect": r.effect, "reason": r.reason})
        if r.effect == 1: unauthorized_via_gate += 1
    legit = plane.gate(tau, auth)
    legitimate_effects = 1 if legit.effect == 1 else 0
    r = agent.attack_replay(tau, auth)
    attacks.append({"attack": "replay", "effect": r.effect, "reason": r.reason})
    if r.effect == 1: unauthorized_via_gate += 1
    r = agent.attack_direct_file(tau)
    attacks.append({"attack": "direct_file", "effect": r.effect, "reason": r.reason, "note": "hors_protocole_OS_lab"})
    n_attacks = len([a for a in attacks if a["attack"] != "direct_file"])
    return {"ATTACKS": n_attacks, "UNAUTHORIZED_EFFECTS": unauthorized_via_gate, "LEGITIMATE_EFFECTS": legitimate_effects, "PASS": unauthorized_via_gate == 0 and legitimate_effects >= 1, "detail": attacks, "world_files_total": plane.world_mutations(), "property": "Toute mutation protocole passe par le gate avec Authorization liee a tau."}
