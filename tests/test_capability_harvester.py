import hashlib
import json
import sqlite3
import subprocess
import tempfile
import unittest
from dataclasses import replace
from pathlib import Path
from unittest.mock import patch

from vxruntime.capability_harvester import (
    CapabilityPassport, CapabilityRegistry, CompatibilityPolicy, EvidenceRunner, SMOKE,
)
from vxruntime.core import ExecutionPolicy, ExecutionStatus, VXRuntime, digest
from vxruntime.admission import AdmissionStatus, ProofBundle, REQUIRED_EVIDENCE


class HarvesterTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.path = str(Path(self.tmp.name) / "registry.sqlite")
        self.registry = CapabilityRegistry(self.path)
        self.policy = CompatibilityPolicy("test-policy-v1", frozenset({"MIT"}))
        self.artifact = b"inert fixture; never imported"
        self.passport = CapabilityPassport(
            "fixture.hash", "1.0", "MIT", "https://example.com/source",
            "a" * 40, hashlib.sha256(self.artifact).hexdigest(), "fixture.contract.v1",
        )
        self.registry.register(self.passport, self.policy)
        self.runtime = VXRuntime(policy=ExecutionPolicy(allowed_capabilities=frozenset({SMOKE})))
        self.runner = EvidenceRunner(self.registry, self.runtime, self.policy)

    def tearDown(self):
        self.registry.close()
        self.tmp.cleanup()

    def run_smoke(self):
        return self.runner.run("fixture.hash", "1.0", self.artifact)

    def test_persistent_inventory_and_relationships(self):
        p = replace(self.passport, capability_id="parent", dependencies=(("fixture.hash", "1.0"),))
        self.registry.register(p, self.policy)
        self.registry.close()
        self.registry = CapabilityRegistry(self.path)
        self.assertEqual(self.registry.get("parent", "1.0"), p)
        self.assertEqual(self.registry.db.execute("SELECT dependency_id FROM relationships").fetchone()[0], "fixture.hash")

    def test_version_is_immutable_and_registration_idempotent(self):
        self.registry.register(self.passport, self.policy)
        with self.assertRaisesRegex(ValueError, "IMMUTABLE_VERSION_CONFLICT"):
            self.registry.register(replace(self.passport, contract_ref="changed"), self.policy)

    def test_gate_rejects_incomplete_denied_unpinned_passports(self):
        for fields in ({"license": "UNKNOWN"}, {"permissions": ("network",)},
                       {"source_commit": "main"}, {"artifact_sha256": "bad"},
                       {"contract_ref": ""}, {"source_url": "file:///etc/passwd"}):
            with self.subTest(fields=fields), self.assertRaises(ValueError):
                self.registry.register(replace(self.passport, **fields), self.policy)

    def test_real_subprocess_smoke_records_evidence_without_adoption(self):
        execution = self.run_smoke()
        self.assertIs(execution.status, ExecutionStatus.SUCCESS)
        self.assertTrue(self.runtime.verify())
        receipt = self.registry.receipt(execution.execution_id)
        self.assertEqual(receipt["passport"], self.passport.fingerprint)
        self.assertEqual(receipt["integration_status"], "PENDING SOURCE VALIDATION")
        self.assertFalse(receipt["canonical_write"])
        self.assertFalse(receipt["independent_verification"])
        self.assertEqual(receipt["events"][0]["event_hash"], execution.event_hash)
        self.assertIs(self.runner.review(execution, None, trusted_verifiers=frozenset()).status, AdmissionStatus.HOLD)

    def test_runtime_policy_denies_before_subprocess(self):
        self.runtime.policy = ExecutionPolicy()
        with patch("vxruntime.capability_harvester.subprocess.run") as process:
            execution = self.run_smoke()
        process.assert_not_called()
        self.assertIs(execution.status, ExecutionStatus.BLOCKED)
        self.assertIs(self.runner.review(execution, None, trusted_verifiers=frozenset()).status, AdmissionStatus.BLOCKED)

    def test_review_requires_independent_verifier_and_exact_source_evidence(self):
        execution = self.run_smoke()
        proof = ProofBundle(
            execution.execution_id, execution.capability, execution.input_hash,
            execution.output_hash, self.passport.source_commit, "VV.fixture", "PASS",
            {**{key: "fixture-evidence" for key in REQUIRED_EVIDENCE},
             "capability_smoke": digest(self.registry.receipt(execution.execution_id))},
        )
        self.assertIs(self.runner.review(execution, proof, trusted_verifiers=frozenset()).status, AdmissionStatus.BLOCKED)
        trusted = frozenset({"VV.fixture"})
        self.assertIs(self.runner.review(execution, proof, trusted_verifiers=trusted).status, AdmissionStatus.ADMITTED)
        for changed in (replace(proof, source_commit="b" * 40),
                        replace(proof, evidence_hashes={}), replace(proof, verifier_result="FAIL")):
            self.assertIs(self.runner.review(execution, changed, trusted_verifiers=trusted).status, AdmissionStatus.BLOCKED)
        self.assertFalse(self.registry.receipt(execution.execution_id)["canonical_write"])

    def test_fabricated_child_result_fails(self):
        with patch("vxruntime.capability_harvester.subprocess.run", return_value=subprocess.CompletedProcess([], 0, b'{}')):
            execution = self.run_smoke()
        self.assertIs(execution.status, ExecutionStatus.FAILED)
        self.assertIn("SMOKE_OUTPUT_MISMATCH", execution.error)

    def test_changed_artifact_fails_before_process(self):
        with patch("vxruntime.capability_harvester.subprocess.run") as process:
            execution = self.runner.run("fixture.hash", "1.0", b"changed")
        process.assert_not_called()
        self.assertIs(execution.status, ExecutionStatus.FAILED)
        self.assertIn("ARTIFACT_DIGEST_MISMATCH", execution.error)

    def test_current_policy_is_rechecked(self):
        self.runner.policy = CompatibilityPolicy("revoked", frozenset())
        with patch("vxruntime.capability_harvester.subprocess.run") as process:
            execution = self.run_smoke()
        process.assert_not_called()
        self.assertIn("LICENSE_DENIED", execution.error)

    def test_missing_dependency_blocks_smoke(self):
        p = replace(self.passport, capability_id="parent", dependencies=(("missing", "1"),))
        self.registry.register(p, self.policy)
        with patch("vxruntime.capability_harvester.subprocess.run") as process:
            execution = self.runner.run("parent", "1.0", self.artifact)
        process.assert_not_called()
        self.assertIs(execution.status, ExecutionStatus.FAILED)

    def test_timeout_and_child_failure_are_recorded(self):
        for failure in (subprocess.TimeoutExpired("smoke", 5), subprocess.CalledProcessError(1, "smoke")):
            with self.subTest(failure=failure), patch("vxruntime.capability_harvester.subprocess.run", side_effect=failure):
                execution = self.run_smoke()
            self.assertIs(execution.status, ExecutionStatus.FAILED)
            self.assertEqual(self.registry.receipt(execution.execution_id)["execution"]["status"], "failed")

    def test_subprocess_configuration_is_bounded(self):
        expected = {"sha256": self.passport.artifact_sha256, "size": len(self.artifact)}
        with patch("vxruntime.capability_harvester.subprocess.run", return_value=subprocess.CompletedProcess([], 0, json.dumps(expected).encode())) as process:
            self.run_smoke()
        args, kwargs = process.call_args
        self.assertEqual(args[0][1:3], ["-I", "-S"])
        self.assertEqual(kwargs["env"], {})
        self.assertLessEqual(kwargs["timeout"], 30)
        self.assertNotIn("shell", kwargs)
        self.assertEqual(kwargs["input"], self.artifact)

    def test_corrupt_passport_is_rejected(self):
        with self.registry.db:
            self.registry.db.execute("UPDATE passports SET body=replace(body, 'fixture.contract.v1', 'tampered')")
        with self.assertRaisesRegex(ValueError, "PASSPORT_INTEGRITY_FAILURE"):
            self.run_smoke()

    def test_corrupt_receipt_is_rejected(self):
        execution = self.run_smoke()
        with self.registry.db:
            self.registry.db.execute("UPDATE receipts SET body='{}'")
        with self.assertRaisesRegex(ValueError, "RECEIPT_INTEGRITY_FAILURE"):
            self.runner.review(execution, None, trusted_verifiers=frozenset())

    def test_unique_execution_history(self):
        first, second = self.run_smoke(), self.run_smoke()
        self.assertNotEqual(first.execution_id, second.execution_id)
        self.assertTrue(self.runtime.verify())
        self.assertEqual(self.registry.db.execute("SELECT COUNT(*) FROM receipts").fetchone()[0], 2)

    def test_oversize_and_invalid_timeout_rejected(self):
        with self.assertRaisesRegex(ValueError, "ARTIFACT_SIZE"):
            self.runner.run("fixture.hash", "1.0", b"x" * (1024 * 1024 + 1))
        with self.assertRaisesRegex(ValueError, "INVALID_TIMEOUT"):
            self.runner.run("fixture.hash", "1.0", self.artifact, timeout=31)


if __name__ == "__main__":
    unittest.main()
