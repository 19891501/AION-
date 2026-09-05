from aion.actuators import make_enforcer_for_lab
from aion.enforcer import Enforcer, Transition, attack_bench

def test_valid_then_replay_blocked():
    enf = Enforcer(b"test-secret")
    tau = Transition("a", "pay", "x", {"n": 1})
    auth = enf.issue(tau)
    assert enf.execute(tau, auth).effect == 1
    assert enf.execute(tau, auth).effect == 0

def test_attack_bench_zero_unauthorized():
    enf = Enforcer(b"test-secret")
    tau = Transition("agent", "transfer", "iban", {"amount": 10000})
    auth = enf.issue(tau)
    report = attack_bench(enf, tau, auth)
    assert report["pass"] is True
    assert report["unauthorized_effects"] == 0

def test_lab_world_only_via_enforcer():
    enf, world = make_enforcer_for_lab(b"lab")
    tau = Transition("agent", "write", "file", {"k": 1})
    enf.execute(tau, None)
    assert world.mutations == 0
    auth = enf.issue(tau)
    enf.execute(tau, auth)
    assert world.mutations == 1
