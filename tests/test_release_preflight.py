from vxruntime.release_preflight import assess, FILE
import json

def load():
    return json.loads(FILE.read_text(encoding="utf-8"))

def test_first_release_held():
    r = assess(load())
    assert r["decision"] == "HOLD"
    assert "UNVERIFIED_GATE" in r["blocking_reasons"]
    assert r["deployment_performed"] is False

def test_claimed_verification_does_not_auto_publish():
    r = load()
    r["checks"] = {k:"VERIFIED" for k in r["checks"]}
    result = assess(r)
    assert result["decision"] == "HOLD"
    assert result["evidence_verified_by_independent_authority"] is False

def test_spend_and_publish_are_denied():
    for mutation in [
        lambda r:r["policy"].update(external_spend_sar=1),
        lambda r:r["policy"].update(public_deployment=True),
        lambda r:r["policy"].update(merge_to_main=True),
        lambda r:r["policy"].update(protected_files_unchanged=False),
    ]:
        r=load()
        mutation(r)
        assert assess(r)["blocking_reasons"]
