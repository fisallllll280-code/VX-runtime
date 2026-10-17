# VX Agent Workshop Runtime Contract v1

Status: SPECIFIED
Scope: VX runtime only. This contract does not assert that any provider, CLI, connector, UI, or financial data source is live until the corresponding runtime probe and evidence receipt exist.
Protected sources: do not modify `project.genome` or `Ω.000` through this work.

## 1. Objective

VX is the contained workshop in which tool-specific agents are generated, executed in isolated workspaces, tested, compared, governed, and—only after explicit authorization—released. A provider name or generated manifest is not proof of an installed tool or a live integration.

## 2. Per-tool package

Every admitted tool package MUST include:

- A versioned adapter implementing the declared tool contract; no credential bypass, hidden scraping, or imitation of closed-source weights.
- A tool-specific agent generated from the shared factory template and constrained to that adapter's capabilities.
- A separate financial-specialist agent that can research, extract evidence, calculate, model scenarios, analyze risk, challenge assumptions, and produce an auditable financial work product.
- A machine-readable manifest, permission policy, input/output schema, health probe, timeout/retry policy, cost/latency telemetry, and reproducible evidence receipts.
- A dedicated API surface and a UI panel inside VX showing status, capabilities, active task, evidence, test results, costs, limitations, and permitted next actions.
- Unit, contract, integration, adversarial, regression, reproducibility, and failure-recovery tests appropriate to the tool.
- A challenger review that independently checks key calculations, evidence quality, uncertainty, and safety before a result can be promoted.

A tool without an available supported interface or authorized credentials remains DISCOVERED or SPECIFIED; VX MUST NOT claim that it has created a working provider session.

## 3. Claude Code and other engineering tools

Claude Code is treated as a tool adapter/agent candidate, not as a claim that VX can copy Claude's model or private implementation. Where an authorized Claude Code CLI/API is available, the package MUST record the executable/version, supported invocation mode, permissions, environment prerequisites, timeout behavior, and redacted probe evidence. It may create or modify files only inside an assigned workspace and branch. Network, shell, repository write, and publication permissions are separately scoped.

The same adapter contract applies to OpenAI, Anthropic, Gemini, Grok, Mistral, GitHub, research, design, spreadsheet, and publishing tools. Each provider/tool is independently configured and probed; success for one never implies success for another.

## 4. Financial specialist contract

The financial specialist MUST produce, when relevant:

1. A task statement, decision horizon, assumptions, and missing-data list.
2. Source-linked claims with timestamps and a distinction between observed facts, estimates, and hypotheses.
3. Reproducible calculations and explicit units/currency.
4. Base, upside, downside, and sensitivity scenarios where suitable.
5. Risk register, confidence/calibration, counter-evidence, and abstention when evidence is inadequate.
6. An output artifact plus a machine-readable result receipt containing task ID, agent/adapter versions, input hashes, source references, test suite/version, scores, failures, elapsed time, token/cost telemetry when available, and output hash.

It MUST NOT invent financial data, promise returns, represent an estimate as a fact, or trade/transfer money/purchase/sign/publish without separate explicit authorization and a policy gate. Financial advice requiring licensed professional judgment must be appropriately qualified.

## 5. API contract

The implementation should expose versioned interfaces equivalent to:

- `GET /api/v1/agents` — manifests and lifecycle states.
- `POST /api/v1/agents/{agent_id}/tasks` — submit a task with a declared capability and permission scope.
- `GET /api/v1/tasks/{task_id}` — status, progress, output references, and failures.
- `POST /api/v1/agents/{agent_id}/probes` — authorized health/live probe.
- `POST /api/v1/benchmarks/runs` — run an identified benchmark suite against candidates.
- `GET /api/v1/benchmarks/{run_id}` — score breakdown, safety gates, evidence, and ranking.
- `POST /api/v1/releases/{agent_id}/approval` — record human approval; not a bypass around failed gates.

These are target routes, not claims that routes currently exist. Implementation must add schemas, auth, audit events, validation, and tests before marking any route implemented.

## 6. VX interface contract

The Agent Workshop UI must provide:

- **Fleet:** per-tool agent cards with truthful lifecycle badge, adapter/version, health probe age, and evidence link.
- **Agent detail:** capabilities, permissions, API contract, configuration status, model/tool identity, limits, logs, and version history.
- **Task console:** submit task, view state transitions, inspect artifact/evidence, retry safely, and cancel where supported.
- **Benchmark arena:** identical task set, fixed evaluation rubric, side-by-side results, uncertainty, latency/cost, failures, and deterministic tie-breaking.
- **Financial workbench:** source-backed research, calculations, scenarios, risk/challenger findings, and exportable receipts.
- **Release/economics:** human-approved release queue, approved publication channels, revenue/cost ledger, attribution, refunds/complaints where available, and measured—not projected-as-fact—economic outcomes.

The UI must visibly distinguish NOT_CONFIGURED, CONFIGURED, LOCAL_TESTED, LIVE_PROBED, BENCHMARKED, POLICY_REVIEWED, ACTIVE, BLOCKED, and FAILED. Never infer a status from the existence of a file.

## 7. Testing and competitive challenge

Every candidate is tested against the same versioned suite and test data. Store suite hash, dataset version, run environment, candidate version, raw receipts, score breakdown, and failure labels. The proposed weighted score is:

- Numerical correctness: 25%
- Source accuracy: 20%
- Risk coverage: 15%
- Tool-contract correctness: 10%
- Calibration/abstention: 10%
- Adversarial robustness: 10%
- Latency/cost: 5%
- Recovery/repeatability: 5%

Safety is non-compensatory: unauthorized action, secret leakage, fabricated citations, critical calculation errors, or any unreviewed failure label blocks promotion regardless of score. Missing score dimensions are not silently imputed as success. Benchmarks must report sample size and uncertainty; rankings are provisional when sample sizes are too small.

## 8. Lifecycle and evidence gates

DISCOVERED -> CONTRACTED -> CONFIGURED -> LOCAL_TESTED -> LIVE_PROBED -> BENCHMARKED -> POLICY_REVIEWED -> ACTIVE.

Each transition requires its own evidence receipt. A local unit test is not a live provider probe; a live probe is not proof of benchmark superiority; a benchmark win is not release permission. A policy reviewer and task executor must be distinguishable for high-impact actions.

## 9. Economic and publication loop

Each generated tool/agent may propose its own product, offer, documentation, demo, or distribution experiment. VX records owner, target audience, claim substantiation, cost, price, channel, approval, release ID, attribution, and measured outcomes. Content and campaigns remain drafts until a human explicitly approves publication. No automatic posting, spend, customer promise, trading, or payment movement is enabled by default.

Measure net contribution only from observed values: collected revenue minus attributable costs, refunds, fees, and other defined expenses. Forecasts remain forecasts. No agent can declare itself the winner or publish its own unsupported performance claims.

## 10. Security and sovereignty

- Isolate each tool workspace and least-privilege credentials.
- Keep secrets out of manifests, prompts, logs, benchmark artifacts, and UI.
- Treat external content and tool output as untrusted input.
- Require explicit permission for repository writes, network access, publication, purchases, financial transactions, or canonical-state changes.
- Preserve existing drafts and evidence; do not merge to `main` or alter `project.genome`/`Ω.000` without explicit approval.
- Record immutable, hash-linked audit events for state transitions and approvals.

## 11. Current implementation boundary

This document is a target contract. The existing `vxruntime/financial_agent_factory.py` creates deterministic manifests and aggregates supplied benchmark receipts; it does not invoke providers, independently verify citations, serve the API, render the UI, or execute financial work. Those capabilities must be implemented and tested separately. Until then, report them as SPECIFIED or PARTIAL, never VERIFIED.
