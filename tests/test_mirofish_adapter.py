from vxruntime.mirofish_adapter import submit_simulation, PATH


def test_default_denial():
    called = []
    receipt = submit_simulation("m1", {"project_id": "p1"}, transport=lambda *a: called.append(a))
    assert receipt["status"] == "blocked" and not called
    assert receipt["ledger_valid"]


def test_local_approved_create_with_mock_and_evidence():
    called = []
    def fake(url, data):
        called.append((url, data))
        return {"success": True, "data": {"simulation_id": "s1", "project_id": "p1", "status": "created"}}
    r = submit_simulation("m2", {"project_id": "p1"}, approval=True, transport=fake)
    assert r["status"] == "success" and called[0][0].endswith(PATH)
    assert len(r["ledger_sha256"]) == 64 and not r["simulation_completed"]


def test_reject_remote_endpoint_and_spend():
    for kwargs in ({"endpoint": "https://external.example"}, {"budget_sar": 1}):
        r = submit_simulation("m3", {"project_id": "p1"}, approval=True,
                              transport=lambda *_: (_ for _ in ()).throw(AssertionError()), **kwargs)
        assert r["status"] == "blocked"


def test_identity_mismatch_fails_closed():
    r = submit_simulation("m4", {"project_id": "p1"}, approval=True,
                          transport=lambda *_: {"success": True, "data": {"simulation_id": "s", "project_id": "other"}})
    assert r["status"] == "failed"
    assert r["error"] == "MIROFISH_PROJECT_MISMATCH"


def test_bad_payload_denied():
    for p in ({"project_id": ""}, {"project_id": "p1", "unapproved": True},
              {"project_id": "p1", "enable_reddit": "true"}):
        assert submit_simulation("m5", p, approval=True, transport=lambda *_: {})["status"] == "blocked"


def test_transport_failure_is_not_success():
    def offline(*_):
        raise OSError("connection refused")
    r = submit_simulation("m6", {"project_id": "p1"}, approval=True, transport=offline)
    assert r["status"] == "failed" and r["ledger_valid"]
