from aion.enforcer import Enforcer, Transition
from aion.gate_bridge import invoke_gate

def test_gate_process_blocks_and_allows(tmp_path):
    secret = "test-gate-secret"
    world, nonces = tmp_path / "world", tmp_path / "nonces"
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
    r = invoke_gate(Transition("a", "pay", "evil", {}), auth, secret=secret, world_dir=tmp_path / "w", nonce_db=tmp_path / "n")
    assert r.effect == 0 and r.reason == "transition_modifiee"
