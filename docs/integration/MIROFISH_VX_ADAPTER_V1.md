# MiroFish → VX | bounded integration v1

Upstream: https://github.com/666ghj/MiroFish | License: AGPL-3.0.
Upstream README: Python 3.11–3.12, local backend :5001, LLM/Zep credentials required for normal deployments.
Contract inspected: `backend/app/api/simulation.py`: POST `/api/simulation/create`
with `project_id`, optional `graph_id`, `enable_twitter`, `enable_reddit`;
response `success=true`, `data.simulation_id`, `data.project_id`.

Integration implemented: `vxruntime.mirofish_adapter.submit_simulation`.
Fail-closed by default, accepts only an explicitly supplied transport for
loopback-only (127.0.0.1 / localhost port 5001), an explicit operator approval
flag, zero cost budget, and a bounded request payload.
Receipts are hash-linked in the existing VX in-memory ledger.
Unit tests supply mock transport; no network/API/model usage.

**WARNING:** Creating a MiroFish simulation is a stateful operation on the
target backend and may trigger or lead to consumption of paid services. The
local approval flag is a developer gate, NOT strong IAM or proof of zero spend.
Do not supply a real transport until host-level sandbox, billing isolation,
authenticated authority grants, and independent evidence gate pass. The
current code does NOT provide a production transport or run simulations.
No federation contract edges have been activated.

Test: `python -m pytest -q tests/test_mirofish_adapter.py`.
Admission status: IMPLEMENTED_ISOLATED / NOT_LIVE / NO_PRODUCTION_APPROVAL.
