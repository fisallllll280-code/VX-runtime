# VX Mobile Control Center — local MVP

This implements an actual mobile-responsive HTML interface backed by the
existing `VXRuntime` in-memory governed execution engine.
It is a **local engineering demo**, not a shipped iOS app, PWA install or public service.

## Run
From `VX-runtime` repository root in Python 3.11+:
```bash
python -m vxruntime.mobile_app
```
Open http://127.0.0.1:8765 on the **same machine**. The server binds to loopback;
an iPhone cannot open this address from a different device. Real iPhone delivery
requires a separate authorized TLS deployment, authentication and mobile test.
No subscription, remote endpoint, model API or payment integration is involved.

The page calls:
- GET /api/status — displays ledger integrity, run count and truthful missing connectors.
- POST /api/demo — performs bounded integer addition using existing VX runtime,
  and returns a locally generated receipt with hashes.

## Security boundaries
- Loopback only, restricted input size/types, origin filtering for POST.
- No file writes, no GitHub write tokens, no `project.genome` or `Ω.000` changes.
- **Demo only**: no strong session authentication, no persistence, no distributed
  multi-worker consistency. Do not deploy as-is on a public interface.
- Ledger verifies the in-memory event hash chain; it is not proof of remote systems.
- No app-store, PWA manifest or installable native app is claimed.

## Test
`python -m pytest -q tests/test_mobile_app.py`
Admission requires test logs for this exact feature branch and a physical
iPhone browser screenshot/session before device-verification claims.
