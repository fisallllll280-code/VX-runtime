# VX Brain sovereign decision composer v0.1

**State:** branch implementation; CI must be independently checked. Local advisory only. Not an LLM, not production or financially autonomous.

## Reused interfaces

- `VXRuntime`: capability control, bounded execution, event hash and replay substrate.
- `MemoryVault`: durable per-tool mission receipts and duplicate suppression.
- `KnowledgeGraph`: derived source-versioned knowledge nodes.
- `audit_pr`: independent advisory PR evidence check.

`VXBrain.evaluate` accepts one mission with `mission_id`, `domain`, `goal`, `source_ref`, `source_version`, optional `evidence_refs`, `pr_snapshot`, `simulation_only`, `action`, `spend_sar` and `external_effect`. Returns HOLD, BLOCK or PROPOSED (never VERIFIED). It never fetches sources or calls models. User-supplied evidence references are **not validated evidence**; PROPOSED means only locally recorded candidate.

Domains: engineering, research, finance, knowledge, operations. Finance permits only offline analytical/simulation paths: no transfer, market order, buy or sell action. Explicit no-external-effects and zero-spend guard. No promotion to Ω registry.

## Required follow-on gates (not implemented)

- Globally atomic mission identity across workers, secure auth and network boundaries.
- Multi-brain delegation with separate verifier, reproducible simulations, threat modeling and ACLs.
- Research source validators, tool adapters, license and privacy checks; prevent prompt injection.
- Financial backtesting data provenance, slippage, fees, capital guardrails and independent risk reviewer.
- Memory backups/restores and Ω cross-repository reconciliation.
- VV backend with scoped credentials; real inference via separately approved provider account.

Run tests with `python -m pytest -q tests/test_brain.py`. No changes to protected files, no main merge, no publication.
