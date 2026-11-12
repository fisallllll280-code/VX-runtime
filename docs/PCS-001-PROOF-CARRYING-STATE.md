# PCS-001 — Proof-Carrying State

Status: implementation proposal on a feature branch; not canonical until reviewed and admitted.

## Purpose

PCS-001 prevents a candidate state from being represented as canonical unless its state identity, provenance, proof bundle, assurance report, replay evidence, verification references, promotion decision, and transition receipt satisfy the admission contract.

## Separation of concerns

- `CandidateState` contains state content, schema version, and provenance. Its `state_cid` is derived from those fields.
- `AssuranceReport` carries evidence references and verification/replay outcomes. It does not authorize promotion.
- `PromotionDecision` records the external authority decision. It cannot manufacture proof or verification evidence.
- `PromotionReceipt` records the transition and links pre/post state, assurance, guards, evidence, replay, verifiers, and authority references.
- `CanonicalState` is returned only after the local admission guards pass.

## Admission invariants

1. Candidate, assurance report, and transition receipt must reference the same state identity.
2. Assurance lifecycle state must be `VERIFIED`; assurance level is a separate dimension.
3. A proof bundle, provenance, verification references, and replayability are required.
4. Counterexamples block admission.
5. Promotion must be explicitly `APPROVED`; decision and authority references remain separate from state identity.
6. Transition guards must all be `PASS`, with evidence hashes, replay hashes, and verifier references.
7. Report and receipt references must match their content digests.

## Trust boundary

The current implementation validates local structure and cross-reference consistency only. It does **not** cryptographically authenticate external references, validate signatures/quorums, provide durable storage, or implement Ω-RAC. Those functions require trusted adapters and their own executable evidence.

## Runtime integration

PCS admission is downstream of execution evidence and replay verification. VX Runtime remains responsible for governed execution and ledger records; VAIXLNS federation authority remains responsible for governed canonical admission. A successful worker result alone never makes a state canonical.

## Verification

Run `python -m compileall -q vxruntime tests` and `python -m pytest -q`. The PCS tests exercise successful admission and rejection of unverified, proof-less, pending, and mismatched state transitions. CI results must be checked on the pull request before this proposal is described as tested.
