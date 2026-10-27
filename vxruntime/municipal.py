"""Local readiness profile derived from MOMAH's sandbox application form.

Not a Balady API, permit validator, eligibility decision, or submission client.
Only presence facts cross this boundary; source documents stay with their owner.
"""
from __future__ import annotations

from dataclasses import dataclass

CAPABILITY = "municipal.sandbox.check_readiness.v1"
AGENT = "VX-MUNICIPAL-VALIDATOR"
PROFILE = "momah-sandbox-local-readiness/1"
SOURCE = "https://momah.gov.sa/ar/form/sandbox-application-form"
# A deliberately selected LOCAL readiness subset, not official mandatory fields.
CHECKS = (
    "solution_description", "problem_statement", "readiness_description",
    "target_sector", "experiment_objectives", "measurable_kpis",
    "experiment_scope", "test_timeline", "risk_mitigation",
    "technical_requirements", "data_requirements_review",
    "integration_requirements_review", "regulatory_requirements_review",
    "scaling_plan",
)
PURPOSE = "municipal_sandbox_readiness"


class BoundaryError(ValueError):
    """Contains a fixed reason code only, never an input value or field name."""


@dataclass(frozen=True)
class DataPolicy:
    """Trusted-host configuration, not supplied or changed by task payloads.

    Engineering controls supporting minimisation/purpose limitation. This is
    not a legal-basis determination or a PDPL compliance certification.
    """
    purpose: str = PURPOSE
    notice_reviewed: bool = False
    processing_basis_reviewed: bool = False
    retention_seconds: int = 3600

    def validate(self) -> None:
        if self.purpose != PURPOSE:
            raise BoundaryError("PURPOSE_DENIED")
        if self.notice_reviewed is not True or self.processing_basis_reviewed is not True:
            raise BoundaryError("DATA_REVIEW_REQUIRED")
        if type(self.retention_seconds) is not int or not 1 <= self.retention_seconds <= 86400:
            raise BoundaryError("RETENTION_DENIED")


def validate_facts(facts: object) -> dict[str, bool]:
    # No arbitrary string fields, attachments, applicant IDs or custom keys.
    if type(facts) is not dict or len(facts) > len(CHECKS):
        raise BoundaryError("FACT_SCHEMA_DENIED")
    if any(type(k) is not str or k not in CHECKS or type(v) is not bool
           for k, v in facts.items()):
        raise BoundaryError("FACT_SCHEMA_DENIED")
    return {key: facts.get(key, False) for key in CHECKS}


def check_readiness(facts: dict[str, bool]) -> dict:
    normal = validate_facts(facts)
    missing = [key for key in CHECKS if not normal[key]]
    return {
        "profile": PROFILE,
        "status": "READY_FOR_REVIEW" if not missing else "INCOMPLETE",
        "missing": missing,
        "satisfied": len(CHECKS) - len(missing),
        "total": len(CHECKS),
        "official_eligibility": "NOT_EVALUATED",
        "submission": "NOT_SENT",
    }
