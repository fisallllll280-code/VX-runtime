from vxruntime import ExecutionPolicy, VXRuntime
from vxruntime.admission import (
    AdmissionStatus, ProofBundle, evaluate_admission,
)


def setup_execution():
    runtime = VXRuntime(policy=ExecutionPolicy(allowed_capabilities=frozenset({"math.add"})))
    execution = runtime.execute("run-1", "math.add", {"a": 2, "b": 3}, lambda x: x["a"] + x["b"])
    proof = ProofBundle(
        execution_id=execution.execution_id,
        capability=execution.capability,
        input_hash=execution.input_hash,
        output_hash=execution.output_hash,
        source_commit="example-pinned-commit",
        verifier_identity="ci-verifier",
        verifier_result="PASS",
        evidence_hashes={
            "identity": "h1", "contract_tests": "h2",
            "security_tests": "h3", "execution_trace": "h4",
        },
    )
    return runtime, execution, proof


def decide(runtime, execution, proof):
    return evaluate_admission(execution, runtime.ledger, proof,
                              trusted_verifiers=frozenset({"ci-verifier"}))


def test_valid_bundle_admitted():
    runtime, execution, proof = setup_execution()
    assert decide(runtime, execution, proof).status is AdmissionStatus.ADMITTED


def test_missing_proof_is_hold():
    runtime, execution, _ = setup_execution()
    result = decide(runtime, execution, None)
    assert result.status is AdmissionStatus.HOLD
    assert result.reasons == ("PROOF_MISSING",)


def test_forged_output_hash_is_blocked():
    from dataclasses import replace
    runtime, execution, proof = setup_execution()
    assert decide(runtime, execution, replace(proof, output_hash="forged")).status is AdmissionStatus.BLOCKED


def test_untrusted_verifier_is_blocked():
    from dataclasses import replace
    runtime, execution, proof = setup_execution()
    assert decide(runtime, execution, replace(proof, verifier_identity="agent")).status is AdmissionStatus.BLOCKED


def test_absent_evidence_is_hold():
    from dataclasses import replace
    runtime, execution, proof = setup_execution()
    result = decide(runtime, execution, replace(proof, evidence_hashes={"identity": "h1"}))
    assert result.status is AdmissionStatus.HOLD


def test_failed_or_blocked_execution_cannot_be_admitted():
    runtime = VXRuntime()
    execution = runtime.execute("blocked-1", "unknown", {}, lambda _: "never")
    assert decide(runtime, execution, None).status is AdmissionStatus.BLOCKED


def test_unlinked_execution_event_is_blocked():
    from dataclasses import replace
    runtime, execution, proof = setup_execution()
    assert decide(runtime, replace(execution, event_hash="wrong"), proof).status is AdmissionStatus.BLOCKED


def test_nonpassing_verification_is_blocked():
    from dataclasses import replace
    runtime, execution, proof = setup_execution()
    assert decide(runtime, execution, replace(proof, verifier_result="FAIL")).status is AdmissionStatus.BLOCKED
