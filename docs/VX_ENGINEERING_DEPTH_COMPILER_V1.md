# VX Engineering Depth Compiler v1

**State:** bounded implementation + tests on an isolated branch. Not deployed, self-improving, a platform clone, or independently verified for real-world performance.

## Purpose
Unlike copying an existing platform, this tool examines a *specified capability* for architectural depth: provenance, contracts, invariants, adversarial threats, failure, tests, evidence, replay, simulation, independent verification, authorization and rollback. It produces a deterministic, reviewable **design-gap report**, not new production code or autonomous edits.

## Engineering flow
Source claim -> typed capability spec -> 14-dimension completeness evaluation -> missing obligations -> PROPOSED engineering improvements -> independent design/proof review -> separately authorized VX execution.

The user-supplied deep architecture paper proposes eight intelligence realms and five evolution engines. These are **candidate classification tags** in this compiler, not evidence that microkernels, TEEs, Merkle DAGs, multi-agent networks or auto-refactoring exist or are enabled.

## Input example
```json
{
  "capability_id": "VAIXLNS.XV.RESEARCH.001",
  "source": {"repository": "VAIXLNS", "revision": "PINNED_COMMIT_SHA"},
  "claimed_realms": ["reasoning", "simulation"],
  "claimed_evolution_engines": ["strategy_compilation"],
  "assurances": {
    "purpose": {"reference": "docs/research/spec.md#mission"},
    "authorization": {"reference": "docs/policy.md#authority"}
  }
}
```

## Commands
```sh
python -m pytest -q tests/test_vx_engineering_depth_compiler.py
python -m tools.vx_engineering_depth_compiler input.json --out build/depth/review.json
```

## Boundaries
- A reference is a claim to inspect, not proof. `declaration_coverage` is NOT a security or readiness score.
- No model API calls, filesystem scanning, external fetch, secret access, actual self-modification or canonical promotion.
- All outputs are PROPOSED and require falsifiable tests, source review, threat-model assessment and sovereign authorization.
- Existing VAIXLNS index builders, ARC-X, VV, VCRE, NEXENT and VX stay separate; integration is by verified contracts.
- Do not alter `project.genome` or `Ω.000`; no main merges or publication without approval.
