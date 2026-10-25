# VX Ω Evolution Forge — Sovereign Prompt Evolution Architecture v0.1

Status: PROPOSED. This file is an engineering specification; NOT a verified runtime feature or release.

## Inputs and licensing
- Candidate upstream: https://github.com/f/prompts.chat
- Repo license scope: MIT for code/site-authored content; CC0 1.0 for prompts.csv, PROMPTS.md and user-submitted prompt data as declared by upstream LICENSE.
- Capture upstream commit SHA, item path/line or stable item ID, source license version, retrieval timestamp and content digest.
- No dynamic ingestion or remote MCP enabled by this document. Check provenance, rights, privacy and outbound data policy before enabling any connector.
- Sponsors and referenced commercial vendors are NOT runtime dependencies.

## Pipeline
1. Discovery: deduplicate by exact digest and candidate semantic match, retaining independent source histories.
2. Prompt Intelligence: source metadata, classification, typed task contract and proposed JSON Schema. Store raw input as untrusted data.
3. Multi-Mind Evaluation: compare registered VX minds with separated calibration, accuracy, latency, cost and robustness metrics on locked evaluation sets.
4. Evolution Engine: optional DSPy or TextGrad candidate generator, strictly in an isolated sandbox and under budget; candidate generation has no authority to alter system instructions.
5. Attack Review: direct/indirect prompt injection, tool-call abuse, sensitive data disclosure, self-approval and license violations.
6. Proof: simulation receipts, deterministic test fixtures, evidence dependency graph, independent reviewer, policy digest and PCS-001 validation.
7. Admission: authorized governance decision. Do not change canonical system prompts, main, deployment or live model connector configuration automatically.
8. Monitoring: regression detection, revoke or roll back via authorized and recorded transitions.

## Contract (per prompt)
Required:
- prompt_id, source_ref, source_revision, license_evidence, origin_digest
- task_domain, requested_capabilities, mind_id, model_connector_id
- input_schema, output_schema, tool_permissions, secrecy_scope
- baseline_id, candidate_version, fixture_set_digest
- metric_scores, independent_test_receipts, simulation_evidence
- provenance_links, policy_version, reviewer_id, approval_receipt
- state: DISCOVERED | CLASSIFIED | EXPERIMENTAL | TESTED | VERIFIED | ADMISSION_PENDING | ADMITTED | REJECTED
Use UNKNOWN / HOLD for missing rights or evidence; 'VERIFIED' and 'ADMITTED' require separate receipts.

## Security invariants
- Existing PCS-001 = Proof-Carrying State contract. Do not redefine it as a prompt-compliance acronym.
- No Proof = No Canonical Promotion. A passing unit test is not evidence of live connector or total system readiness.
- Well-formed JSON does not imply true, safe or policy-compliant results.
- SHA-256 digest only establishes content equivalence/integrity relative to a trusted reference; it does not authenticate an originator. For signatures use a verified signing key and signed payload.
- Keep code execution and prompt data separate; block prompt-originated authority escalation.
- Refuse privileged actions: MERGE, PUBLISH, TRADE, TRANSFER_FUNDS, DELETE and secret extraction unless independently authorized by a separate governed runtime (not available in this proposal).
- Independent verification must not be performed by the authoring agent alone; track correlated evidence sources.

## Minimal verification backlog (NOT_RUN)
- Reject missing/unknown rights before redistribution.
- Detect corrupted source digest or missing origin revision.
- Reject spoofed mind IDs, forbidden tools and self-review.
- Verify structured output against JSON Schema AND domain-specific correctness checks.
- Repeat fixed test sets and compare against baseline; reserve held-out adversarial tests.
- Require complete replay evidence and explicit authorized admission before canonical promotion.
- Check no mutation of project.genome or Ω.000 and no release before sign-off.

## Boundaries
Integrate within current VAIXLNS and VX-runtime; reuse existing financial_agent_factory and agent_mind_registry, without inventing a fifth sovereign root. No paid API calls by default (0 SAR ceiling). No deployment, merge or model connection from this spec.

## Relevant references
https://github.com/f/prompts.chat/blob/main/LICENSE
https://prompts.chat/docs/api
https://github.com/stanfordnlp/dspy/blob/main/docs/docs/learn/optimization/optimizers.md
