from aion.arbitre import Stake
from aion.enforcer import Enforcer, Transition
from aion.runtime import AionRuntime, Proposal, demo_transfer_10000
from aion.veritas import Evidence

def test_conflict_blocks_world():
    d = demo_transfer_10000()
    assert d["pass"] is True

def test_executer_allows_once():
    world = []
    rt = AionRuntime(Enforcer(b"t", world=lambda t: world.append(t.hash())))
    tau = Transition("a", "mail", "u@x", {})
    tr = rt.submit(Proposal(claim="ok", tau=tau, evidences=[Evidence("src", True, 0, True)], stake=Stake(reversible=True, cout=0.01)))
    assert tr.effect == 1 and len(world) == 1
    assert rt.bypass_attempt(tau, None).effect == 0
