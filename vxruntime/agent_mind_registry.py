"""Fail-closed VX agent-to-mind bindings; no model or runtime activation."""
from __future__ import annotations
from dataclasses import dataclass
from hashlib import sha256
import json

DENIED = frozenset({"TRADE", "TRANSFER_FUNDS", "PURCHASE", "PUBLISH", "MERGE", "DELETE", "SIGN_CONTRACT"})
KINDS = frozenset({"RESEARCH", "ENGINEERING", "MATHEMATICS", "SIMULATION", "VERIFY", "FINANCIAL", "DATA", "SECURITY"})

@dataclass(frozen=True)
class VXMind:
    mind_id: str
    domain: str
    model_connector_id: str | None = None
    live_probe_evidence_ref: str | None = None

@dataclass(frozen=True)
class VXAgent:
    agent_id: str
    mind_id: str
    capabilities: tuple[str, ...]
    allowed_operations: tuple[str, ...] = ("OBSERVE", "RESEARCH", "CALCULATE", "PROPOSE")
    evidence_refs: tuple[str, ...] = ()
    approval_ref: str | None = None

def assess(agent: VXAgent, mind: VXMind) -> dict:
    errors = []
    if not agent.agent_id.strip() or not mind.mind_id.strip() or agent.mind_id != mind.mind_id:
        errors.append("MIND_BINDING_INVALID")
    if mind.domain not in KINDS:
        errors.append("DOMAIN_UNKNOWN")
    if not agent.capabilities or any(not c.strip() for c in agent.capabilities):
        errors.append("CAPABILITIES_INVALID")
    if set(agent.allowed_operations) & DENIED:
        errors.append("FORBIDDEN_OPERATION")
    if not mind.model_connector_id or not mind.live_probe_evidence_ref:
        errors.append("NO_VERIFIED_LIVE_CONNECTOR")
    if not agent.evidence_refs:
        errors.append("EVIDENCE_MISSING")
    if not agent.approval_ref:
        errors.append("APPROVAL_MISSING")
    payload = {
        "agent_id": agent.agent_id, "mind_id": mind.mind_id,
        "domain": mind.domain, "connector_id": mind.model_connector_id,
        "capabilities": sorted(set(agent.capabilities)),
        "allowed_operations": sorted(set(agent.allowed_operations)),
        "evidence_refs": sorted(set(agent.evidence_refs)),
        "approval_ref": agent.approval_ref,
        "live_probe_evidence_ref": mind.live_probe_evidence_ref,
    }
    digest = sha256(json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
    return {"decision": "HOLD" if errors else "ELIGIBLE_FOR_INDEPENDENT_VERIFICATION",
            "reasons": sorted(set(errors)), "manifest_sha256": digest, "execution_enabled": False}
