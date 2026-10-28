# VX Auto-Repair Agent v1 — Bounded Failure Triage

**Status:** PROTOTYPE / NOT VERIFIED IN CI  
**Owner layer:** VX-runtime execution and evidence; VAIXLNS remains the authority layer.

## Purpose
Run a chosen test command, classify common failure signatures, optionally invoke one explicitly configured repair adapter with the captured failure log on stdin, then rerun the same test command once. Emit a JSON report.

## Safety contract
- Run only in a disposable worktree or isolated branch.
- The repair adapter is optional and never invoked unless explicitly configured.
- This tool does not provide credentials to the adapter; do not expose secrets in test logs.
- No merge, release, deployment, or external side effect is performed.
- One repair attempt maximum per invocation; no infinite repair loops.
- A zero exit code means only that the configured tests passed, not that the root cause is proven or the whole system is correct.
- project.genome and Ω.000 are protected and must not be modified by any future adapter.
- Root-cause categories are signature matches, not verified causality.

## Usage
Run tests and produce a report:
    python tools/vx_auto_repair.py --test-command python -m pytest

Use a trusted repair adapter only inside an isolated checkout:
    python tools/vx_auto_repair.py --test-command python -m pytest --repair-command python tools/my_repair_adapter.py

The adapter reads the captured first-run log from stdin. It must make a minimal patch, avoid protected files, and exit non-zero if it cannot safely repair. The runner then reruns the configured test command once.

## Integration path
1. Add unit tests for classification and subprocess outcomes.
2. Wire into a non-privileged GitHub Actions job on feature branches and pull requests.
3. Add an evidence artifact and explicit protected-path checks.
4. Integrate an approved model adapter behind a policy gate and strict patch allowlist.
5. Require independent tests/replay and human approval before merge.

## Known limitations
The prototype does not itself generate code patches or prove semantic root causes. Automatic patch generation requires a separately configured repair adapter and policy-controlled model/tool access. Adding these files alone does not execute CI.
