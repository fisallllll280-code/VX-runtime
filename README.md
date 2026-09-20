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
