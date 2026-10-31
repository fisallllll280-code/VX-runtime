"""VX Engineering Depth Compiler: source-aware, non-executing architecture review.

This is a deterministic gap compiler, not a system-design LLM or a verifier.
It never writes canonical registries or triggers tools, deployment, or agents.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

DIMENSIONS = (
    "identity", "provenance", "purpose", "contracts", "invariants",
    "threat_model", "failure_modes", "tests", "evidence", "replay",
    "simulation", "verification", "authorization", "rollback",
)
SUGGESTIONS = {
    "identity": "Bind a stable capability ID and canonical owner.",
    "provenance": "Pin source repository, revision and content hashes.",
    "purpose": "Specify the problem, scope and measurable acceptance target.",
    "contracts": "Define typed inputs, outputs, side effects and interfaces.",
    "invariants": "State machine-checkable safety and integrity constraints.",
    "threat_model": "Model privilege boundaries, injections and abuse cases.",
    "failure_modes": "Specify timeouts, loss, drift and failure isolation.",
    "tests": "Add positive, negative and regression fixtures.",
    "evidence": "Bind receipts to source revision and independent observations.",
    "replay": "Describe deterministic replay and nondeterministic external effects.",
    "simulation": "Compare baseline and counterfactual models with error bounds.",
    "verification": "Require verifier independence and falsification criteria.",
    "authorization": "Identify approver and explicit authorization scope.",
    "rollback": "Define restore checkpoint and irreversible effect handling.",
}
# Candidate groups from the supplied SEF deep-architecture research, not operational claims.
REALMS = (
    "perception", "reasoning", "action", "memory", "adaptation",
    "governance", "simulation", "collaboration",
)
EVOLUTION_ENGINES = (
    "textual_feedback", "mutation_selection", "composite_loss",
    "strategy_compilation", "structural_refactoring",
)


def canonical_digest(value: object) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False,
                                     separators=(",", ":")).encode("utf-8")).hexdigest()


def compile_depth(spec: dict) -> dict:
    if not isinstance(spec, dict) or not isinstance(spec.get("capability_id"), str) or not spec["capability_id"].strip():
        raise ValueError("capability_id must be a nonempty string")
    if not isinstance(spec.get("source"), dict):
        raise ValueError("source must identify its repository and revision")
    source = spec["source"]
    if not all(isinstance(source.get(k), str) and source[k].strip() for k in ("repository", "revision")):
        raise ValueError("source requires repository and pinned revision")
    supplied = spec.get("assurances", {})
    if not isinstance(supplied, dict):
        raise ValueError("assurances must be an object")
    if any(k not in DIMENSIONS for k in supplied):
        raise ValueError("unknown assurance dimension")
    # This is completeness of *declarations*, NOT evidence of correctness.
    present = sorted(k for k in DIMENSIONS if isinstance(supplied.get(k), dict)
                     and bool(supplied[k].get("reference")))
    missing = [k for k in DIMENSIONS if k not in present]
    proposals = [{"dimension": k, "suggestion": SUGGESTIONS[k],
                  "state": "PROPOSED", "evidence": None} for k in missing]
    claimed = spec.get("claimed_realms", [])
    if not isinstance(claimed, list) or any(not isinstance(x, str) or x not in REALMS for x in claimed):
        raise ValueError("claimed_realms must be known names")
    engines = spec.get("claimed_evolution_engines", [])
    if not isinstance(engines, list) or any(not isinstance(x, str) or x not in EVOLUTION_ENGINES for x in engines):
        raise ValueError("claimed_evolution_engines must be known names")
    return {
        "schema": "vx.engineering.depth.v1",
        "capability_id": spec["capability_id"],
        "source": source,
        "source_spec_hash": canonical_digest(spec),
        "review_state": "REQUIRES_INDEPENDENT_VERIFICATION",
        "declaration_coverage": {"declared": len(present), "total": len(DIMENSIONS),
                                 "dimensions": present},
        "missing": missing,
        "engineering_proposals": proposals,
        "claimed_realms": sorted(set(claimed)),
        "claimed_evolution_engines": sorted(set(engines)),
        "execution_authorized": False,
        "canonical_promotion_authorized": False,
        "novelty_verified": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("input", type=Path)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    # Caller controls paths. This command only reads one JSON spec and writes its analysis output.
    spec = json.loads(args.input.read_text(encoding="utf-8"))
    report = compile_depth(spec)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, ensure_ascii=False, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
