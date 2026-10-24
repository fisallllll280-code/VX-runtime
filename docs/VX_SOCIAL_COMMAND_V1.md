# VX Social Command v1 — isolated local prototype
Status: IMPLEMENTED IN SOURCE / NO LIVE CONNECTION / TEST RUN NOT YET VERIFIED.

## Architecture
- Source: `tools/vx_social_command.py` (stdlib only).
- Target: 13 social platforms. Registration means an internal placeholder, **not** verified ownership, social login, or connected access.
- A local JSON ledger records account placeholders, posts, approvals and a chained event digest.
- Publishing is *unconditionally disabled* even for approved posts. No OmniSocials credentials, network calls, subscriptions, API integration or social accounts are created.
- Data is held locally under `build/social-command/` by default. Treat it as local prototype state, not trusted evidence storage. Audit event hashes detect event modification but are **not** externally notarized and do not protect against replacement of the whole ledger; add signed append-only storage before production.
- Roles are represented by caller-provided actor strings for prototype demonstrations only. They are **not authenticated**; never use these approvals as real authorization.

## Local usage
Run from repository root (no installs required):

```bash
python -m unittest discover -s tests -p 'test_vx_social_command.py' -v
python tools/vx_social_command.py status
python tools/vx_social_command.py register x @VAIXLNS --actor owner
python tools/vx_social_command.py draft x:@vaixlns "Our early announcement" --actor writer
python tools/vx_social_command.py transition POST-000001 submit --actor writer
python tools/vx_social_command.py transition POST-000001 approve --actor reviewer
python tools/vx_social_command.py publish POST-000001 --actor owner
```

The last command **must fail closed** with exit status 2. This module does not publish anything.

## Required hardening before production
1. Confirm brand-account ownership via provider OAuth; maintain secret vault with scoped credentials; no tokens in Git.
2. Authenticate users centrally; role-based authorization, separate author/reviewer identities, owner signed release.
3. Review OmniSocials current official SDK/API and supported platforms; implement one verified sandbox adapter behind VX policy.
4. Use transactional DB, immutable signed events, revision binding of approvals to content, concurrency protection and idempotency keys.
5. Rate limits, opt-outs, deletion, privacy, regional platform rules and incident controls.
6. Tested UI, iPhone Safari checks, CI logs, external integration evidence and explicit owner launch approval.

Rules: Zero SAR external spend; no merge to main; no modification to `project.genome` or `Ω.000`.
