"""VX Brain: proof-first decision composition across existing specialist modules.

No model calls, payments, trades, autonomous writes, or untrusted code execution.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping, Any
from .core import VXRuntime, ExecutionPolicy, ExecutionStatus, digest
from .memory import MemoryVault
from .knowledge_graph import KnowledgeGraph
from .pr_auditor import audit_pr

DOMAINS = frozenset({"engineering", "research", "finance", "knowledge", "operations"})
FINANCIAL_FORBIDDEN = frozenset({"trade", "place_order", "transfer", "withdraw", "buy", "sell"})
REQUIRED = ("mission_id", "domain", "goal", "source_ref", "source_version")


@dataclass(frozen=True)
class BrainDecision:
    mission_id: str
    status: str
    rationale: tuple[str, ...]
    evidence_hash: str | None
    memory_id: int | None


class VXBrain:
    """Deterministic local advisory brain. Does not admit claims to canonical Ω."""
    def __init__(self, db_path):
        self.memory = MemoryVault(db_path)
        self.graph = KnowledgeGraph(str(db_path) + ".graph")
        self.runtime = VXRuntime(policy=ExecutionPolicy(
            allowed_capabilities=frozenset({"vx.brain.evaluate"})))

    def evaluate(self, mission: Mapping[str, Any]) -> BrainDecision:
        if not isinstance(mission, Mapping):
            raise ValueError("MISSION_MAPPING_REQUIRED")
        if any(not isinstance(mission.get(k), str) or not mission[k].strip()
               for k in REQUIRED):
            raise ValueError("MISSION_IDENTITY_AND_PROVENANCE_REQUIRED")
        mission_id, domain = mission["mission_id"], mission["domain"]
        if domain not in DOMAINS:
            raise ValueError("UNKNOWN_DOMAIN")
        action = str(mission.get("action", "analyze")).lower()
        if domain == "finance" and action in FINANCIAL_FORBIDDEN:
            return BrainDecision(mission_id, "BLOCK", ("LIVE_FINANCIAL_ACTION_FORBIDDEN",), None, None)
        if mission.get("external_effect") or mission.get("spend_sar", 0) != 0:
            return BrainDecision(mission_id, "BLOCK", ("EXTERNAL_EFFECT_OR_SPEND_DENIED",), None, None)
        existing = [r for r in self.memory.recall("vx-brain", "mission")
                    if r["body"].get("mission_id") == mission_id]
        if existing:
            return BrainDecision(mission_id, "HOLD", ("MISSION_ALREADY_RECORDED",),
                                 existing[0]["hash"], existing[0]["id"])
        reasons = []
        if not mission.get("evidence_refs"):
            reasons.append("INDEPENDENT_EVIDENCE_PENDING")
        if domain == "finance" and not mission.get("simulation_only", False):
            reasons.append("FINANCE_SIMULATION_FLAG_REQUIRED")
        pr_snapshot = mission.get("pr_snapshot")
        if pr_snapshot is not None:
            verdict = audit_pr(pr_snapshot)
            if verdict.verdict != "PASS":
                reasons.append("PR_AUDIT_" + verdict.verdict)
                reasons.extend(verdict.reasons)
        status = "HOLD" if reasons else "PROPOSED"
        inputs = {"mission": dict(mission), "decision": status, "reasons": reasons}
        execution = self.runtime.execute(mission_id, "vx.brain.evaluate", inputs,
            lambda p: {"status": p["decision"], "reasons": p["reasons"],
                       "fingerprint": digest(p["mission"])})
        if execution.status is not ExecutionStatus.SUCCESS:
            return BrainDecision(mission_id, "BLOCK", ("VX_EXECUTION_FAILED",), None, None)
        record = self.memory.remember("vx-brain", "mission",
            {"mission_id": mission_id, "status": status, "reasons": reasons,
             "input_hash": execution.input_hash, "output_hash": execution.output_hash},
            mission["source_ref"], mission["source_version"])
        self.graph.add_node("vx-brain", "mission", mission_id,
                            mission["source_version"], {"status": status,
                            "receipt_hash": execution.event_hash})
        return BrainDecision(mission_id, status, tuple(reasons),
                             execution.event_hash, record["id"])

    def verify_local(self):
        return self.runtime.verify() and self.memory.integrity_check() and self.graph.verify()

    def close(self):
        self.graph.close()
        self.memory.close()
