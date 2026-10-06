# VX Runtime

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


