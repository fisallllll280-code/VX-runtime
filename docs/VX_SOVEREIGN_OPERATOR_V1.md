# VX Sovereign Operator v0.1

**State:** prototype, feature branch, pending independent CI; no external agents connected.

Purpose: allow VAIXLNS to plan, simulate, approve and execute **locally bounded** operations while preserving evidence and keeping the owner in control.

Authority: **not impersonation**. The operator acts through explicitly delegated capabilities and does not inherit account authority. No universal control, no silent deployment or purchases.

Sequence: simulation (pure, no handler) → exact-input fingerprint → explicit in-process approval → policy-gated local execution → VX event hash and replay substrate. Approval is limited to the exact task fingerprint; modifying parameters invalidates it.

Allowed demonstration capabilities: inspect, analyze, draft, test_local. Forbidden: publish, merge, pay, trade, send, delete, modify_canonical; any external effects or nonzero spend. No connection to models, browsers, OAuth, persistent queue or GitHub write tools.

Limitations before production: approvals are in memory and do not survive restarts; no signed authority tokens, two-person review, persistent work queue, tenant separation, handler sandbox, distributed lock or independent audit. Do not put untrusted handlers into this runtime. The system is NOT fully autonomous and NOT production ready.

Example:

```python
from vxruntime.operator import SovereignOperator
op=SovereignOperator()
ticket=op.simulate("task-1","analyze",{"data":"sample"})
op.approve(ticket)
out=op.execute("task-1","analyze",{"data":"sample"},lambda p:len(p["data"]))
assert out.decision=="EXECUTED"
```

Test: `python -m pytest -q tests/test_operator.py`. Never merge to main or publish without separate approval.
