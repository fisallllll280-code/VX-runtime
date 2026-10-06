# VX Runtime — RIRF Execution Boundary V1

## Role

VX-runtime is the execution boundary for an already admitted mutation. It is not the discovery engine and not the canonical governance authority.

## Required input

An execution request must already carry the applicable capability, policy, authorization, scope, and evidence references.

## Mutation rule

RIRF mutations execute against an isolated branch/worktree/sandbox. The default branch is never treated as the mutation workspace.

## Runtime evidence

The runtime must preserve execution identity, capability, input hash, output hash, event chain position, failure state, and replay reference where replay is applicable.

## Finality relationship

VX-runtime supplies execution facts. Finality is decided only after those facts are combined with the required verification, provenance, proof, and governance records.

Canonical Finality Gate specification: `VAIXLNS/docs/canonical/FINALITY_GATE_V1.md`.
