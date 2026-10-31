from vx_runtime.core import VXRuntime
import pytest


def test_policy_precedes_execution():
    calls = []
    runtime = VXRuntime(lambda req: calls.append(req.execution_id) or {"ok": True})
    request = runtime.request("demo", {"x": 1}, approved=False)
    with pytest.raises(PermissionError):
        runtime.execute(request)
    assert calls == []


def test_execution_identity_and_hash_are_present():
    runtime = VXRuntime(lambda req: {"value": req.inputs["value"]})
    request = runtime.request("demo", {"value": 7}, approved=True)
    result = runtime.execute(request)
    assert result.execution_id == request.execution_id
    assert len(result.output_hash) == 64
