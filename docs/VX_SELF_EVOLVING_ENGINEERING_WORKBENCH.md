# VX Self-Evolving Engineering Workbench

Status: PROPOSAL — architecture contract only; not an implementation claim.
Scope: VX Runtime. This document does not modify or redefine VAIXLNS canonical sources, `project.genome`, or `Ω.000`.

## Mission

VX is intended to become a governed engineering workbench that can research, design, build, inspect, test, integrate, and improve software through its own explicitly declared languages and capability contracts. It is not an unrestricted autonomous agent and does not treat generated code or model output as proof.

## Product surfaces

1. **Command Center** — current runtime health, active jobs, policy denials, evidence status, and recent transitions.
2. **My Workspace** — user-configured projects, pinned tools, preferred workflows, language/toolchain profiles, and saved views.
3. **Projects & Artifacts** — source trees, generated applications, dependency graphs, builds, test runs, packages, and provenance.
4. **Agents & Tasks** — registered agents, capabilities, mailbox/task state, budgets, cancellation, and per-task evidence.
5. **Model Bridge** — provider adapters for OpenAI, Anthropic/Claude, Google/Gemini, xAI/Grok, Mistral, and local models where configured. Each adapter must be explicitly configured and health-tested; provider names alone do not imply connectivity.
6. **Program Inspector** — static analysis, dependency/SBOM inventory, format detection, source and symbol inspection, and safe sandboxed execution when permitted. Decompilation is only attempted where technically feasible and legally authorized; outputs are labeled reconstructed/approximate, never original source by default.
7. **Builder** — create applications from a declared project manifest, templates, language profiles, tests, and reproducible build steps.
8. **Evolution Lab** — collect failure evidence, form a diagnosis, propose a patch, run isolated tests/replay/security checks, request approval, and produce a rollbackable release candidate.
9. **Evidence & Trust** — append-only execution records, artifact hashes, tool/model identities, policy decisions, test reports, replay outcomes, and explicit status taxonomy.
10. **Wallets & Portfolios** — pluggable portfolio/asset views only when a user configures an authorized data source. Keep financial accounts and credentials outside source code; no transactions or financial actions without explicit, scoped approval. The interface must not invent balances or claim live sync without a successful connector test.

## VX-native language strategy

VX should use a small set of explicit, versioned, typed domain languages rather than one vague universal language:

- **VX-Intent**: declarative user goal and constraints.
- **VX-Plan**: typed execution graph with dependencies, budgets, preconditions, and rollback strategy.
- **VX-Policy**: allow/deny/approval rules; default deny for unregistered capabilities.
- **VX-Project**: application manifest, source languages, dependencies, build/test commands, target platforms.
- **VX-Workflow**: reusable automation graph with typed inputs/outputs and failure branches.
- **VX-Evidence**: schema for provenance, hashes, observations, verification results, and replay receipts.
- **VX-Query**: read-only search across registered repositories, artifacts, logs, and evidence.
- **VX-IR**: optional intermediate representation for supported code-generation and analysis backends; not a promise to compile every language.

Each language requires a versioned grammar/schema, parser/validator, examples, error messages, and conformance tests. Start with JSON Schema or a typed Python model for the first implementation; do not claim a new compiler exists until parsing, validation, diagnostics, and round-trip tests pass.

## Governed engineering loop

`Intent → Clarify → Search → Evidence Triage → Plan → Policy Gate → Isolated Build/Inspect → Tests → Independent Verification → Approval → Candidate Release → Replay/Monitor`

A failed check moves the job to `BLOCKED`, `HOLD`, or `NEEDS_REVIEW`; it must not be silently upgraded to `VERIFIED`.

## Capability contracts

All tools are registered with:
- stable capability ID and version;
- owner and trust/provenance source;
- accepted input/output schemas;
- permissions and data classification;
- timeout, resource budget, and cancellation behavior;
- side-effect declaration and approval requirement;
- test suite, health check, and failure semantics.

The orchestrator may plan but may not bypass policy. Agents receive only task-scoped capabilities. Unregistered tools, missing permissions, invalid schemas, and missing required evidence fail closed.

## Self-improvement safety contract

`Observe → Diagnose → Propose → Branch → Build → Test → Security/Policy Review → Evidence Bundle → Human Approval → Release Candidate → Replay/Monitor → Rollback if needed`

- The running process cannot rewrite its active executable or canonical policy in place.
- Changes occur in an isolated worktree/branch with resource limits and a clean baseline.
- No automatic merge to `main`, deployment, credential change, or canonical-source mutation.
- Protect `project.genome` and `Ω.000`; require explicit owner approval for any proposed change.
- Preserve rejected proposals and their evidence for audit; do not delete or overwrite history.
- A model-generated explanation is not independent verification.
- Recovery must use durable state and recorded inputs; in-memory queues alone are not crash recovery.

## Program inspection and construction boundaries

- Prefer source-aware analysis where source is available.
- For binaries, start with metadata, hashes, signatures, SBOM/dependency checks, strings/symbols where appropriate, and static analysis.
- Execute unknown artifacts only in a disposable sandbox with network disabled by default, least privilege, resource/time limits, and explicit authorization.
- Decompilation may be incomplete or inaccurate and cannot recover information that was removed by compilation/obfuscation.
- Generated projects must include a manifest, lockfile where supported, build instructions, tests, license/provenance notes, and a reproducible evidence report.
- Never bypass DRM, access controls, or licensing restrictions.

## Initial delivery slices

### Slice 0 — inventory and contracts
Inspect the repository and existing implementation; map current capabilities to the contracts above. Do not duplicate already-existing modules.

### Slice 1 — workflow manifest and validator
Implement a minimal versioned `VX-Workflow` JSON schema and validator with deterministic validation errors and tests. No arbitrary shell execution in this slice.

### Slice 2 — capability registry and policy gate
Register capabilities and reject unregistered, unauthorized, or out-of-budget tasks. Add negative tests.

### Slice 3 — task runner and evidence envelope
Connect approved capabilities to the existing Active Objects/task lifecycle implementation where available. Record stable task IDs, input/output hashes, timestamps, and outcome status.

### Slice 4 — first interface
Expose a local, authenticated web interface for Command Center, Projects, Agents & Tasks, Model Bridge, Program Inspector, Evolution Lab, and Evidence. Use mock/demo data only when visibly labeled; never mix it with live results.

### Slice 5 — adapters and engineering tools
Add one provider adapter and one language/build backend at a time. Each must pass contract, connectivity, failure, timeout, and evidence tests before being marked connected.

### Slice 6 — controlled evolution
Generate patches only on isolated branches; run the complete test/security/replay suite; produce a reviewable PR. Human approval remains mandatory.

## Status labels

- `VERIFIED`: executable evidence exists and the named check passed.
- `SPECIFIED`: contract/documentation exists, implementation not yet proven.
- `PARTIAL`: some behavior is implemented but the complete contract is not met.
- `MISSING`: no implementation/evidence found.
- `CONFLICT`: evidence disagrees or the contract is violated.
- `PROPOSAL`: suggested future behavior, not implemented.

Every dashboard metric and integration badge must expose its source, last check time, and evidence reference. A configured provider is not a connected provider; a successful health check is not proof that every model feature works.

## Acceptance criteria for the first executable slice

1. Valid workflow manifests parse and normalize deterministically.
2. Invalid versions, unknown capability IDs, malformed input/output schemas, and forbidden side effects are rejected.
3. Tests cover positive and negative cases.
4. No unapproved external process or network action can run.
5. CI runs the tests and publishes a machine-readable evidence summary.
6. No canonical files are changed; no main merge or deployment occurs.

## Non-goals

- Claiming universal support for every programming language or executable format.
- Treating LLM output as trusted code or verified evidence.
- Unrestricted autonomous self-modification.
- Pretending local models, provider credentials, financial data, or device execution are connected without tests.
