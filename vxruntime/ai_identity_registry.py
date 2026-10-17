"""Identity gate for AI agents entering the VX challenge.

This module records declared identity; it does not cryptographically prove that
a provider/model is who it claims to be. Verification evidence is a separate
admission requirement.
"""
from __future__ import annotations

from dataclasses import dataclass, asdict
from datetime import datetime, timezone
import hashlib
import json
import re
from typing import Any


_REQUIRED = ("ai_name", "company_name", "agent_name", "identity_source")


@dataclass(frozen=True)
class AIIdentity:
    ai_name: str
    company_name: str
    agent_name: str
    identity_source: str
    model_or_product: str = ""
    official_url: str = ""
    verification_evidence_id: str = ""
    declared_at_utc: str = ""

    def normalized(self) -> "AIIdentity":
        values = {k: str(getattr(self, k)).strip() for k in asdict(self)}
        values["declared_at_utc"] = values["declared_at_utc"] or datetime.now(timezone.utc).isoformat()
        return AIIdentity(**values)


@dataclass(frozen=True)
class IdentityAdmission:
    admitted_to_lobby: bool
    identity_status: str
    identity: dict[str, str]
    identity_hash: str
    blockers: tuple[str, ...]


def admit_identity(identity: AIIdentity) -> IdentityAdmission:
    """Allow entry to the lobby only with a complete declared identity.

    A complete declaration is NOT equivalent to verified corporate identity.
    The agent must not be labelled VERIFIED without external evidence.
    """
    normalized = identity.normalized()
    values = asdict(normalized)
    blockers = [f"MISSING_{name.upper()}" for name in _REQUIRED if not values[name]]
    if values["official_url"] and not re.match(r"^https://", values["official_url"], re.I):
        blockers.append("OFFICIAL_URL_MUST_USE_HTTPS")
    canonical = json.dumps(values, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    digest = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
    complete = not blockers
    # This declaration helper cannot independently validate evidence. Never
    # emit VERIFIED here; a separate trusted verifier must make that transition.
    status = "DECLARED_PENDING_VERIFICATION" if complete else "INCOMPLETE"
    if complete and not normalized.verification_evidence_id:
        blockers.append("VERIFICATION_EVIDENCE_REQUIRED_FOR_VERIFIED_STATUS")
    elif complete:
        blockers.append("EVIDENCE_ID_PRESENT_BUT_NOT_INDEPENDENTLY_VALIDATED")
    return IdentityAdmission(
        admitted_to_lobby=complete,
        identity_status=status,
        identity=values,
        identity_hash=digest,
        blockers=tuple(blockers),
    )


def identity_public_card(admission: IdentityAdmission) -> dict[str, Any]:
    """Public-facing card; never hides a pending-verification status."""
    identity = admission.identity
    return {
        "ai_name": identity["ai_name"],
        "company_name": identity["company_name"],
        "model_or_product": identity["model_or_product"],
        "agent_name": identity["agent_name"],
        "identity_status": admission.identity_status,
        "identity_hash": admission.identity_hash,
        "verification_evidence_id": identity["verification_evidence_id"] or None,
    }
