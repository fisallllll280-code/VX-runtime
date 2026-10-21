"""Fail-closed verification of evidence before a VX admission decision.

This does not grant permissions, execute tools, or merge branches. It validates
a proof bundle against an exact execution and an independently supplied
verification verdict.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Mapping

from .core import Execution, ExecutionStatus, EventLedger


class AdmissionStatus(str, Enum):
    ADMITTED = "ADMITTED"
    HOLD = "HOLD"
    BLOCKED = "BLOCKED"


@dataclass(frozen=True)
class ProofBundle:
    execution_id: str
    capability: str
    input_hash: str
    output_hash: str
    source_commit: str
    verifier_identity: str
    verifier_result: str
    evidence_hashes: Mapping[str, str]


@dataclass(frozen=True)
class AdmissionDecision:
    status: AdmissionStatus
    reasons: tuple[str, ...]


REQUIRED_EVIDENCE = frozenset({"identity", "contract_tests", "security_tests", "execution_trace"})


def evaluate_admission(
    execution: Execution,
    ledger: EventLedger,
    proof: ProofBundle | None,
    *,
    trusted_verifiers: frozenset[str],
) -> AdmissionDecision:
    """Fail closed; neither a worker nor a proof bundle self-approves."""
    if execution.status is not ExecutionStatus.SUCCESS:
        return AdmissionDecision(AdmissionStatus.BLOCKED, ("EXECUTION_NOT_SUCCESSFUL",))
    if not ledger.verify():
        return AdmissionDecision(AdmissionStatus.BLOCKED, ("LEDGER_INVALID",))
    matching_events = [
        e for e in ledger.events
        if e.execution_id == execution.execution_id
        and e.capability == execution.capability
        and e.event_type == "EXECUTION_COMPLETED"
        and e.payload.get("input_hash") == execution.input_hash
        and e.payload.get("output_hash") == execution.output_hash
    ]
    if len(matching_events) != 1 or execution.event_hash != matching_events[0].event_hash:
        return AdmissionDecision(AdmissionStatus.BLOCKED, ("EXECUTION_EVENT_MISMATCH",))
    if proof is None:
        return AdmissionDecision(AdmissionStatus.HOLD, ("PROOF_MISSING",))
    if (proof.execution_id, proof.capability, proof.input_hash, proof.output_hash) != (
        execution.execution_id, execution.capability, execution.input_hash, execution.output_hash
    ):
        return AdmissionDecision(AdmissionStatus.BLOCKED, ("PROOF_EXECUTION_MISMATCH",))
    if not proof.source_commit:
        return AdmissionDecision(AdmissionStatus.HOLD, ("SOURCE_COMMIT_MISSING",))
    if proof.verifier_identity not in trusted_verifiers:
        return AdmissionDecision(AdmissionStatus.BLOCKED, ("UNTRUSTED_VERIFIER",))
    if proof.verifier_result != "PASS":
        return AdmissionDecision(AdmissionStatus.BLOCKED, ("VERIFICATION_NOT_PASSED",))
    missing = REQUIRED_EVIDENCE - {k for k, v in proof.evidence_hashes.items() if v}
    if missing:
        return AdmissionDecision(AdmissionStatus.HOLD, tuple(f"EVIDENCE_MISSING:{k}" for k in sorted(missing)))
    return AdmissionDecision(AdmissionStatus.ADMITTED, ())
