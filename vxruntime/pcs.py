"""PCS-001 proof-carrying state contracts.

This module enforces structural admission invariants only. It does not claim
that external evidence, signatures, or authority decisions are authentic;
those references must be verified by their owning adapters.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any, Mapping

from .core import digest


class AssuranceState(str, Enum):
    OPEN = "OPEN"
    VERIFIED = "VERIFIED"
    CONFLICTED = "CONFLICTED"
    INVALIDATED = "INVALIDATED"
    CLOSED = "CLOSED"


class AssuranceLevel(str, Enum):
    UNVERIFIED = "UNVERIFIED"
    SINGLE_SOURCE = "SINGLE_SOURCE"
    CORROBORATED = "CORROBORATED"
    CONFIRMED = "CONFIRMED"


class PromotionStatus(str, Enum):
    NOT_PROPOSED = "NOT_PROPOSED"
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    REVOKED = "REVOKED"


@dataclass(frozen=True)
class CandidateState:
    """State content and provenance, excluding proof and promotion decisions."""
    content: Mapping[str, Any]
    schema_version: str
    provenance_refs: tuple[str, ...]

    @property
    def state_cid(self) -> str:
        return digest({
            "content": dict(self.content),
            "schema_version": self.schema_version,
            "provenance_refs": list(self.provenance_refs),
        })


@dataclass(frozen=True)
class AssuranceReport:
    state_cid: str
    assurance_state: AssuranceState
    assurance_level: AssuranceLevel
    proof_bundle_cid: str
    verification_refs: tuple[str, ...]
    replayable: bool
    counterexample_refs: tuple[str, ...] = ()


@dataclass(frozen=True)
class PromotionDecision:
    decision_cid: str
    status: PromotionStatus
    authority_refs: tuple[str, ...]


@dataclass(frozen=True)
class PromotionReceipt:
    transition_cid: str
    pre_state_cid: str | None
    post_state_cid: str
    assurance_report_cid: str
    decision_cid: str
    guard_results: tuple[str, ...]
    evidence_hashes: tuple[str, ...]
    replay_hashes: tuple[str, ...]
    verifier_refs: tuple[str, ...]
    authority_refs: tuple[str, ...]


@dataclass(frozen=True)
class CanonicalState:
    state_cid: str
    schema_version: str
    provenance_refs: tuple[str, ...]
    proof_bundle_cid: str
    assurance_report_cid: str
    verification_refs: tuple[str, ...]
    promotion_receipt_cid: str
    decision_cid: str


def validate_promotion(
    candidate: CandidateState,
    report: AssuranceReport,
    decision: PromotionDecision,
    receipt: PromotionReceipt,
) -> CanonicalState:
    """Build a canonical state only when all local proof-carrying guards pass."""
    if candidate.state_cid != report.state_cid or candidate.state_cid != receipt.post_state_cid:
        raise ValueError("PCS_STATE_CID_MISMATCH")
    if report.assurance_state is not AssuranceState.VERIFIED:
        raise ValueError("PCS_ASSURANCE_NOT_VERIFIED")
    if report.assurance_level is AssuranceLevel.UNVERIFIED:
        raise ValueError("PCS_ASSURANCE_LEVEL_UNVERIFIED")
    if report.counterexample_refs:
        raise ValueError("PCS_COUNTEREXAMPLES_PRESENT")
    if not report.proof_bundle_cid:
        raise ValueError("PCS_PROOF_BUNDLE_REQUIRED")
    if not report.replayable:
        raise ValueError("PCS_REPLAY_REQUIRED")
    if not report.verification_refs:
        raise ValueError("PCS_VERIFICATION_REFS_REQUIRED")
    if not candidate.schema_version or not candidate.provenance_refs:
        raise ValueError("PCS_PROVENANCE_REQUIRED")
    if decision.status is not PromotionStatus.APPROVED:
        raise ValueError("PCS_PROMOTION_NOT_APPROVED")
    if not decision.decision_cid or not decision.authority_refs:
        raise ValueError("PCS_AUTHORITY_DECISION_REQUIRED")
    if receipt.decision_cid != decision.decision_cid:
        raise ValueError("PCS_DECISION_RECEIPT_MISMATCH")
    if not receipt.transition_cid or not receipt.assurance_report_cid:
        raise ValueError("PCS_TRANSITION_RECEIPT_REQUIRED")
    if not receipt.guard_results or any(result != "PASS" for result in receipt.guard_results):
        raise ValueError("PCS_GUARDS_NOT_PASSED")
    if not receipt.evidence_hashes or not receipt.replay_hashes or not receipt.verifier_refs:
        raise ValueError("PCS_TRANSITION_EVIDENCE_REQUIRED")
    if tuple(receipt.authority_refs) != tuple(decision.authority_refs):
        raise ValueError("PCS_AUTHORITY_REFS_MISMATCH")
    if receipt.assurance_report_cid != digest(report):
        raise ValueError("PCS_ASSURANCE_REPORT_CID_MISMATCH")

    return CanonicalState(
        state_cid=candidate.state_cid,
        schema_version=candidate.schema_version,
        provenance_refs=candidate.provenance_refs,
        proof_bundle_cid=report.proof_bundle_cid,
        assurance_report_cid=digest(report),
        verification_refs=report.verification_refs,
        promotion_receipt_cid=digest(receipt),
        decision_cid=decision.decision_cid,
    )
