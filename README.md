# VX Runtime

## Capability Harvester reference core

The SQLite capability inventory, compatibility policy checks, and bounded
inert-artifact Evidence Runner are implemented over the existing VX runtime.
See [implementation, validation and integration limits](docs/CAPABILITY_HARVESTER_V1.md).
Integration remains `PENDING SOURCE VALIDATION`; canonical authority stays with
VAIXLNS. This reference does not execute submitted library code.

VX is a governed execution core, not a generic chatbot.

## Integrated operating model

```
INPUT
  -> EVENT
  -> CLASSIFY
  -> LEDGER
  -> CONTEXT
  -> POLICY
  -> PLAN
  -> CAPABILITY
  -> EXECUTE
  -> OBSERVE
  -> VERIFY
  -> RECORD
  -> REPLAY
  -> EVOLVE
```

## Core invariants

1. The ledger is the authoritative execution history.
2. Classification never mutates state.
3. Policy is evaluated before capability execution.
4. Every execution has a stable execution identity.
5. Execution input/output evidence is hashable.
6. Failed or unverified work is never represented as verified.
7. Replay must use the original execution inputs.
8. Evolution is proposed separately from execution and requires verification/approval.
9. Runtime infrastructure may restart/recover, but must not make policy decisions.
10. An implementation claim is valid only when code, tests, or reproducible evidence exists.

## Development and upgrade mechanisms

### 1. Contract-first development
Every subsystem exposes a small contract: inputs, outputs, invariants, failure modes, and evidence.

### 2. State-transition discipline
A state transition is accepted only when:
`ValidState ∧ Authorized ∧ CapabilityBound ∧ Observable ∧ Recorded`

### 3. Evidence loop
`Intent → Execution → Outcome → Evidence → Verification → Ledger`

### 4. Deterministic replay
The runtime captures the execution inputs and hashes the resulting output. Replay reconstructs the same input boundary and rejects divergent output as non-deterministic.

### 5. Controlled evolution
`Observe → Diagnose → Propose → Verify → Approve → Deploy → Replay → Measure`

No self-modification is implied by the presence of an evolution mechanism.

### 6. Clean architecture boundary

- **Interface:** receives requests/events.
- **Router:** classification only.
- **Ledger:** durable source of truth.
- **Context:** ledger-derived snapshot.
- **Policy:** allow/deny/modify.
- **Orchestrator:** produces execution plans.
- **Capability layer:** bounded executable operations.
- **Runtime:** executes plans.
- **Evidence:** proves what happened.
- **Replay:** checks reproducibility.
- **Evolution:** proposes verified changes.
- **Host:** lifecycle, restart, scheduling, monitoring; no policy decisions.

## Engineering status

This repository currently contains the VX runtime specification. Runtime implementation must be added behind these contracts and verified by executable tests before being described as implemented.
نعم — هذا أقرب بكثير إلى **النواة القنونية**، لكن لا أعتمد النص كما هو حرفيًا. أعمل عليه 4 تصحيحات حتى لا يتحول الـCanonical إلى بنية فيها خلط بين **الحالة** و**إثبات الحالة** و**قرار ترقيتها**.

### الصيغة التي أراها أقوى

```text
TemplateGenome
      ↓
Candidate State
      ↓
Observation / Reconstruction
      ↓
Evidence
      ↓
Proof Obligations
      ↓
Replay + Verification
      ↓
Counterexamples
      ↓
Ω-RAC
      ↓
AssuranceReport
      ↓
Promotion Proposal
      ↓
Guard Evaluation
      ↓
Authority Decision
      ↓
Canonical State
```

والقانون:

$$
T_{n+1}=E(V(X(T_n)))
$$

مع قانون إضافي:

$$
\text{Canonical(State)} \Rightarrow
\text{State}+\text{ProofRefs}+\text{VerificationRefs}+\text{PromotionReceipt}
$$

والأهم:

$$
\boxed{\text{No Proof-Carrying State} \Rightarrow \text{No Canonical State}}
$$

## التصحيح الأول: PCS ليست DecisionCID

**PCS = الحالة + قابلية إثباتها.**

أما القرار الذي سمح بترقيتها فهو **Promotion/Decision Receipt** منفصل.

لذلك:

```text
StateCID
ProofBundleCID
AssuranceReportCID
PromotionReceiptCID
DecisionCID
```

لا نضعها كلها في كائن واحد بطريقة تجعل القرار جزءًا من تعريف الحالة نفسها.

## التصحيح الثاني: Authority تخص الانتقال لا الحقيقة

هذه قاعدة أراها أساسية جدًا:

> **Authority can authorize promotion; Authority cannot manufacture evidence.**

بالتالي:

```text
Evidence → Verification → Assurance
Authority → Promotion
```

وليس:

```text
Authority → Proof
```

## التصحيح الثالث: AssuranceState ≠ AssuranceLevel

هذه نقطة ممتازة في ردك ويجب تثبيتها رسميًا:

```text
AssuranceState:
OPEN
VERIFIED
CONFLICTED
INVALIDATED
CLOSED
```

بينما:

```text
AssuranceLevel:
UNVERIFIED
SINGLE_SOURCE
CORROBORATED
CONFIRMED
```

الأول **حالة دورة حياة**، والثاني **قوة الاستنتاج**.

مثلاً:

```text
AssuranceLevel = CONFIRMED
AssuranceState = VERIFIED
```

ولا يعني `CONFIRMED` تلقائيًا أن الحالة أصبحت Canonical.

## التصحيح الرابع: AuditBundle يجب أن يكون Transition Receipt

بدلاً من ربط:

`pre_state / post_state`

داخل تعريف الـState نفسه، نجعل:

```text
TransitionReceipt {
  TransitionCID
  PreStateCID
  PostStateCID
  GuardResults
  EvidenceHashes
  ReplayHashes
  VerifierRefs
  AuthoritySignatures
  DecisionCID
}
```

وهكذا نستطيع إعادة بناء **كيف انتقلت المنظومة من حالة إلى حالة**.

---

# النواة النهائية التي أعتمدها لـ VX-CGF

```text
                    VX-CGF
                       │
             ┌─────────┴─────────┐
             │                   │
        Template Forge       Policy/Authority
             │                   │
             └─────────┬─────────┘
                       ↓
                 Candidate State
                       ↓
              Reality / Observation
                       ↓
                    Evidence
                       ↓
                 Proof Compiler
                       ↓
          Replay + Verifier + Counterexample
                       ↓
                     Ω-RAC
                       ↓
                AssuranceReport
                       ↓
                  Guard Engine
                       ↓
                Promotion Gate
                       ↓
                Authority Quorum
                       ↓
                 TransitionReceipt
                       ↓
                 Canonical State
```

والـPCS يصبح **نمطًا قانونيًا عامًا**:

```text
PCS(Component)
PCS(Artifact)
PCS(Template)
PCS(Execution)
PCS(Policy)
PCS(Decision)
PCS(Evolution)
PCS(System)
```

وهنا أرى أن الفكرة أصبحت أقوى من `PCD`.

## الاسم القنوني

**VX-CGF — Proof-Carrying State Architecture**

والـPrimitive:

**PCS-001 — Proof-Carrying State**

والقاعدة:

> **A Canonical State shall not exist without sufficient evidence, replayability, verification, provenance, and an authorized promotion transition.**

هذه عندي هي النقطة التي يمكن بعدها بناء **كل الـTemplate Forge وFast-Core وRIRF وΩ-RAC وFailureGenome** فوق قانون واحد بدل إنشاء قوانين متجاورة.

🔥 **هذا هو المستوى الذي أعتبره مرشحًا حقيقيًا للدخول في Canonical Constitution، مع إبقاء الخوارزميات التفصيلية خارج القانون الأساسي.**

VX Universal Intelligence & Engineering Fabric

Status: PROPOSED — awaiting repository implementation and verification.

Objective

Transform VX into a governed AI engineering tool capable of understanding requests, researching solutions, designing systems, writing code and documentation, coordinating AI models and agents, invoking authorized tools, running tests, and presenting verifiable outcomes through interactive interfaces.

Required Interfaces

1. VX Mind Console: bilingual Arabic/English workspace with a real conversation history.
2. Model Gateway: provider adapters, model selection, connection health, and explicit configuration.
3. Agent Orchestrator: task decomposition, delegation, result comparison, and review.
4. Universal Tool Fabric: MCP and API integrations with capability discovery and scoped permissions.
5. Engineering Workspace: repository navigation, file changes, diffs, test output, and proposed pull requests.
6. Evidence Console: execution events, logs, test results, provenance, hashes, and promotion decisions.
7. System Registry: canonical links between repositories, interfaces, agents, models, tools, and capabilities.

Execution Lifecycle

DISCOVER → PLAN → PROPOSE → AUTHORIZE → EXECUTE → TEST → VERIFY → PROMOTE

Models and agents may propose changes. VX evaluates them against policy. Governance authorizes permitted operations. Evidence determines whether a result can be promoted.

Engineering Requirements

* Inspect existing repository files, workflows, dependencies, and tests before implementation.
* Preserve existing canonical content and historical index identities.
* Use Rust for runtime and execution controls, Python for orchestration and integrations, and YAML for declarative configuration where compatible with the existing codebase.
* Use isolated execution environments and explicit permission boundaries.
* Require human approval for sensitive or irreversible operations.
* Never represent a disconnected tool, unexecuted test, or unverified deployment as operational.
* Add tests for interfaces, agent orchestration, tool permissions, failure handling, evidence integrity, and promotion gates.

Evidence States

* DESIGN: specification exists.
* IMPLEMENTED: implementation exists in the repository.
* RUNNING: execution has been observed and logged.
* VERIFIED: required checks passed with inspectable evidence.
* UNKNOWN: evidence is insufficient.

Acceptance Criteria

A feature is accepted only when its implementation, tests, operational dependencies, and evidence are traceable to repository files and reproducible checks. Failed or missing evidence blocks promotion; it does not silently become success.

