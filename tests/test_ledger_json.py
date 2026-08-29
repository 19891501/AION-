import json

from aion import Ledger


def test_export_json_relisible():
    led = Ledger()
    led.append("f", "HYPOTHESIS", justification="observe", source="web", context="lab")
    data = json.loads(led.to_json())
    assert data[0]["fact"] == "f"
    assert data[0]["predecessor"] is None
    assert len(data[0]["hash"]) == 64
