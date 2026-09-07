"""Gate process isolé — 0 €."""
import os
from pathlib import Path

from aion.enforcer import Enforcer, Transition
from aion.gate_bridge import invoke_gate


def test_gate_process_blocks_and_allows(tmp_path):
    secret = "test-gate-secret"
    world = tmp_path / "world"
    nonces = tmp_path / "nonces"
    enf = Enforcer(secret.encode())
    tau = Transition("agent", "write", "x", {"n": 1})
    auth = enf.issue(tau)

    assert invoke_gate(tau, None, secret=secret, world_dir=world, nonce_db=nonces).effect == 0
    assert invoke_gate(tau, auth, secret=secret, world_dir=world, nonce_db=nonces).effect == 1
    assert invoke_gate(tau, auth, secret=secret, world_dir=world, nonce_db=nonces).effect == 0
    assert any(world.iterdir())


def test_gate_rejects_modified_transition(tmp_path):
    secret = "test-gate-secret"
    enf = Enforcer(secret.encode())
    tau = Transition("a", "pay", "good", {})
    auth = enf.issue(tau)
    bad = Transition("a", "pay", "evil", {})
    r = invoke_gate(
        bad, auth, secret=secret, world_dir=tmp_path / "w", nonce_db=tmp_path / "n"
    )
    assert r.effect == 0
    assert r.reason == "transition_modifiee"


def test_gate_params_extra_key_is_different_tau(tmp_path):
    secret = "s"
    enf = Enforcer(secret.encode())
    tau = Transition("a", "write", "x", {"n": 1})
    auth = enf.issue(tau)
    stuffed = Transition("a", "write", "x", {"n": 1, "x": "1"})
    r = invoke_gate(
        stuffed, auth, secret=secret, world_dir=tmp_path / "w", nonce_db=tmp_path / "n"
    )
    assert r.effect == 0


def test_gate_refuses_world_dir_symlink(tmp_path):
    secret = "s"
    victim = tmp_path / "victim"
    victim.mkdir()
    world = tmp_path / "world_link"
    world.symlink_to(victim)
    enf = Enforcer(secret.encode())
    tau = Transition("agent", "write", "x", {"n": 1})
    auth = enf.issue(tau)
    r = invoke_gate(tau, auth, secret=secret, world_dir=world, nonce_db=tmp_path / "n")
    assert r.effect == 0
    assert r.reason == "world_symlink"
    assert list(victim.iterdir()) == []


def test_gate_refuses_planted_file_symlink(tmp_path):
    secret = "s"
    world = tmp_path / "world"
    world.mkdir()
    outside = tmp_path / "OUTSIDE.txt"
    outside.write_text("SAFE")
    enf = Enforcer(secret.encode())
    tau = Transition("agent", "write", "x", {"n": 1})
    auth = enf.issue(tau)
    plant = world / f"{tau.hash()[:16]}.json"
    plant.symlink_to(outside)
    r = invoke_gate(tau, auth, secret=secret, world_dir=world, nonce_db=tmp_path / "n")
    assert r.effect == 0
    assert r.reason == "world_symlink"
    assert outside.read_text() == "SAFE"


def test_gate_refuses_nonce_symlink(tmp_path):
    secret = "s"
    victim = tmp_path / "PWNED_NONCE.txt"
    victim.write_text("SAFE\n")
    nonce = tmp_path / "nonce_link"
    nonce.symlink_to(victim)
    enf = Enforcer(secret.encode())
    tau = Transition("agent", "write", "x", {"n": 1})
    auth = enf.issue(tau)
    r = invoke_gate(
        tau, auth, secret=secret, world_dir=tmp_path / "w", nonce_db=nonce
    )
    assert r.effect == 0
    assert r.reason == "nonce_symlink"
    assert victim.read_text() == "SAFE\n"