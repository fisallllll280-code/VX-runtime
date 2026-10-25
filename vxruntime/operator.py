"""VX Sovereign Operator: simulation-first delegated local actions.

Capability grants are explicit; dry-run does not call any handler.
No implicit human identity, authority, network, financial or publication actions.
"""
from dataclasses import dataclass
from typing import Callable, Mapping
from .core import VXRuntime, ExecutionPolicy, ExecutionStatus, digest

SAFE_CAPABILITIES=frozenset({"inspect","analyze","draft","test_local"})
SENSITIVE_CAPABILITIES=frozenset({"merge","publish","pay","trade","send","delete","modify_canonical"})

@dataclass(frozen=True)
class OperatorReceipt:
    task_id: str
    phase: str
    decision: str
    reason: str
    fingerprint: str
    event_hash: str | None = None

class SovereignOperator:
    def __init__(self, permitted=SAFE_CAPABILITIES):
        permitted=frozenset(permitted)
        if permitted & SENSITIVE_CAPABILITIES or not permitted <= SAFE_CAPABILITIES:
            raise ValueError("UNSAFE_OPERATOR_GRANT")
        self.permitted=permitted
        self.runtime=VXRuntime(policy=ExecutionPolicy(
            allowed_capabilities=frozenset("operator."+x for x in permitted)))
        self.approved=set()
        self.simulations={}

    def simulate(self, task_id: str, capability: str, arguments: Mapping):
        if not task_id or not isinstance(arguments, Mapping):
            raise ValueError("INVALID_TASK")
        fingerprint=digest({"task_id":task_id,"capability":capability,"arguments":dict(arguments)})
        if capability not in self.permitted:
            return OperatorReceipt(task_id,"SIMULATED","BLOCK","CAPABILITY_DENIED",fingerprint)
        if arguments.get("external_effect") or arguments.get("spend_sar",0)!=0:
            return OperatorReceipt(task_id,"SIMULATED","BLOCK","EXTERNAL_EFFECT_OR_SPEND",fingerprint)
        if task_id in self.simulations and self.simulations[task_id]!=fingerprint:
            return OperatorReceipt(task_id,"SIMULATED","BLOCK","TASK_ID_CONFLICT",fingerprint)
        self.simulations[task_id]=fingerprint
        return OperatorReceipt(task_id,"SIMULATED","READY","LOCAL_SAFE_CANDIDATE",fingerprint)

    def approve(self, receipt: OperatorReceipt):
        if receipt.decision!="READY" or receipt.phase!="SIMULATED":
            raise PermissionError("SIMULATION_NOT_READY")
        if self.simulations.get(receipt.task_id)!=receipt.fingerprint:
            raise PermissionError("SIMULATION_RECEIPT_MISMATCH")
        self.approved.add((receipt.task_id,receipt.fingerprint))

    def execute(self, task_id: str, capability: str, arguments: Mapping,
                handler: Callable[[Mapping],object]):
        candidate=self.simulate(task_id,capability,arguments)
        if candidate.decision!="READY":
            return candidate
        if (task_id,candidate.fingerprint) not in self.approved:
            return OperatorReceipt(task_id,"EXECUTION","HOLD","EXPLICIT_APPROVAL_REQUIRED",candidate.fingerprint)
        if task_id in self.runtime.history:
            return OperatorReceipt(task_id,"EXECUTION","BLOCK","ALREADY_EXECUTED",candidate.fingerprint)
        result=self.runtime.execute(task_id,"operator."+capability,dict(arguments),handler)
        return OperatorReceipt(task_id,"EXECUTION",
              "EXECUTED" if result.status is ExecutionStatus.SUCCESS else "BLOCK",
              result.error or result.status.value,candidate.fingerprint,result.event_hash)
