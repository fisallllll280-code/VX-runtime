from vxruntime.apple_device import AppleDeviceAdapter, DetectionStatus
from vxruntime.apple_capabilities import (
    DISCOVER_CAPABILITY,
    PREPARE_UPDATE_CAPABILITY,
    execute_discovery,
    execute_update_preparation,
)
from vxruntime.core import ExecutionPolicy, ExecutionStatus, VXRuntime


class FakePnp:
    def list_apple_devices(self):
        return [{
            "FriendlyName": "Apple Recovery (iBoot) Device",
            "InstanceId": r"USB\VID_05AC\DEVICE-1",
            "Status": "OK",
        }]


def test_discovery_is_blocked_without_explicit_vx_capability():
    runtime = VXRuntime(policy=ExecutionPolicy(allowed_capabilities=frozenset()))
    result = execute_discovery(runtime, "apple-discovery-denied", AppleDeviceAdapter(FakePnp()))
    assert result.status is ExecutionStatus.BLOCKED
    assert result.error == "CAPABILITY_DENIED"


def test_discovery_runs_only_with_explicit_read_capability():
    runtime = VXRuntime(policy=ExecutionPolicy(allowed_capabilities=frozenset({DISCOVER_CAPABILITY})))
    result = execute_discovery(runtime, "apple-discovery-allowed", AppleDeviceAdapter(FakePnp()))
    assert result.status is ExecutionStatus.SUCCESS
    assert result.output["status"] == DetectionStatus.DETECTED.value
    assert runtime.verify()


def test_update_preparation_is_separate_and_non_executable():
    adapter = AppleDeviceAdapter(FakePnp())
    report = adapter.discover()
    runtime = VXRuntime(policy=ExecutionPolicy(allowed_capabilities=frozenset({PREPARE_UPDATE_CAPABILITY})))
    result = execute_update_preparation(runtime, "apple-update-plan-only", report)
    assert result.status is ExecutionStatus.SUCCESS
    assert result.output["status"] == "PREPARED_NOT_EXECUTED"
    assert result.output["execution"] == "NONE"
    assert result.output["restore_allowed"] is False
    assert result.output["data_erasure_allowed"] is False
    assert runtime.verify()
