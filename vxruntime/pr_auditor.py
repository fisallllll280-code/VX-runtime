"""Read-only PR evidence auditor: pure data evaluation; never calls GitHub."""
from __future__ import annotations
from dataclasses import dataclass
from typing import Mapping, Any

@dataclass(frozen=True)
class AuditVerdict:
    verdict: str
    reasons: tuple[str, ...]
    evidence: tuple[str, ...]


def audit_pr(snapshot: Mapping[str, Any]) -> AuditVerdict:
    """Fail closed. Sources are supplied snapshots, not live GitHub evidence."""
    if not isinstance(snapshot, Mapping):
        raise ValueError("SNAPSHOT_MAPPING_REQUIRED")
    reasons = []
    evidence = []
    if not snapshot.get("repo") or not snapshot.get("head_sha"):
        reasons.append("IDENTITY_OR_COMMIT_MISSING")
    if snapshot.get("protected_files_changed"):
        reasons.append("PROTECTED_FILE_CHANGE")
    if snapshot.get("merge_requested"):
        reasons.append("MERGE_REQUIRES_HUMAN_APPROVAL")
    checks = snapshot.get("checks")
    if not isinstance(checks, list) or not checks:
        reasons.append("CHECKS_MISSING")
    else:
        for check in checks:
            if not isinstance(check, Mapping) or not check.get("name") or not check.get("url"):
                reasons.append("CHECK_PROVENANCE_MISSING")
                continue
            evidence.append(str(check["url"]))
            if check.get("conclusion") not in {"success", "failure", "cancelled", "skipped"}:
                reasons.append("CHECK_INCOMPLETE")
            elif check.get("conclusion") != "success":
                reasons.append("CHECK_NOT_SUCCESS")
    if not snapshot.get("independent_review"):
        reasons.append("INDEPENDENT_REVIEW_MISSING")
    if not snapshot.get("source_access_confirmed"):
        reasons.append("SOURCE_ACCESS_NOT_CONFIRMED")
    verdict = "BLOCK" if any(reason in reasons for reason in
                            ("PROTECTED_FILE_CHANGE","CHECK_NOT_SUCCESS")) else "HOLD" if reasons else "PASS"
    # PASS is advisory only; the gate never merges or declares the system VERIFIED.
    return AuditVerdict(verdict, tuple(dict.fromkeys(reasons)), tuple(evidence))
