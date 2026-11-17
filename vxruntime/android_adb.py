"""Allowlisted, read-only ADB inventory adapter for VX.

No arbitrary shell command execution is exposed. Mutating ADB operations are
intentionally absent from this adapter.
"""
from __future__ import annotations

import re
import subprocess
from dataclasses import dataclass
from typing import Callable, Sequence

_SERIAL = re.compile(r"^[A-Za-z0-9._:-]{1,128}$")


class AdbError(RuntimeError):
    pass


@dataclass(frozen=True)
class AdbDevice:
    serial: str
    state: str
    details: str


class ReadOnlyAdbBridge:
    """Minimal ADB bridge restricted to device discovery and inventory."""

    def __init__(
        self,
        serial: str,
        adb_path: str = "adb",
        timeout_seconds: int = 12,
        runner: Callable[..., subprocess.CompletedProcess[str]] = subprocess.run,
    ) -> None:
        if not _SERIAL.fullmatch(serial):
            raise ValueError("INVALID_DEVICE_SERIAL")
        if timeout_seconds < 1 or timeout_seconds > 60:
            raise ValueError("INVALID_TIMEOUT")
        self.serial = serial
        self.adb_path = adb_path
        self.timeout_seconds = timeout_seconds
        self._runner = runner

    def _run(self, args: Sequence[str]) -> str:
        command = [self.adb_path, "-s", self.serial, *args]
        try:
            result = self._runner(
                command,
                capture_output=True,
                text=True,
                timeout=self.timeout_seconds,
                check=False,
            )
        except (OSError, subprocess.TimeoutExpired) as exc:
            raise AdbError("ADB_TRANSPORT_UNAVAILABLE") from exc
        if result.returncode != 0:
            raise AdbError("ADB_COMMAND_FAILED")
        return result.stdout.strip()

    def inspect(self) -> dict[str, str]:
        state = self._run(["get-state"])
        if state != "device":
            raise AdbError("DEVICE_NOT_READY")
        return {
            "serial": self.serial,
            "model": self._run(["shell", "getprop", "ro.product.model"]),
            "manufacturer": self._run(["shell", "getprop", "ro.product.manufacturer"]),
            "android_release": self._run(["shell", "getprop", "ro.build.version.release"]),
            "battery": self._run(["shell", "dumpsys", "battery"]),
            "data_storage": self._run(["shell", "df", "-h", "/data"]),
        }
