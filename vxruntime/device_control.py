"""Supervised Android device-control boundary for VX.

This module is a policy-gated adapter contract. It does not itself grant Android,
ADB, root, accessibility, or device-owner privileges.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Mapping, Protocol

from .core import digest


class DeviceOperation(str, Enum):
    INSPECT = "device.inspect"
    REPAIR_SETTINGS = "device.repair_settings"
    INSTALL_PACKAGE = "device.install_package"
    DELETE_DATA = "device.delete_data"
    REBOOT = "device.reboot"
    ROOT_ACCESS = "device.root_access"


class Decision(str, Enum):
    ALLOWED = "allowed"
    REQUIRES_APPROVAL = "requires_approval"
    DENIED = "denied"


@dataclass(frozen=True)
class DeviceRequest:
    request_id: str
    operation: DeviceOperation
    parameters: Mapping[str, Any] = field(default_factory=dict)

    @property
    def parameters_hash(self) -> str:
        return digest(dict(self.parameters))


@dataclass(frozen=True)
class ApprovalReceipt:
    """Host-issued approval bound to one request and its exact parameters.

    Production hosts must issue this object only after an authenticated,
    explicit human confirmation. A caller-created receipt is not a trusted
    production authorization mechanism.
    """

    request_id: str
    operation: DeviceOperation
    parameters_hash: str
    approval_id: str
    approved: bool


@dataclass(frozen=True)
class DeviceResult:
    decision: Decision
    status: str
    detail: str


class AndroidAdapter(Protocol):
    def inspect(self, parameters: Mapping[str, Any]) -> Mapping[str, Any]: ...

    def apply(
        self, operation: DeviceOperation, parameters: Mapping[str, Any]
    ) -> Mapping[str, Any]: ...


class DevicePolicy:
    """Fail-closed policy for supervised device operations."""

    READ_ONLY = frozenset({DeviceOperation.INSPECT})
    APPROVAL_REQUIRED = frozenset(
        {
            DeviceOperation.REPAIR_SETTINGS,
            DeviceOperation.INSTALL_PACKAGE,
            DeviceOperation.DELETE_DATA,
            DeviceOperation.REBOOT,
        }
    )
    NEVER_ALLOWED = frozenset({DeviceOperation.ROOT_ACCESS})

    def decide(
        self, request: DeviceRequest, approval: ApprovalReceipt | None
    ) -> Decision:
        if not request.request_id:
            return Decision.DENIED
        if request.operation in self.NEVER_ALLOWED:
            return Decision.DENIED
        if request.operation in self.READ_ONLY:
            return Decision.ALLOWED
        if request.operation not in self.APPROVAL_REQUIRED:
            return Decision.DENIED
        if approval is None or not approval.approved:
            return Decision.REQUIRES_APPROVAL
        if (
            approval.request_id != request.request_id
            or approval.operation is not request.operation
            or approval.parameters_hash != request.parameters_hash
            or not approval.approval_id
        ):
            return Decision.DENIED
        return Decision.ALLOWED


class SupervisedDeviceController:
    """Executes only through an injected adapter after policy authorization."""

    def __init__(self, adapter: AndroidAdapter, policy: DevicePolicy | None = None):
        self._adapter = adapter
        self._policy = policy or DevicePolicy()
        self._consumed_approvals: set[str] = set()

    def execute(
        self,
        request: DeviceRequest,
        approval: ApprovalReceipt | None = None,
    ) -> DeviceResult:
        decision = self._policy.decide(request, approval)
        if decision is not Decision.ALLOWED:
            return DeviceResult(
                decision=decision,
                status="blocked",
                detail="No device operation was performed.",
            )

        if request.operation is DeviceOperation.INSPECT:
            observation = self._adapter.inspect(dict(request.parameters))
            return DeviceResult(
                decision=Decision.ALLOWED,
                status="observed",
                detail=digest(observation),
            )

        assert approval is not None  # enforced by DevicePolicy
        if approval.approval_id in self._consumed_approvals:
            return DeviceResult(
                decision=Decision.DENIED,
                status="blocked",
                detail="Approval receipt has already been consumed.",
            )
        self._consumed_approvals.add(approval.approval_id)
        outcome = self._adapter.apply(
            request.operation, dict(request.parameters)
        )
        return DeviceResult(
            decision=Decision.ALLOWED,
            status="executed",
            detail=digest(outcome),
        )
