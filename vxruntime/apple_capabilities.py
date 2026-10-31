"""Bind read-only Apple discovery and update planning to VX capabilities."""
from __future__ import annotations

from typing import Any

from .apple_device import AppleDeviceAdapter, DiscoveryReport
from .core import Execution, VXRuntime


DISCOVER_CAPABILITY = "apple.device.discover"
PREPARE_UPDATE_CAPABILITY = "apple.update.prepare"


def execute_discovery(
    runtime: VXRuntime,
    execution_id: str,
    adapter: AppleDeviceAdapter | None = None,
) -> Execution:
    """Run discovery only when the host policy explicitly grants its capability."""
    selected = adapter or AppleDeviceAdapter()
    return runtime.execute(
        execution_id,
        DISCOVER_CAPABILITY,
        {"operation": "read_only_discovery"},
        lambda _inputs: selected.discover().to_dict(),
    )


def execute_update_preparation(
    runtime: VXRuntime,
    execution_id: str,
    report: DiscoveryReport,
) -> Execution:
    """Record a non-executable Update plan; never invoke Apple update software."""
    return runtime.execute(
        execution_id,
        PREPARE_UPDATE_CAPABILITY,
        {"discovery_status": report.status.value},
        lambda _inputs: AppleDeviceAdapter.prepare_update_plan(report),
    )


__all__ = [
    "DISCOVER_CAPABILITY",
    "PREPARE_UPDATE_CAPABILITY",
    "execute_discovery",
    "execute_update_preparation",
]
