# VX-APP-PREVIEW-001 — First release execution gate (2026-10-24)

**Current outcome: HOLD / NOT PUBLISHED.** This release candidate must NOT be
presented as an installed iPhone app or production hosted service.

## Inspected evidence
- Repository: `fisallllll280-code/VX-runtime`, public; default branch `main`.
- Feature chain: Graft context → mobile VX app → Agent Builder → YouTube skills.
- Agent Builder PR #23 and YouTube skills PR #24 were **draft/open at inspection**.
- Mobile app PR #22 was merged to the Graft feature branch, NOT to main.
- Latest displayed GitHub Actions success was for older commits, not the
  exact release candidate commit SHA.
- Agent Builder stores proposals only in process memory, binds loopback :8765,
  lacks production authentication, CSRF defenses and persistent evidence.

## Publication sequence
1. Run all feature tests and inspect failures on a single pinned head SHA.
2. Add authenticated identity/session controls, CSRF, durable audit database,
   network/sandbox boundaries, security scan, threat review.
3. Verify mobile browser on an iPhone using a separate authorized TLS staging
   host; preserve screenshots and a redacted end-to-end test receipt.
4. Confirm exact dependency licenses, secret scan and immutable file digests.
5. Request separate explicit approval for cost, merge to main and public release.
6. Only then enable staging release pipeline. Rollback must restore known good
   version without losing immutable audit history.

## Local no-network proof
```bash
python -m pytest -q tests/test_release_preflight.py
python -m vxruntime.release_preflight
```

Manifest: `release/vx_app_preview_001.json`.
This policy gate **cannot produce evidence itself** or publish; its fixed HOLD
decision prevents mistaken release on user-supplied status labels. Independent
CI and approval verification are still required.

No production token, API connection, deployment, merge or spend authorized.
