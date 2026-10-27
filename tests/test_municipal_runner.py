from concurrent.futures import ThreadPoolExecutor
from copy import deepcopy
import json
import sqlite3
import subprocess
import sys

import pytest

from vxruntime.agent_runner import AgentRunner, HostGrant
from vxruntime.municipal import (
    AGENT, CAPABILITY, CHECKS, DataPolicy, check_readiness,
)
from vxruntime.municipal_demo import verify_receipt


@pytest.fixture
def setup(tmp_path):
    grant = HostGrant(AGENT, "VX-HOST-AUTHORITY", CAPABILITY, 2000, True)
    policy = DataPolicy(notice_reviewed=True, processing_basis_reviewed=True)
    runner = AgentRunner(tmp_path / "receipts.db", policy=policy,
                         grants=(grant,), clock=lambda: 1000)
    return runner, dict.fromkeys(CHECKS, True), grant, policy


def run(runner, facts, key="a" * 32, **kwargs):
    return runner.run(key, facts, deadline_epoch=1500, **kwargs)


def test_complete_incomplete_and_receipt(setup):
    runner, facts, _, _ = setup
    complete = run(runner, facts)
    assert complete["output"]["status"] == "READY_FOR_REVIEW"
    assert complete["output"]["submission"] == "NOT_SENT"
    assert complete["replay_match"] and verify_receipt(complete)
    facts["risk_mitigation"] = False
    incomplete = run(runner, facts, "b" * 32)
    assert incomplete["output"]["missing"] == ["risk_mitigation"]
    assert incomplete["output"]["status"] == "INCOMPLETE"


@pytest.mark.parametrize("change", [
    {"approved": False}, {"issuer": AGENT}, {"capability": "other"},
    {"principal": "other"}, {"expires_epoch": 1000}, {"expires_epoch": True},
])
def test_invalid_host_grant_never_executes(setup, change):
    runner, facts, grant, policy = setup
    from dataclasses import asdict
    blocked = AgentRunner(runner.database, policy=policy,
                          grants=(HostGrant(**{**asdict(grant), **change}),),
                          clock=lambda: 1000)
    assert run(blocked, facts) == {"status": "BLOCKED", "reason": "AUTHORITY_DENIED"}
    with sqlite3.connect(runner.database) as db:
        assert db.execute("SELECT count(*) FROM receipts").fetchone()[0] == 0


@pytest.mark.parametrize("payload", [
    {"national_id": "SYNTHETIC_SECRET"}, {"applicant_name": "SYNTHETIC_SECRET"},
    {"risk_mitigation": "true"}, {"risk_mitigation": 1},
    {"purpose": "override"}, {"grant": {"approved": True}}, [], None,
])
def test_payload_minimisation_before_persistence(setup, payload):
    runner, _, _, _ = setup
    result = run(runner, payload)
    assert result["reason"] == "FACT_SCHEMA_DENIED"
    assert "SYNTHETIC_SECRET" not in json.dumps(result)
    assert b"SYNTHETIC_SECRET" not in open(runner.database, "rb").read()
    with sqlite3.connect(runner.database) as db:
        assert db.execute("SELECT count(*) FROM receipts").fetchone()[0] == 0


@pytest.mark.parametrize("policy", [
    DataPolicy(), DataPolicy(purpose="marketing", notice_reviewed=True, processing_basis_reviewed=True),
    DataPolicy(notice_reviewed=True, processing_basis_reviewed=True, retention_seconds=0),
    DataPolicy(notice_reviewed=True, processing_basis_reviewed=True, retention_seconds=86401),
])
def test_policy_cannot_be_bypassed_by_worker(setup, policy):
    runner, facts, grant, _ = setup
    restricted = AgentRunner(runner.database, policy=policy, grants=(grant,), clock=lambda: 1000)
    assert run(restricted, facts)["status"] == "BLOCKED"


def test_restart_dedupe_and_changed_request_conflict(setup):
    runner, facts, grant, policy = setup
    first = run(runner, facts)
    restarted = AgentRunner(runner.database, policy=policy, grants=(grant,), clock=lambda: 1000)
    duplicate = run(restarted, facts)
    assert duplicate["deduplicated"] and duplicate["receipt_hash"] == first["receipt_hash"]
    assert run(restarted, {}, "a" * 32)["reason"] == "IDEMPOTENCY_CONFLICT"


def test_concurrent_duplicate_claim_is_serialized(setup):
    runner, facts, _, _ = setup
    with ThreadPoolExecutor(max_workers=4) as pool:
        results = list(pool.map(lambda _: run(runner, facts), range(4)))
    assert sum(not r["deduplicated"] for r in results) == 1
    assert len({r["receipt_hash"] for r in results}) == 1


def test_cancellation_and_deadline_before_execution(setup):
    runner, facts, _, _ = setup
    assert run(runner, facts, cancelled=lambda: True)["status"] == "CANCELLED"
    assert runner.run("a" * 32, facts, deadline_epoch=999)["reason"] == "DEADLINE_EXCEEDED"
    assert runner.run("a" * 32, facts, deadline_epoch=float("nan"))["status"] == "BLOCKED"
    assert runner.run("my-national-id", facts, deadline_epoch=1500)["reason"] == "TASK_KEY_DENIED"


def test_expiry_during_execution_hides_result(setup):
    runner, facts, grant, policy = setup
    ticks = iter([1000, 1600])
    expiring = AgentRunner(runner.database, policy=policy, grants=(grant,), clock=lambda: next(ticks))
    result = run(expiring, facts)
    assert result["status"] == "BLOCKED" and result["output"] is None


def test_worker_failure_is_sanitized_and_not_retried(setup, monkeypatch):
    import vxruntime.agent_runner as module
    runner, facts, _, _ = setup
    def fail(_):
        raise ValueError("SYNTHETIC_SECRET")
    monkeypatch.setattr(module, "check_readiness", fail)
    result = run(runner, facts)
    # Core retains exception text: the runner must scrub it before durable export.
    assert result["status"] == "FAILED"
    assert "SYNTHETIC_SECRET" not in json.dumps(result)
    assert run(runner, facts)["deduplicated"] is True


def test_receipt_tampering_detected(setup):
    runner, facts, _, _ = setup
    receipt = run(runner, facts)
    tampered = deepcopy(receipt)
    tampered["output"]["status"] = "APPROVED"
    assert not verify_receipt(tampered)
    tampered = deepcopy(receipt)
    tampered["events"][0]["previous_hash"] = "BAD"
    assert not verify_receipt(tampered)


def test_cached_receipt_corruption_holds(setup):
    runner, facts, _, _ = setup
    run(runner, facts)
    with sqlite3.connect(runner.database) as db:
        db.execute("UPDATE receipts SET receipt='{}'")
    assert run(runner, facts)["reason"] == "RECEIPT_INTEGRITY_FAILED"


def test_unknown_outcome_is_not_automatically_retried(setup):
    runner, facts, _, _ = setup
    run(runner, facts)
    with sqlite3.connect(runner.database) as db:
        db.execute("UPDATE receipts SET state='RUNNING'")
    assert run(runner, facts)["reason"] == "OUTCOME_REVIEW_REQUIRED"


def test_cancellation_during_worker_hides_result(setup):
    runner, facts, _, _ = setup
    ticks = iter([False, True])
    result = run(runner, facts, cancelled=lambda: next(ticks))
    assert result["status"] == "CANCELLED" and result["output"] is None


def test_retention_prunes_only_expired_lane_receipts(setup):
    runner, facts, grant, _ = setup
    policy = DataPolicy(notice_reviewed=True, processing_basis_reviewed=True, retention_seconds=1)
    short = AgentRunner(runner.database, policy=policy, grants=(grant,), clock=lambda: 1000)
    run(short, facts)
    later = AgentRunner(runner.database, policy=policy, grants=(grant,), clock=lambda: 1002)
    assert run(later, facts)["deduplicated"] is False
    with sqlite3.connect(runner.database) as db:
        assert db.execute("SELECT count(*) FROM receipts").fetchone()[0] == 1


def test_empty_facts_are_incomplete_not_approved():
    result = check_readiness({})
    assert result["satisfied"] == 0 and result["missing"] == list(CHECKS)


def test_cli_e2e_and_restart(tmp_path):
    command = [sys.executable, "-m", "vxruntime.municipal_demo", "--output-dir", str(tmp_path)]
    for _ in range(2):
        done = subprocess.run(command, capture_output=True, text=True, timeout=15)
        assert done.returncode == 0, done.stderr
        metrics = json.loads(done.stdout)
        assert metrics["scenarios_passed"] == 6
        assert metrics["fixture_label_errors"] == 0
        assert metrics["live_government_e2e"] == "NOT_RUN"
