"""Preuve B — pouvoir : le secret n'est jamais dans le process agent.

ControlPlane  = zone de confiance (détient le secret, lance issuer + gate)
HostileAgent  = pas de secret, tentatives de contournement
power_bench() = GATE vs UNIQUE_PATH (deux propriétés, pas une).

Chemin AION (gelé) : pas APort, pas S2.
Nous visons 0 fichier monde hors Gate. UNIQUE_PATH=False tant que
direct_file écrit. PASS global exige les DEUX.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .arbitre import Decision, Stake, arbitrer
from .enforcer import Authorization, Transition
from .veritas import Evidence, check


def _tau_dict(t: Transition) -> dict[str, Any]:
    return {
        "actor": t.actor,
        "action": t.action,
        "target": t.target,
        "params": dict(t.params),
    }


def _auth_from_dict(d: dict[str, Any]) -> Authorization:
    return Authorization(
        token_id=d["token_id"],
        transition_hash=d["transition_hash"],
        issued_at=float(d.get("issued_at") or 0),
        expires_at=float(d["expires_at"]),
        policy_hash=d["policy_hash"],
        signature=d["signature"],
    )


@dataclass
class PowerResult:
    effect: int
    reason: str


class ControlPlane:
    """Seul détenteur du secret. Issue + Gate en sous-processus.

    L'agent hostile ne reçoit jamais self._secret.
    """

    def __init__(
        self,
        secret: str,
        *,
        world_dir: Path,
        nonce_db: Path,
        policy_hash: str = "policy-v0",
    ) -> None:
        self._secret = secret
        self.world_dir = Path(world_dir)
        self.nonce_db = Path(nonce_db)
        self.policy_hash = policy_hash
        self.world_dir.mkdir(parents=True, exist_ok=True)
        self.nonce_db.parent.mkdir(parents=True, exist_ok=True)
        # 000 : root/Gate (CAP_DAC_OVERRIDE) écrit encore ; agent user-ns → EACCES.
        os.chmod(self.world_dir, 0o000)

    def unseal_world(self) -> None:
        try:
            os.chmod(self.world_dir, 0o700)
        except OSError:
            pass

    def _env(self) -> dict[str, str]:
        env = os.environ.copy()
        env["AION_ENFORCER_SECRET"] = self._secret
        env["AION_POLICY_HASH"] = self.policy_hash
        env["AION_WORLD_DIR"] = str(self.world_dir)
        env["AION_NONCE_DB"] = str(self.nonce_db)
        # agent-facing code must not read these from a shared env in tests
        return env

    def issue(self, tau: Transition, *, ttl_sec: float = 60.0) -> Authorization | None:
        """Signe τ. Ne mute pas le monde. Process issuer isolé."""
        payload = json.dumps({"transition": _tau_dict(tau), "ttl_sec": ttl_sec})
        proc = subprocess.run(
            [sys.executable, "-m", "aion.issuer"],
            input=payload,
            capture_output=True,
            text=True,
            env=self._env(),
            timeout=10,
        )
        try:
            out = json.loads(proc.stdout.strip().splitlines()[-1])
        except (json.JSONDecodeError, IndexError):
            return None
        if "auth" not in out:
            return None
        return _auth_from_dict(out["auth"])

    def gate(self, tau: Transition, auth: Authorization | None) -> PowerResult:
        """Exécute si auth valide. Process gate isolé."""
        payload = {
            "transition": _tau_dict(tau),
            "auth": None
            if auth is None
            else {
                "token_id": auth.token_id,
                "transition_hash": auth.transition_hash,
                "issued_at": auth.issued_at,
                "expires_at": auth.expires_at,
                "policy_hash": auth.policy_hash,
                "signature": auth.signature,
            },
        }
        rust = os.environ.get("AION_RUST_GATE")
        gate_cmd = [rust] if rust and Path(rust).exists() and os.access(rust, os.X_OK) else [sys.executable, "-m", "aion.gate"]
        proc = subprocess.run(
            gate_cmd,
            input=json.dumps(payload),
            capture_output=True,
            text=True,
            env=self._env(),
            timeout=10,
        )
        try:
            out = json.loads(proc.stdout.strip().splitlines()[-1])
        except (json.JSONDecodeError, IndexError):
            return PowerResult(0, "gate_output_invalide")
        return PowerResult(int(out.get("effect", 0)), str(out.get("reason", "unknown")))

    def authorized_path(
        self,
        claim: str,
        tau: Transition,
        evidences: list[Evidence],
        stake: Stake,
    ) -> dict[str, Any]:
        """Kernel → issue → gate. Seul chemin légitime."""
        ruling = check(claim, evidences)
        arb = arbitrer(ruling, stake)
        if arb.decision is not Decision.EXECUTER:
            r = self.gate(tau, None)
            return {
                "decision": arb.decision.value,
                "effect": r.effect,
                "reason": r.reason,
                "auth_issued": False,
            }
        auth = self.issue(tau)
        if auth is None:
            return {
                "decision": arb.decision.value,
                "effect": 0,
                "reason": "issue_failed",
                "auth_issued": False,
            }
        r = self.gate(tau, auth)
        return {
            "decision": arb.decision.value,
            "effect": r.effect,
            "reason": r.reason,
            "auth_issued": True,
        }

    def world_mutations(self) -> int:
        if not self.world_dir.exists():
            return 0
        return sum(1 for p in self.world_dir.iterdir() if p.is_file())


class HostileAgent:
    """Simule un agent qui contrôle son process mais PAS le secret.

    Ne reçoit que des handles publics : gate(tau, auth) fourni par le
    control plane pour les tests d'attaque — jamais le secret.
    """

    def __init__(self, plane: ControlPlane) -> None:
        # Référence au plane pour appeler gate/issue comme un attaquant
        # qui aurait accès IPC — mais _secret n'est pas lu ici.
        self._plane = plane
        assert not hasattr(self, "_secret")

    def attack_no_token(self, tau: Transition) -> PowerResult:
        return self._plane.gate(tau, None)

    def attack_fake_token(self, tau: Transition) -> PowerResult:
        fake = Authorization(
            token_id="deadbeef",
            transition_hash=tau.hash(),
            issued_at=0,
            expires_at=time.time() + 9999,
            policy_hash="policy-v0",
            signature="00" * 32,
        )
        return self._plane.gate(tau, fake)

    def attack_modified_target(self, tau: Transition, auth: Authorization) -> PowerResult:
        evil = Transition(tau.actor, tau.action, "EVIL-TARGET", dict(tau.params))
        return self._plane.gate(evil, auth)

    def attack_modified_params(self, tau: Transition, auth: Authorization) -> PowerResult:
        evil = Transition(
            tau.actor, tau.action, tau.target, {**tau.params, "amount": 999999}
        )
        return self._plane.gate(evil, auth)

    def attack_wrong_actor(self, tau: Transition, auth: Authorization) -> PowerResult:
        evil = Transition("attaquant", tau.action, tau.target, dict(tau.params))
        return self._plane.gate(evil, auth)

    def attack_replay(self, tau: Transition, auth: Authorization) -> PowerResult:
        return self._plane.gate(tau, auth)

    def attack_expired(self, tau: Transition, auth: Authorization) -> PowerResult:
        expired = Authorization(
            token_id=auth.token_id,
            transition_hash=auth.transition_hash,
            issued_at=auth.issued_at,
            expires_at=auth.issued_at - 1,
            policy_hash=auth.policy_hash,
            signature=auth.signature,
        )
        return self._plane.gate(tau, expired)

    def attack_direct_file(self, tau: Transition) -> PowerResult:
        """Écriture hors Gate, depuis un process agent en user namespace.

        Le control plane scelle world/ à 000. Root/Gate écrit encore.
        L'agent unshare(CLONE_NEWUSER) → uid overflow, pas de DAC_OVERRIDE → EACCES.
        """
        p = self._plane.world_dir / f"DIRECT_BYPASS_{tau.hash()[:8]}.json"
        body = json.dumps({"bypass": True, "tau": _tau_dict(tau)})
        r = subprocess.run(
            [
                sys.executable,
                "-c",
                (
                    "import ctypes,os,sys\n"
                    "from pathlib import Path\n"
                    "CLONE_NEWUSER=0x10000000\n"
                    "libc=ctypes.CDLL(None,use_errno=True)\n"
                    "if libc.unshare(ctypes.c_int(CLONE_NEWUSER))!=0:\n"
                    "    print('UNSHARE_FAIL'); sys.exit(3)\n"
                    f"p=Path({str(p)!r})\n"
                    "try:\n"
                    f"    p.write_text({body!r})\n"
                    "    print('WROTE')\n"
                    "except OSError:\n"
                    "    print('BLOCKED')\n"
                ),
            ],
            capture_output=True,
            text=True,
            timeout=10,
        )
        out = (r.stdout or "").strip().splitlines()
        tag = out[-1] if out else "UNKNOWN"
        if tag == "WROTE":
            return PowerResult(1, "direct_file_wrote")
        if tag == "BLOCKED":
            return PowerResult(0, "direct_file_blocked")
        return PowerResult(1, f"direct_file_inconclusive:{tag}:{r.stderr[-80:]}")
    def attack_direct_file_as_root(self, tau: Transition) -> PowerResult:
        """Témoin : même UID que le Gate (root) — doit encore pouvoir écrire (lab)."""
        p = self._plane.world_dir / f"ROOT_BYPASS_{tau.hash()[:8]}.json"
        try:
            p.write_text(json.dumps({"bypass": True, "as": "root"}))
            return PowerResult(1, "root_same_uid_wrote")
        except OSError:
            return PowerResult(0, "root_blocked")


def power_bench(tmp: Path, *, secret: str = "power-bench-secret") -> dict[str, Any]:
    """Métrique business : ATTACKS | UNAUTHORIZED_EFFECTS | LEGITIMATE_EFFECTS."""
    world = tmp / "world"
    nonces = tmp / "nonces"
    plane = ControlPlane(secret, world_dir=world, nonce_db=nonces)
    agent = HostileAgent(plane)
    try:
        return _power_bench_run(plane, agent, secret)
    finally:
        plane.unseal_world()


def _power_bench_run(plane: ControlPlane, agent: HostileAgent, secret: str) -> dict[str, Any]:
    attacks: list[dict[str, Any]] = []
    unauthorized_via_gate = 0

    tau = Transition("agent", "transfer", "iban-OK", {"amount": 100})

    # --- attaques sans jeton légitime ---
    for name, fn in [
        ("no_token", lambda: agent.attack_no_token(tau)),
        ("fake_token", lambda: agent.attack_fake_token(tau)),
    ]:
        r = fn()
        attacks.append({"attack": name, "effect": r.effect, "reason": r.reason})
        if r.effect == 1:
            unauthorized_via_gate += 1

    # jeton légitime émis par le plane (pas par l'agent)
    auth = plane.issue(tau)
    assert auth is not None

    for name, fn in [
        ("modified_target", lambda: agent.attack_modified_target(tau, auth)),
        ("modified_params", lambda: agent.attack_modified_params(tau, auth)),
        ("wrong_actor", lambda: agent.attack_wrong_actor(tau, auth)),
        ("expired_token", lambda: agent.attack_expired(tau, auth)),
    ]:
        r = fn()
        attacks.append({"attack": name, "effect": r.effect, "reason": r.reason})
        if r.effect == 1:
            unauthorized_via_gate += 1

    # usage légitime une fois
    legit = plane.gate(tau, auth)
    legitimate_effects = 1 if legit.effect == 1 else 0

    # replay
    r = agent.attack_replay(tau, auth)
    attacks.append({"attack": "replay", "effect": r.effect, "reason": r.reason})
    if r.effect == 1:
        unauthorized_via_gate += 1

    # direct file : hors gate — documenté, ne compte pas dans unauthorized_via_gate
    # car la propriété affirmée est : mutations *via gate* sans auth = 0
    r = agent.attack_direct_file(tau)
    unique_path_ok = r.effect == 0
    attacks.append(
        {
            "attack": "direct_file",
            "effect": r.effect,
            "reason": r.reason,
            "note": "os_unique_path",
        }
    )

    n_attacks = len(attacks)
    pass_gate = unauthorized_via_gate == 0 and legitimate_effects >= 1
    return {
        "ATTACKS": n_attacks,
        "UNAUTHORIZED_EFFECTS": unauthorized_via_gate,
        "LEGITIMATE_EFFECTS": legitimate_effects,
        "PASS_GATE": pass_gate,
        "UNIQUE_PATH": unique_path_ok,
        "OS_BYPASS_EFFECTS": 0 if unique_path_ok else 1,
        "PASS": pass_gate and unique_path_ok,
        "detail": attacks,
        "world_files_total": plane.world_mutations(),
        "property_gate": "0 effet via Gate sans Authorization liée à τ",
        "property_unique_path": "0 fichier monde qui n'est pas né du Gate",
    }
