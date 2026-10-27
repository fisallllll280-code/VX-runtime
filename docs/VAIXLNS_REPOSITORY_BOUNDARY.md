# VX-runtime Repository Boundary

Role: governed VX execution runtime, contracts and local reference capabilities.

The reference implementation exists in `vxruntime/core.py` and is covered by
executable tests. See `VAIXLNS_REPOSITORY_CONTRACT.md` for implementation commits.

Status: IMPLEMENTED / LOCAL REFERENCE; production and canonical admission HOLD.

Municipal lane: `vxruntime/agent_runner.py` invokes the same runtime, with a fixed
role and presence-only input profile. No official API transport is configured.

Canonical relationship:
VAIXLNS canonical rules -> VX-runtime contracts -> executable implementation -> tests/evidence -> verification.
