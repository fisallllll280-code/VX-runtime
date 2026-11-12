# VX Competence Lab v0.1

State: feature-branch implementation. This is a deterministic evaluation rubric, **not evidence of superhuman capability**, autonomous learning, or an installed LLM.

For every candidate improvement, compare results against an identical pinned task set and baseline. Capture per-case independent evidence and critical safety cases. Reject regressions, missing evidence and non-improvements. The `eligible` flag means only the candidate is suitable for independent review: evidence strings are not independently authenticated and there is no automatic promotion to VERIFIED.

Domains to benchmark separately: programming, factual retrieval with citations, mathematics, research quality, financial simulation *without orders*, task planning, security, memory retrieval accuracy, agent cost, latency and recovery. Use externally grounded tasks and blind human review where appropriate. Record model versions, costs, hardware and seeds; don't compare incomparable workloads.

Before production: signed evidence receipts, verified baseline, calibrated scoring, multiple independent reviewers, distribution shift checks, exploit resistance, holdout data and ongoing monitoring. No changes to Ω.000 or project.genome. No autonomous merge, deployment, account use, financial transaction or spend.

Tests: `python -m pytest -q tests/test_competence_lab.py`.
