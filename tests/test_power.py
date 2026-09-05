from aion.power import ControlPlane, HostileAgent, power_bench
from aion.enforcer import Transition
from aion.veritas import Evidence
from aion.arbitre import Stake

def test_power_bench_metric(tmp_path):
    report = power_bench(tmp_path)
    assert report["UNAUTHORIZED_EFFECTS"] == 0
    assert report["LEGITIMATE_EFFECTS"] >= 1
    assert report["PASS"] is True

def test_hostile_agent_has_no_secret(tmp_path):
    plane = ControlPlane("s3cr3t", world_dir=tmp_path / "w", nonce_db=tmp_path / "n")
    agent = HostileAgent(plane)
    assert not hasattr(agent, "_secret")

def test_authorized_path_conflict_zero_effect(tmp_path):
    plane = ControlPlane("s3cr3t", world_dir=tmp_path / "w", nonce_db=tmp_path / "n")
    tau = Transition("agent", "transfer", "iban", {"amount": 8000})
    out = plane.authorized_path("beneficiaire conforme", tau, [Evidence("bank", True, 0, True), Evidence("compliance", False, 0, True)], Stake(reversible=False, cout=8000, seuil_humain=50))
    assert out["effect"] == 0
