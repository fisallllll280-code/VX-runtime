"""Read-only Apple device discovery and update planning for VX.

This module never installs drivers, pairs/trusts a device, downloads firmware,
or invokes Apple Devices/iTunes update or restore actions. Windows discovery is
performed with one fixed PowerShell query; no user-provided command is executed.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from enum import Enum
import hashlib
import json
import platform
import subprocess
from typing import Any, Mapping, Protocol


class DetectionStatus(str, Enum):
    DETECTED = "DETECTED"
    NOT_DETECTED = "NOT_DETECTED"
    AMBIGUOUS = "AMBIGUOUS"
    UNAVAILABLE = "UNAVAILABLE"


class DeviceMode(str, Enum):
    NORMAL = "NORMAL"
    RECOVERY = "RECOVERY"
    DFU = "DFU"
    UNKNOWN = "UNKNOWN"


@dataclass(frozen=True)
class ApplePnpDevice:
    device_fingerprint: str
    label: str
    pnp_status: str
    mode: DeviceMode
    evidence_source: str = "WINDOWS_PNP"


@dataclass(frozen=True)
class DiscoveryReport:
    status: DetectionStatus
    devices: tuple[ApplePnpDevice, ...]
    host_platform: str
    observed_at_utc: str
    reason: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "status": self.status.value,
            "devices": [
                {**asdict(device), "mode": device.mode.value}
                for device in self.devices
            ],
            "host_platform": self.host_platform,
            "observed_at_utc": self.observed_at_utc,
            "reason": self.reason,
        }


class PnpProvider(Protocol):
    def list_apple_devices(self) -> list[Mapping[str, Any]]: ...


class WindowsPnpProvider:
    """Read-only PnP query. It does not invoke pnputil mutation commands."""

    _SCRIPT = (
        "$ErrorActionPreference='Stop'; "
        "$items = @(Get-PnpDevice -PresentOnly | "
        "Where-Object { $_.InstanceId -match 'VID_05AC' -or "
        "$_.FriendlyName -match 'Apple Mobile Device|iPhone|iBoot|Recovery|DFU' } | "
        "Select-Object Class,FriendlyName,Status,InstanceId); "
        "ConvertTo-Json -InputObject $items -Compress"
    )

    def __init__(self, timeout_seconds: int = 12) -> None:
        if timeout_seconds < 1 or timeout_seconds > 30:
            raise ValueError("TIMEOUT_OUT_OF_RANGE")
        self.timeout_seconds = timeout_seconds

    def list_apple_devices(self) -> list[Mapping[str, Any]]:
        if platform.system() != "Windows":
            raise OSError("WINDOWS_PNP_REQUIRES_WINDOWS")
        completed = subprocess.run(
            [
                "powershell.exe", "-NoLogo", "-NoProfile", "-NonInteractive",
                "-ExecutionPolicy", "AllSigned", "-Command", self._SCRIPT,
            ],
            capture_output=True,
            text=True,
            timeout=self.timeout_seconds,
            check=False,
        )
        if completed.returncode != 0:
            raise OSError("WINDOWS_PNP_QUERY_FAILED")
        raw = completed.stdout.strip()
        if not raw:
            return []
        parsed = json.loads(raw)
        if isinstance(parsed, dict):
            parsed = [parsed]
        if not isinstance(parsed, list):
            raise ValueError("INVALID_PNP_RESPONSE")
        return [item for item in parsed if isinstance(item, dict)]


def _mode(label: str) -> DeviceMode:
    value = label.casefold()
    if "dfu" in value:
        return DeviceMode.DFU
    if "recovery" in value or "iboot" in value:
        return DeviceMode.RECOVERY
    # Do not infer NORMAL merely because a generic Apple USB interface exists.
    return DeviceMode.UNKNOWN


def _fingerprint(instance_id: str) -> str:
    if not instance_id:
        return ""
    return hashlib.sha256(instance_id.encode("utf-8", errors="replace")).hexdigest()


class AppleDeviceAdapter:
    """Produces bounded, read-only host observations and a non-executable plan."""

    def __init__(self, provider: PnpProvider | None = None) -> None:
        self.provider = provider or WindowsPnpProvider()

    def discover(self) -> DiscoveryReport:
        observed = datetime.now(timezone.utc).isoformat()
        try:
            raw_devices = self.provider.list_apple_devices()
        except (OSError, subprocess.TimeoutExpired, json.JSONDecodeError, ValueError) as exc:
            return DiscoveryReport(
                DetectionStatus.UNAVAILABLE, (), platform.system(), observed,
                "DISCOVERY_UNAVAILABLE:" + type(exc).__name__,
            )

        devices: list[ApplePnpDevice] = []
        for item in raw_devices:
            instance_id = str(item.get("InstanceId") or "")
            label = str(item.get("FriendlyName") or "Apple USB device")[:160]
            status = str(item.get("Status") or "UNKNOWN")[:40]
            devices.append(
                ApplePnpDevice(
                    device_fingerprint=_fingerprint(instance_id),
                    label=label,
                    pnp_status=status,
                    mode=_mode(label),
                )
            )

        if not devices:
            result, reason = DetectionStatus.NOT_DETECTED, "NO_PRESENT_APPLE_PNP_DEVICE"
        elif len(devices) == 1:
            result, reason = DetectionStatus.DETECTED, "ONE_APPLE_PNP_INTERFACE_OBSERVED"
        else:
            result, reason = DetectionStatus.AMBIGUOUS, "MULTIPLE_APPLE_PNP_INTERFACES_REQUIRE_CORRELATION"

        return DiscoveryReport(result, tuple(devices), platform.system(), observed, reason)

    @staticmethod
    def prepare_update_plan(report: DiscoveryReport) -> dict[str, Any]:
        """Prepare instructions only. This method cannot execute an update."""
        eligible = (
            report.status is DetectionStatus.DETECTED
            and len(report.devices) == 1
            and report.devices[0].mode in {DeviceMode.NORMAL, DeviceMode.RECOVERY}
        )
        plan = {
            "plan_type": "APPLE_OFFICIAL_UPDATE",
            "status": "PREPARED_NOT_EXECUTED" if eligible else "HOLD",
            "device_fingerprint": report.devices[0].device_fingerprint if eligible else None,
            "precondition": "USER_APPROVAL_REQUIRED_BEFORE_OPENING_APPLE_DEVICES_UPDATE",
            "execution": "NONE",
            "restore_allowed": False,
            "data_erasure_allowed": False,
            "reason": "DISCOVERY_ACCEPTED" if eligible else "DEVICE_DISCOVERY_NOT_UNAMBIGUOUS_OR_MODE_UNSUPPORTED",
        }
        canonical = json.dumps(plan, sort_keys=True, separators=(",", ":"))
        plan["plan_sha256"] = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
        return plan


__all__ = [
    "AppleDeviceAdapter", "ApplePnpDevice", "DetectionStatus",
    "DeviceMode", "DiscoveryReport", "WindowsPnpProvider",
]
