import unittest

from vxruntime.device_control import (
    ApprovalReceipt,
    Decision,
    DeviceOperation,
    DeviceRequest,
    SupervisedDeviceController,
)


class FakeAdapter:
    def __init__(self):
        self.inspections = 0
        self.applies = []

    def inspect(self, parameters):
        self.inspections += 1
        return {"device_connected": False, "parameters": dict(parameters)}

    def apply(self, operation, parameters):
        self.applies.append((operation, dict(parameters)))
        return {"accepted": True}


class SupervisedDeviceControllerTests(unittest.TestCase):
    def setUp(self):
        self.adapter = FakeAdapter()
        self.controller = SupervisedDeviceController(self.adapter)

    def test_inspection_is_read_only(self):
        result = self.controller.execute(
            DeviceRequest("r1", DeviceOperation.INSPECT, {"scope": "basic"})
        )
        self.assertEqual(result.decision, Decision.ALLOWED)
        self.assertEqual(result.status, "observed")
        self.assertEqual(self.adapter.inspections, 1)
        self.assertEqual(self.adapter.applies, [])

    def test_mutation_without_approval_is_blocked(self):
        result = self.controller.execute(
            DeviceRequest("r2", DeviceOperation.REPAIR_SETTINGS, {"setting": "x"})
        )
        self.assertEqual(result.decision, Decision.REQUIRES_APPROVAL)
        self.assertEqual(self.adapter.applies, [])

    def test_approval_must_match_exact_request_and_parameters(self):
        request = DeviceRequest(
            "r3", DeviceOperation.REPAIR_SETTINGS, {"setting": "brightness"}
        )
        wrong = ApprovalReceipt(
            "r3", DeviceOperation.REPAIR_SETTINGS, "wrong-hash", "approval-1", True
        )
        result = self.controller.execute(request, wrong)
        self.assertEqual(result.decision, Decision.DENIED)
        self.assertEqual(self.adapter.applies, [])

    def test_valid_approval_executes_once(self):
        request = DeviceRequest(
            "r4", DeviceOperation.REPAIR_SETTINGS, {"setting": "brightness"}
        )
        approval = ApprovalReceipt(
            "r4",
            DeviceOperation.REPAIR_SETTINGS,
            request.parameters_hash,
            "approval-2",
            True,
        )
        first = self.controller.execute(request, approval)
        second = self.controller.execute(request, approval)
        self.assertEqual(first.status, "executed")
        self.assertEqual(second.decision, Decision.DENIED)
        self.assertEqual(len(self.adapter.applies), 1)

    def test_root_access_is_never_allowed(self):
        result = self.controller.execute(
            DeviceRequest("r5", DeviceOperation.ROOT_ACCESS, {})
        )
        self.assertEqual(result.decision, Decision.DENIED)
        self.assertEqual(self.adapter.applies, [])

    def test_reboot_requires_explicit_approval(self):
        result = self.controller.execute(
            DeviceRequest("r6", DeviceOperation.REBOOT, {})
        )
        self.assertEqual(result.decision, Decision.REQUIRES_APPROVAL)
        self.assertEqual(self.adapter.applies, [])


if __name__ == "__main__":
    unittest.main()
