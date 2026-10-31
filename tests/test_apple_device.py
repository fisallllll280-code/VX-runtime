import json

from vxruntime.apple_device import (
    AppleDeviceAdapter,
    DetectionStatus,
    DeviceMode,
)


class FakePnp:
    def __init__(self, items=None, error=None):
        self.items = items or []
        self.error = error

    def list_apple_devices(self):
        if self.error:
            raise self.error
        return self.items


def item(name="Apple Mobile Device USB Device", instance="USB\\VID_05AC&PID_12A8\\SERIAL"):
    return {
        "FriendlyName": name,
        "InstanceId": instance,
        "Status": "OK",
    }


def test_detects_one_apple_usb_interface_without_claiming_normal_mode():
    report = AppleDeviceAdapter(FakePnp([item()])).discover()
    assert report.status is DetectionStatus.DETECTED
    assert len(report.devices) == 1
    assert report.devices[0].mode is DeviceMode.UNKNOWN
    assert "SERIAL" not in json.dumps(report.to_dict())


def test_recovery_and_dfu_are_classified_separately():
    recovery = AppleDeviceAdapter(FakePnp([item("Apple Recovery (iBoot) Device")])).discover()
    dfu = AppleDeviceAdapter(FakePnp([item("Apple DFU Device")])).discover()
    assert recovery.devices[0].mode is DeviceMode.RECOVERY
    assert dfu.devices[0].mode is DeviceMode.DFU


def test_no_device_is_not_detected():
    report = AppleDeviceAdapter(FakePnp()).discover()
    assert report.status is DetectionStatus.NOT_DETECTED
    assert report.devices == ()


def test_multiple_interfaces_are_ambiguous_and_update_is_held():
    report = AppleDeviceAdapter(FakePnp([
        item(instance="USB\\VID_05AC\\A"),
        item(instance="USB\\VID_05AC\\B"),
    ])).discover()
    assert report.status is DetectionStatus.AMBIGUOUS
    assert AppleDeviceAdapter.prepare_update_plan(report)["status"] == "HOLD"


def test_provider_failure_is_unavailable_not_not_detected():
    report = AppleDeviceAdapter(FakePnp(error=OSError("unavailable"))).discover()
    assert report.status is DetectionStatus.UNAVAILABLE


def test_update_plan_is_non_executable_and_never_allows_restore():
    report = AppleDeviceAdapter(FakePnp([item("Apple Recovery (iBoot) Device")])).discover()
    plan = AppleDeviceAdapter.prepare_update_plan(report)
    assert plan["status"] == "PREPARED_NOT_EXECUTED"
    assert plan["execution"] == "NONE"
    assert plan["restore_allowed"] is False
    assert plan["data_erasure_allowed"] is False
    assert len(plan["plan_sha256"]) == 64


def test_dfu_does_not_prepare_update():
    report = AppleDeviceAdapter(FakePnp([item("Apple DFU Device")])).discover()
    assert AppleDeviceAdapter.prepare_update_plan(report)["status"] == "HOLD"
