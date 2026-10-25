# Capability Harvester v1

Status: reference implementation; integration `PENDING SOURCE VALIDATION`.

## Source inspection

Inspected the canonical `fisallllll280-code/VAIXLNS` at
`433969a43b604563e22b70b8cb88223aff539fad` and `fisallllll280-code/VX-runtime`
at `97fc6574f637984818841248ebe6b10dc36f6308` through the connected GitHub
adapter. Their recursive source inventories contain no AGENTS.md.

VAIXLNS README identifies it as the canonical project hub. Its typed federation
contract (`registry/federation/federation_contract_edges.v1.json`) requires
declared adapters, explicit execution grants and evidence; VX execution and
evidence edges are disabled and `SPECIFIED_NOT_CONNECTED`. They stay disabled.
VX already implements `VXRuntime`, `EventLedger`, `ExecutionPolicy` and
`evaluate_admission`; this implementation reuses those boundaries. Its README
claim that only a specification exists is stale relative to the source and
repository contract. No canonical files, `project.genome` or `Ω.000` are edited.

## Implemented boundary

`vxruntime/capability_harvester.py` adds:

- A derived SQLite inventory of immutable capability/version passports, source
  revisions, artifact SHA-256, licenses, contracts, requested permissions and
  dependency relationships. Re-registering identical data is idempotent;
  replacing an existing version with different metadata is rejected.
- A host-supplied compatibility policy with explicit license/permission lists
  and a revision. Missing fields, floating source revisions, denied licenses
  and denied permissions block inventory registration. Current policy is
  rechecked before smoke execution. Risk is classified in the receipt.
- A fixed inert-artifact smoke test via the existing VX execution policy and
  event ledger. Receipts persist execution inputs/results, source revision,
  observation time, policy revision, passport fingerprint and ledger events.
  Each receipt has a digest; failed/blocked executions remain failed/blocked.
- Local eligibility review through the existing independent-verifier admission
  gate. Proofs must also bind to the passport source revision and exact receipt
  digest under `evidence_hashes.capability_smoke`. No proof means HOLD after a
  successful execution. This API never grants canonical adoption.

The database is a local projection suitable for later Nexus ingestion, not a
second authoritative execution history. Hashes detect accidental changes and
bind reviewed bytes; they are not signatures or protection against a database
administrator rewriting both data and hashes. Source URL/revision declarations
are syntax-checked, not remote provenance verification. Dependency links require
inventory entries but do not imply compatibility or independent verification.

## Reproducible example

```python
import hashlib
from vxruntime.core import ExecutionPolicy, VXRuntime
from vxruntime.capability_harvester import (
    CapabilityPassport, CapabilityRegistry, CompatibilityPolicy, EvidenceRunner, SMOKE,
)

artifact = b"inert sample"
policy = CompatibilityPolicy("reviewed-policy-v1", frozenset({"MIT"}))
registry = CapabilityRegistry("capabilities.sqlite")
try:
    passport = CapabilityPassport(
        "sample.artifact", "1", "MIT", "https://example.com/sample",
        "a" * 40, hashlib.sha256(artifact).hexdigest(), "sample.contract.v1",
    )
    registry.register(passport, policy)
    # Local fixture authorization only. Production grants belong to VAIXLNS.
    runtime = VXRuntime(policy=ExecutionPolicy(allowed_capabilities=frozenset({SMOKE})))
    runner = EvidenceRunner(registry, runtime, policy)
    execution = runner.run("sample.artifact", "1", artifact)
    print(registry.receipt(execution.execution_id))
    print(runner.review(execution, None, trusted_verifiers=frozenset()).status)
finally:
    registry.close()
```

The sample uses synthetic metadata and demonstrates no verified external source.

## Isolation and acceptance limits

The child runs only fixed trusted hashing code with `python -I -S`, an empty
environment, a temporary working directory, at most 1 MiB input and a 1–30 second
timeout (positive fractional timeouts also supported). It does not import,
install or execute submitted artifact code. Process separation is not an OS
sandbox; arbitrary library smoke tests require a future sandbox adapter with
filesystem, network and resource enforcement. No runtime claim for Nexus,
NEXENT, Multi-Mind, VV, OIF or Ω Evidence services is made. Receipts are exportable
local evidence, not proof of a connected Ω Evidence store.

The next integration gates are authenticated VAIXLNS grants, source and license
verification, independently reviewed contract/security tests, dependency/runtime
compatibility matrices, Nexus ingestion and an authorized canonical promotion
receipt. Research, simulation and innovation engines remain future work.

## Validation

```bash
python -m unittest discover -s tests -p test_capability_harvester.py -v
python -m compileall -q vxruntime tests
python -m pytest -q
```

The focused tests require only the Python standard library. The full existing
suite requires pytest. CI runs both and uploads the focused evidence log; a
successful CI run is evidence for this reference implementation only.
