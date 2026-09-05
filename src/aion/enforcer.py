"""Enforcer logiciel minimal — 0 EUR, deterministe."""
from __future__ import annotations

import hashlib
import hmac
import json
import secrets
import time
from dataclasses import dataclass, field
from typing import Any, Callable


@dataclass(frozen=True)
class Transition:
    actor: str
    action: str
    target: str
    params: dict[str, Any] = field(default_factory=dict)

    def canonical(self) -> str:
        payload = {
            "actor": self.actor,
            "action": self.action,
            "target": self.target,
            "params": self.params,
        }
        return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False)

    def hash(self) -> str:
        return hashlib.sha256(self.canonical().encode()).hexdigest()


@dataclass
class Authorization:
    token_id: str
    transition_hash: str
    issued_at: float
    expires_at: float
    policy_hash: str
    signature: str
    used: bool = False


@dataclass
class EffectResult:
    allowed: bool
    effect: int
    reason: str


class Enforcer:
    def __init__(
        self,
        secret: bytes,
        *,
        ttl_sec: float = 60.0,
        policy_hash: str = "policy-v0",
        world: Callable[[Transition], Any] | None = None,
    ) -> None:
        self._secret = secret
        self.ttl_sec = ttl_sec
        self.policy_hash = policy_hash
        self._world = world
        self._tokens: dict[str, Authorization] = {}
        self.attempts = 0
        self.blocked = 0
        self.executed = 0

    def _sign(self, msg: str) -> str:
        return hmac.new(self._secret, msg.encode(), hashlib.sha256).hexdigest()

    def issue(self, tau: Transition, *, now: float | None = None) -> Authorization:
        now = time.time() if now is None else now
        tid = secrets.token_hex(16)
        th = tau.hash()
        exp = now + self.ttl_sec
        msg = f"{tid}|{th}|{exp}|{self.policy_hash}"
        auth = Authorization(
            token_id=tid,
            transition_hash=th,
            issued_at=now,
            expires_at=exp,
            policy_hash=self.policy_hash,
            signature=self._sign(msg),
        )
        self._tokens[tid] = auth
        return auth

    def execute(
        self,
        tau: Transition,
        auth: Authorization | None,
        *,
        now: float | None = None,
    ) -> EffectResult:
        self.attempts += 1
        now = time.time() if now is None else now
        if auth is None:
            self.blocked += 1
            return EffectResult(False, 0, "authorization_absente")
        stored = self._tokens.get(auth.token_id)
        if stored is None:
            self.blocked += 1
            return EffectResult(False, 0, "token_inconnu")
        msg = f"{auth.token_id}|{auth.transition_hash}|{auth.expires_at}|{auth.policy_hash}"
        if not hmac.compare_digest(auth.signature, self._sign(msg)):
            self.blocked += 1
            return EffectResult(False, 0, "signature_invalide")
        if auth.policy_hash != self.policy_hash:
            self.blocked += 1
            return EffectResult(False, 0, "policy_hash_modifie")
        if now > auth.expires_at:
            self.blocked += 1
            return EffectResult(False, 0, "authorization_expiree")
        if stored.used:
            self.blocked += 1
            return EffectResult(False, 0, "nonce_reutilise")
        if auth.transition_hash != tau.hash():
            self.blocked += 1
            return EffectResult(False, 0, "transition_modifiee")
        stored.used = True
        if self._world is not None:
            self._world(tau)
        self.executed += 1
        return EffectResult(True, 1, "execute")


def attack_bench(enforcer: Enforcer, tau: Transition, valid: Authorization) -> dict:
    results = []

    def try_attack(name: str, t: Transition, a: Authorization | None) -> None:
        r = enforcer.execute(t, a)
        results.append(
            {"attack": name, "allowed": r.allowed, "effect": r.effect, "reason": r.reason}
        )

    try_attack("sans_auth", tau, None)
    try_attack(
        "token_inconnu",
        tau,
        Authorization("dead", tau.hash(), 0, 1e12, enforcer.policy_hash, "00"),
    )
    try_attack(
        "signature_invalide",
        tau,
        Authorization(
            valid.token_id,
            valid.transition_hash,
            valid.issued_at,
            valid.expires_at,
            valid.policy_hash,
            "ff" * 32,
        ),
    )
    try_attack(
        "policy_hash_modifie",
        tau,
        Authorization(
            valid.token_id,
            valid.transition_hash,
            valid.issued_at,
            valid.expires_at,
            "policy-HACKED",
            valid.signature,
        ),
    )
    try_attack(
        "transition_modifiee_cible",
        Transition(tau.actor, tau.action, "autre-cible", dict(tau.params)),
        valid,
    )
    try_attack(
        "transition_modifiee_params",
        Transition(tau.actor, tau.action, tau.target, {**tau.params, "amount": 999999}),
        valid,
    )
    try_attack(
        "actor_modifie",
        Transition("attaquant", tau.action, tau.target, dict(tau.params)),
        valid,
    )
    try_attack("usage_legitime", tau, valid)
    try_attack("nonce_reutilise", tau, valid)

    pure = [x for x in results if x["attack"] not in ("usage_legitime",)]
    unauthorized = sum(x["effect"] for x in pure)
    return {
        "n_attacks": len(pure),
        "unauthorized_effects": unauthorized,
        "detail": results,
        "pass": unauthorized == 0,
    }
