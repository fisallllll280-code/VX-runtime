# VX Predictive Engineering Gate v1

**Status:** DESIGN / NOT VERIFIED IN CI.

## Goal
Find preventable defects before execution by combining diff analysis, contracts, dependency impact, test selection, static checks, deterministic simulation, and historical failure evidence.

## Pipeline
1. Capture the exact base/head commits and changed paths.
2. Protect canonical files: reject changes to project.genome and Ω.000.
3. Build an impact graph from changed modules to callers, contracts, schemas, tests, and dependent repositories.
4. Run cheap checks first: formatting, syntax/compilation, type checks, lint, secret/dependency scans.
5. Run targeted unit tests, then integration and regression tests.
6. Generate boundary cases and property-based tests for changed contracts.
7. Run deterministic replay and fault injection in a sandbox with external side effects disabled.
8. Rank risks by severity, likelihood, blast radius, evidence quality, and uncertainty.
9. Block on explicit invariants or failed mandatory checks; otherwise require review when evidence is weak.
10. Preserve a signed/hashed report with commit IDs, commands, exit codes, findings, and artifacts.

## Risk scoring
Use an explainable score, not an opaque model verdict:
Risk = Severity × Likelihood × BlastRadius × Uncertainty.
The score prioritizes investigation; policy gates determine whether execution is allowed. Calibrate likelihood only from measured historical outcomes and publish false-positive/false-negative rates.

## Learning loop
After each verified defect, store a sanitized failure signature, root-cause label, affected component, reproducer, effective test, fix category, and recurrence result. Use this corpus to propose targeted tests and improve risk ranking. Do not train on secrets or unreviewed claims; keep prediction separate from proof.

## Automatic repair boundary
Repairs are proposals in an isolated branch. Allow one bounded repair attempt, inspect the diff, rerun the failed test and regression suite, then replay evidence. Repeated failure, protected-file change, policy bypass, dependency expansion, or unrelated edits cause rejection and rollback. Merge and deployment require explicit owner approval.

## Evaluation
Use seeded defects and historical incidents to measure:
- defect detection recall and precision before merge;
- false-block rate and missed-defect rate;
- test runtime and CI minutes saved;
- regression rate after accepted fixes;
- reproducibility of each verdict;
- cost per prevented defect.

## Limits
No system can guarantee knowledge of every future error. Static analysis and models estimate risk; tests and reproducible evidence establish only the properties they actually cover. Keep unknowns explicitly marked UNKNOWN/PENDING_VERIFICATION.
