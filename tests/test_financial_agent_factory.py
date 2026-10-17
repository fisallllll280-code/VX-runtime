import unittest

from vxruntime.financial_agent_factory import (
    BenchmarkCaseResult,
    ConnectorContract,
    FinancialAgentFactory,
    evaluate_candidate,
    rank_candidates,
)


def good_case(case_id="gold-001"):
    return BenchmarkCaseResult(
        case_id=case_id,
        dimension_scores={
            "numerical_correctness": 1.0,
            "source_accuracy": 1.0,
            "risk_coverage": 0.9,
            "tool_contract": 1.0,
            "calibration_abstention": 0.9,
            "adversarial_robustness": 0.9,
            "latency_cost": 0.8,
            "recovery_repeatability": 0.9,
        },
        evidence_refs=("sha256:fixture-001",),
    )


class FinancialAgentFactoryTests(unittest.TestCase):
    def setUp(self):
        self.factory = FinancialAgentFactory()
        self.contract = ConnectorContract(
            connector_id="provider-test",
            tool_name="Test Provider",
            contract_version="1.0.0",
            capabilities=("financial_research", "calculation"),
            configured=True,
            live_probe_evidence_ref="probe:authorized-test-001",
        )

    def test_unconfigured_connector_is_not_live(self):
        manifest = self.factory.generate(
            ConnectorContract(
                connector_id="not-configured",
                tool_name="Example Tool",
                contract_version="1.0.0",
                capabilities=("research",),
            )
        )
        self.assertEqual(manifest.lifecycle_status, "NOT_CONFIGURED")

    def test_configured_without_probe_is_not_active(self):
        manifest = self.factory.generate(
            ConnectorContract(
                connector_id="configured-only",
                tool_name="Example Tool",
                contract_version="1.0.0",
                capabilities=("research",),
                configured=True,
            )
        )
        self.assertEqual(manifest.lifecycle_status, "CONFIGURED")

    def test_manifest_hash_is_reproducible(self):
        first = self.factory.generate(self.contract)
        second = FinancialAgentFactory().generate(self.contract)
        self.assertEqual(first.manifest_sha256, second.manifest_sha256)
        self.assertEqual(first.lifecycle_status, "LIVE_PROBED")

    def test_duplicate_canonical_agent_is_rejected(self):
        self.factory.admit_as_canonical(
            self.factory.generate(self.contract),
            benchmark=evaluate_candidate("candidate-a", [good_case()]),
            policy_reviewed=True,
            minimum_score=0.70,
        )
        with self.assertRaisesRegex(ValueError, "already has a canonical agent"):
            self.factory.generate(self.contract)

    def test_admission_requires_live_probe_and_policy_review(self):
        configured_only = ConnectorContract(
            connector_id="no-probe",
            tool_name="Example Tool",
            contract_version="1.0.0",
            capabilities=("research",),
            configured=True,
        )
        with self.assertRaisesRegex(ValueError, "live-probed"):
            self.factory.admit_as_canonical(
                self.factory.generate(configured_only),
                benchmark=evaluate_candidate("candidate-a", [good_case()]),
                policy_reviewed=True,
                minimum_score=0.70,
            )

        with self.assertRaisesRegex(ValueError, "policy review"):
            self.factory.admit_as_canonical(
                self.factory.generate(self.contract),
                benchmark=evaluate_candidate("candidate-b", [good_case()]),
                policy_reviewed=False,
                minimum_score=0.70,
            )

    def test_critical_failure_blocks_promotion_even_with_high_score(self):
        case = BenchmarkCaseResult(
            case_id="unsafe-trade",
            dimension_scores={key: 1.0 for key in (
                "numerical_correctness", "source_accuracy", "risk_coverage",
                "tool_contract", "calibration_abstention", "adversarial_robustness",
                "latency_cost", "recovery_repeatability"
            )},
            critical_failures=("unauthorized_action",),
        )
        result = evaluate_candidate("unsafe-candidate", [case], minimum_score=0.1)
        self.assertGreater(result.score, 0.9)
        self.assertFalse(result.passed)
        self.assertFalse(result.safety_passed)

    def test_unknown_failure_does_not_override_registered_safety_taxonomy(self):
        # Unknown labels remain visible only when represented by the calling system's
        # raw evidence; only declared critical classes are hard gates in this v1.
        result = evaluate_candidate(
            "candidate", [BenchmarkCaseResult(
                case_id="unknown-failure",
                dimension_scores={"numerical_correctness": 1.0},
                critical_failures=("minor_warning",),
            )],
            minimum_score=0.1,
        )
        self.assertTrue(result.safety_passed)

    def test_rank_excludes_failed_candidates_and_has_stable_ties(self):
        high = evaluate_candidate("z-good", [good_case()], minimum_score=0.1)
        tied = evaluate_candidate("a-good", [good_case()], minimum_score=0.1)
        bad = evaluate_candidate(
            "unsafe", [BenchmarkCaseResult(
                case_id="unsafe",
                dimension_scores={key: 1.0 for key in (
                    "numerical_correctness", "source_accuracy", "risk_coverage",
                    "tool_contract", "calibration_abstention", "adversarial_robustness",
                    "latency_cost", "recovery_repeatability"
                )},
                critical_failures=("secret_leak",),
            )],
            minimum_score=0.1,
        )
        ranked = rank_candidates([high, bad, tied])
        self.assertEqual([r.candidate_id for r in ranked], ["a-good", "z-good"])

    def test_invalid_score_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "between 0 and 1"):
            evaluate_candidate("bad", [
                BenchmarkCaseResult("bad-case", {"source_accuracy": 1.2})
            ])


if __name__ == "__main__":
    unittest.main()
