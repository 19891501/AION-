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
    bad = [d for d in report["detail"] if d["attack"] != "nonce_reutilise"]
    assert sum(d["effect"] for d in bad) == 0
