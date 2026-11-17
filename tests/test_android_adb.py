import subprocess
import unittest
from unittest.mock import Mock

from vxruntime.android_adb import AdbError, ReadOnlyAdbBridge


class ReadOnlyAdbBridgeTests(unittest.TestCase):
    def test_inventory_uses_only_allowlisted_read_commands(self):
        outputs = iter(["device", "Pixel Test", "Acme", "16", "battery info", "storage info"])
        calls = []

        def runner(command, **kwargs):
            calls.append(command)
            return subprocess.CompletedProcess(command, 0, next(outputs), "")

        bridge = ReadOnlyAdbBridge("emulator-5554", runner=runner)
        result = bridge.inspect()

        self.assertEqual(result["model"], "Pixel Test")
        self.assertEqual(result["android_release"], "16")
        self.assertEqual(len(calls), 6)
        self.assertTrue(all(call[1:3] == ["-s", "emulator-5554"] for call in calls))
        self.assertFalse(any("install" in call or "uninstall" in call or "reboot" in call for call in calls))

    def test_rejects_invalid_serial(self):
        with self.assertRaises(ValueError):
            ReadOnlyAdbBridge("serial; rm -rf /")

    def test_fails_closed_when_device_not_ready(self):
        runner = Mock(return_value=subprocess.CompletedProcess([], 0, "unauthorized", ""))
        bridge = ReadOnlyAdbBridge("device-1", runner=runner)
        with self.assertRaisesRegex(AdbError, "DEVICE_NOT_READY"):
            bridge.inspect()

    def test_transport_error_is_normalized(self):
        def runner(*args, **kwargs):
            raise subprocess.TimeoutExpired("adb", 12)
        bridge = ReadOnlyAdbBridge("device-1", runner=runner)
        with self.assertRaisesRegex(AdbError, "ADB_TRANSPORT_UNAVAILABLE"):
            bridge.inspect()

    def test_nonzero_exit_is_rejected(self):
        runner = Mock(return_value=subprocess.CompletedProcess([], 1, "", "error"))
        bridge = ReadOnlyAdbBridge("device-1", runner=runner)
        with self.assertRaisesRegex(AdbError, "ADB_COMMAND_FAILED"):
            bridge.inspect()


if __name__ == "__main__":
    unittest.main()
