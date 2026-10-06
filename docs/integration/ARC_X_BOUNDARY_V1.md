# ARC-X Ω Boundary — VX Runtime Integration v1

**Status:** SPECIFIED

VX remains the governed deterministic execution and replay boundary. ARC-X does not replace VX.

## ARC-X may request from VX
- execution of an admitted candidate;
- health and readiness observations;
- event/state/evidence capture;
- deterministic replay;
- runtime reconstruction evidence.

## VX MUST preserve
- authorization before capability execution;
- stable execution identity;
- hashable input/output evidence;
- append-only execution history;
- deterministic replay from original inputs;
- separation of evolution proposals from execution.

## Boundary

```text
ARC-X
  ↓
admission request
  ↓
VAIXLNS governance
  ↓
VX
  ↓
events / state / observations
  ↓
evidence
  ↓
ARC-X reconstruction
```

Startup, health, or successful execution MUST NOT be interpreted as semantic proof by themselves.

See the canonical ARC-X specification in the VAIXLNS repository:
https://github.com/fisallllll280-code/VAIXLNS/blob/main/docs/tools/ARC_X_EPISTEMIC_REALITY_COMPILER_V1.md