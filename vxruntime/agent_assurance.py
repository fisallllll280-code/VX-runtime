"""Fail-closed evidence/authority bridge for agent task admissions.

This module does NOT dispatch remote agents, sign permits or deploy workers.
"""
from dataclasses import dataclass
from typing import FrozenSet, Tuple
import hashlib
import json

ROLES = frozenset({"ARCHITECT","IMPLEMENTER","ADVERSARIAL_REVIEWER","INDEPENDENT_VERIFIER","EVOLUTION_JUDGE"})

@dataclass(frozen=True)
class AgentPrincipal:
    principal_id: str
    role: str
    capabilities: FrozenSet[str]

@dataclass(frozen=True)
class TaskGrant:
    task_id: str
    principal_id: str
    capability: str
    source_revision: str
    not_before: int
    expires_at: int
    revoked: bool = False

@dataclass(frozen=True)
class AgentReceipt:
    task_id: str
    producer_id: str
    verifier_id: str
    source_revision: str
    evidence_sha256: str
    tests_passed: bool

def verify_sha256(value: str) -> bool:
    return len(value)==64 and all(c in "0123456789abcdef" for c in value)

def authorize(principal: AgentPrincipal, grant: TaskGrant, now: int, source_revision: str) -> dict:
    if not principal.principal_id or principal.role not in ROLES:
        return {"decision":"HOLD","reason":"UNKNOWN_PRINCIPAL"}
    if grant.revoked or now < grant.not_before or now >= grant.expires_at:
        return {"decision":"HOLD","reason":"GRANT_INACTIVE"}
    if not grant.task_id or not grant.capability or not source_revision:
        return {"decision":"HOLD","reason":"INVALID_TASK_SCOPE"}
    if principal.principal_id != grant.principal_id or grant.capability not in principal.capabilities:
        return {"decision":"REJECT","reason":"AUTHORITY_MISMATCH"}
    if source_revision != grant.source_revision:
        return {"decision":"HOLD","reason":"REVISION_DRIFT"}
    return {"decision":"ELIGIBLE_TO_DISPATCH","reason":"EXTERNAL_RUNTIME_CHECK_REQUIRED"}

def admit(receipt: AgentReceipt, producer: AgentPrincipal, verifier: AgentPrincipal,
          grant: TaskGrant, now: int, *, policy_approved: bool) -> dict:
    auth=authorize(producer,grant,now,receipt.source_revision)
    if auth["decision"]!="ELIGIBLE_TO_DISPATCH":
        return {"decision":"HOLD","reason":"GRANT_OR_SCOPE_INVALID"}
    if not policy_approved or not receipt.tests_passed:
        return {"decision":"HOLD","reason":"POLICY_OR_TESTS_INCOMPLETE"}
    if not receipt.task_id or receipt.task_id != grant.task_id or receipt.producer_id != producer.principal_id:
        return {"decision":"HOLD","reason":"RECEIPT_TASK_MISMATCH"}
    if verifier.role!="INDEPENDENT_VERIFIER" or receipt.verifier_id != verifier.principal_id:
        return {"decision":"HOLD","reason":"UNVERIFIED_PRINCIPAL"}
    if producer.principal_id==verifier.principal_id:
        return {"decision":"REJECT","reason":"SELF_VERIFICATION"}
    if not verify_sha256(receipt.evidence_sha256):
        return {"decision":"HOLD","reason":"EVIDENCE_DIGEST_INVALID"}
    return {"decision":"ELIGIBLE_FOR_GOVERNANCE","reason":"EXTERNAL_EVIDENCE_CHECK_REQUIRED"}
