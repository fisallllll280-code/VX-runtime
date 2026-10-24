"""VX release preflight: deterministic HOLD unless independent evidence recorded."""
import json
from pathlib import Path

REQUIRED = ("ci_exact_head","agent_builder_http","mobile_http","security_authentication",
            "csrf_protection","persistent_storage","tls_delivery","iphone_device",
            "operator_release_approval")
FILE = Path(__file__).resolve().parents[1] / "release" / "vx_app_preview_001.json"

def assess(record):
    checks = record.get("checks") if isinstance(record, dict) else None
    policy = record.get("policy") if isinstance(record, dict) else None
    errors = []
    if not isinstance(checks, dict) or set(checks) != set(REQUIRED):
        errors.append("MISSING_OR_EXTRA_CHECKS")
    elif any(checks[k] != "VERIFIED" for k in REQUIRED):
        errors.append("UNVERIFIED_GATE")
    if not isinstance(policy, dict) or type(policy.get("external_spend_sar")) is not int or policy["external_spend_sar"] != 0:
        errors.append("SPEND_POLICY")
    if isinstance(policy, dict) and (policy.get("public_deployment") is not False or policy.get("merge_to_main") is not False):
        errors.append("UNAPPROVED_DEPLOYMENT")
    if isinstance(policy, dict) and policy.get("protected_files_unchanged") is not True:
        errors.append("PROTECTED_FILES")
    if record.get("release_state") != "HOLD_NOT_PUBLISHED":
        errors.append("RELEASE_STATE_TAMPERED")
    # This preflight never deploys; verified fields are not self-authenticating.
    return {"decision": "HOLD", "blocking_reasons": errors,
            "evidence_verified_by_independent_authority": False,
            "deployment_performed": False}

if __name__ == "__main__":
    print(json.dumps(assess(json.loads(FILE.read_text(encoding="utf-8"))),sort_keys=True))
