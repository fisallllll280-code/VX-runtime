# VX Agent Builder — mobile web MVP v1

Status: IMPLEMENTED_ON_ISOLATED_BRANCH; pending CI and device verification.

The existing VX mobile HTTP UI is extended through a subclass of its Handler,
preserving GET /, GET /api/status, POST /api/demo. New endpoints:
- GET /agents: Arabic mobile-first Agent Factory form
- GET /api/agents: current in-memory proposal records (instructions omitted)
- POST /api/agents: validate and create immutable proposal in local memory

Role allowlist: coding, research, testing, security, design, integration.
Tools allowlist: Read, Grep, Glob only. No Bash, shell, git write, network
access, arbitrary imports, model calls, background jobs or paid invocations.
Every proposed agent has stable identifier, canonical SHA-256 digest and
PROPOSED_NOT_RUNNING state. Duplicate IDs are rejected.

## Start locally
```bash
python -m vxruntime.agent_builder_app
```
Open `http://127.0.0.1:8765/agents` on the same host.

## Security/readiness
- 127.0.0.1 only; in-memory registry is not persistent.
- This is not user-authenticated. Origin filtering alone is insufficient
  for public deployment; requires sessions, CSRF protections and persistent
  audit/ledger before public release.
- No model execution or agent orchestration is enabled.
- No edits to project.genome, Ω.000, federation edge activation or main.
- External spending limit: zero SAR.

## Tests
`python -m pytest -q tests/test_agent_builder_app.py`

Physical iPhone validation is NOT_RUN until authenticated HTTPS deployment and
screenshots/test receipts. No public deployment is authorized.
