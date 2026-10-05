from vxruntime import EventLedger, ExecutionPolicy, ExecutionStatus, VXRuntime


def test_execute_records_hash_chain_and_replays():
    runtime = VXRuntime(
        policy=ExecutionPolicy(allowed_capabilities=frozenset({"math.add"}))
    )

    result = runtime.execute(
        execution_id="exec-001",
        capability="math.add",
        inputs={"a": 21, "b": 21},
        worker=lambda payload: payload["a"] + payload["b"],
    )

    assert result.status is ExecutionStatus.SUCCESS
    assert result.output == 42
    assert runtime.verify() is True
    assert runtime.replay(
        "exec-001",
        lambda payload: payload["a"] + payload["b"],
    ) is True


def test_policy_blocks_before_worker():
    called = False

    def worker(_):
        nonlocal called
        called = True
        return 99

    runtime = VXRuntime(
        policy=ExecutionPolicy(allowed_capabilities=frozenset({"allowed"}))
    )
    result = runtime.execute("exec-002", "forbidden", {}, worker)

    assert result.status is ExecutionStatus.BLOCKED
    assert called is False
    assert runtime.verify() is True


def test_replay_detects_divergence():
    runtime = VXRuntime(
        policy=ExecutionPolicy(allowed_capabilities=frozenset({"math.add"}))
    )
    runtime.execute(
        "exec-003",
        "math.add",
        {"a": 2, "b": 3},
        lambda payload: payload["a"] + payload["b"],
    )

    assert runtime.replay(
        "exec-003",
        lambda _payload: 999,
    ) is False
