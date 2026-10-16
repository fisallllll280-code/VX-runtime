import pytest

from vxruntime.pcs import (
    AssuranceLevel, AssuranceReport, AssuranceState, CandidateState,
    PromotionDecision, PromotionReceipt, PromotionStatus, validate_promotion,
)
from vxruntime.core import digest


def fixture_state():
    candidate = CandidateState({"component": "router"}, "pcs-001/v1", ("commit:abc",))
    report = AssuranceReport(
        candidate.state_cid, AssuranceState.VERIFIED, AssuranceLevel.CORROBORATED,
        "proof:bundle:1", ("verifier:tests",), True,
    )
    decision = PromotionDecision("decision:1", PromotionStatus.APPROVED, ("authority:1",))
    receipt = PromotionReceipt(
        "transition:1", None, candidate.state_cid, digest(report), decision.decision_cid,
        ("PASS",), ("sha256:evidence",), ("sha256:replay",), ("verifier:tests",),
        decision.authority_refs,
    )
    return candidate, report, decision, receipt


def test_valid_candidate_builds_canonical_state():
    candidate, report, decision, receipt = fixture_state()
    result = validate_promotion(candidate, report, decision, receipt)
    assert result.state_cid == candidate.state_cid
    assert result.promotion_receipt_cid == digest(receipt)


def test_unverified_state_is_rejected():
    from dataclasses import replace
    candidate, report, decision, receipt = fixture_state()
    report = replace(report, assurance_state=AssuranceState.OPEN)
    receipt = replace(receipt, assurance_report_cid=digest(report))
    with pytest.raises(ValueError, match="PCS_ASSURANCE_NOT_VERIFIED"):
        validate_promotion(candidate, report, decision, receipt)


def test_missing_proof_bundle_is_rejected():
    from dataclasses import replace
    candidate, report, decision, receipt = fixture_state()
    report = replace(report, proof_bundle_cid="")
    receipt = replace(receipt, assurance_report_cid=digest(report))
    with pytest.raises(ValueError, match="PCS_PROOF_BUNDLE_REQUIRED"):
        validate_promotion(candidate, report, decision, receipt)


def test_pending_promotion_is_rejected():
    from dataclasses import replace
    candidate, report, decision, receipt = fixture_state()
    decision = replace(decision, status=PromotionStatus.PENDING)
    with pytest.raises(ValueError, match="PCS_PROMOTION_NOT_APPROVED"):
        validate_promotion(candidate, report, decision, receipt)


def test_state_reference_mismatch_is_rejected():
    from dataclasses import replace
    candidate, report, decision, receipt = fixture_state()
    receipt = replace(receipt, post_state_cid="different-state")
    with pytest.raises(ValueError, match="PCS_STATE_CID_MISMATCH"):
        validate_promotion(candidate, report, decision, receipt)
