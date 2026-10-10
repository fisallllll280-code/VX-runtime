import pytest

from vxruntime import Event, EventLedger, ExecutionPolicy, ExecutionStatus, VXRuntime


def test_execute_records_hash_chain_and_replays():
    runtime = VXRuntime(
        policy=ExecutionPolicy(allowed_capabilities=frozenset({"math.add"}))
    )
    result = runtime.execute("exec-001", "math.add", {"a": 21, "b": 21}, lambda p: p["a"] + p["b"])
    assert result.status is ExecutionStatus.SUCCESS
    assert result.output == 42
    assert runtime.verify() is True
    assert runtime.replay("exec-001", lambda p: p["a"] + p["b"]) is True


def test_policy_blocks_before_worker():
    called = False

    def worker(_):
        nonlocal called
        called = True
        return 99

    runtime = VXRuntime(policy=ExecutionPolicy(allowed_capabilities=frozenset({"allowed"})))
    result = runtime.execute("exec-002", "forbidden", {}, worker)
    assert result.status is ExecutionStatus.BLOCKED
    assert called is False
    assert runtime.verify() is True


def test_replay_detects_divergence():
    runtime = VXRuntime(policy=ExecutionPolicy(allowed_capabilities=frozenset({"math.add"})))
    runtime.execute("exec-003", "math.add", {"a": 2, "b": 3}, lambda p: p["a"] + p["b"])
    assert runtime.replay("exec-003", lambda _p: 999) is False


def test_execution_identity_cannot_be_reused_or_overwritten():
    runtime = VXRuntime(policy=ExecutionPolicy(allowed_capabilities=frozenset({"math.add"})))
    original = runtime.execute("exec-004", "math.add", {"a": 1, "b": 2}, lambda p: p["a"] + p["b"])
    event_count = len(runtime.ledger.events)
    with pytest.raises(ValueError, match="EXECUTION_ID_ALREADY_USED"):
        runtime.execute("exec-004", "math.add", {"a": 40, "b": 2}, lambda p: p["a"] + p["b"])
    assert runtime.history["exec-004"] == original
    assert len(runtime.ledger.events) == event_count
    assert runtime.verify()


def test_nested_input_snapshot_survives_worker_mutation():
    runtime = VXRuntime(policy=ExecutionPolicy(allowed_capabilities=frozenset({"payload.inspect"})))
    supplied = {"nested": {"values": [1, 2]}}

    def worker(payload):
        payload["nested"]["values"].append(3)
        return len(payload["nested"]["values"])

    result = runtime.execute("exec-005", "payload.inspect", supplied, worker)
    assert supplied == {"nested": {"values": [1, 2]}}
    assert result.inputs == {"nested": {"values": [1, 2]}}
    assert result.input_hash == runtime.history["exec-005"].input_hash
    assert runtime.replay("exec-005", lambda p: len(p["nested"]["values"]) + 1) is True


def test_caller_mutation_after_execution_does_not_rewrite_replay_inputs():
    runtime = VXRuntime(policy=ExecutionPolicy(allowed_capabilities=frozenset({"payload.size"})))
    supplied = {"nested": {"values": [1]}}
    result = runtime.execute("exec-006", "payload.size", supplied, lambda p: len(p["nested"]["values"]))
    supplied["nested"]["values"].append(2)
    assert result.inputs == {"nested": {"values": [1]}}
    assert runtime.replay("exec-006", lambda p: len(p["nested"]["values"])) is True


def test_failed_execution_is_recorded_and_not_replayed_as_success():
    runtime = VXRuntime(policy=ExecutionPolicy(allowed_capabilities=frozenset({"failure.test"})))

    def fail(_):
        raise RuntimeError("expected failure")

    result = runtime.execute("exec-007", "failure.test", {}, fail)
    assert result.status is ExecutionStatus.FAILED
    assert result.error == "expected failure"
    assert runtime.replay("exec-007", lambda _: "unexpected") is False
    assert runtime.verify()


def test_event_ledger_rejects_wrong_previous_hash():
    ledger = EventLedger()
    bad = Event.build(
        event_id="bad-event",
        event_type="TEST",
        execution_id="exec-bad",
        capability="test",
        payload={},
        previous_hash="NOT-GENESIS",
    )
    with pytest.raises(ValueError, match="LEDGER_PREVIOUS_HASH_MISMATCH"):
        ledger.append(bad)
