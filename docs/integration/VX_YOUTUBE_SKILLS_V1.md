# YouTube Agent Skill admission into VX Agent Builder

Upstream: https://github.com/Jakeschincariol/youtube-agent-skill
Pinned commit: `a2feb2104981a375ffd4f87ee04f4f5344ac43c6`; MIT license.

Eleven skills and six Python utilities are indexed, preserving upstream
relative paths and Git blob hashes in `registry/youtube_skills.v1.json`.
`vxruntime/youtube_skills.py` validates the fail-closed manifest and
produces a deterministic SHA-256 receipt. Tests cover default registration
and six rejected privilege escalations.

**Not yet installed or executed:** original SKILL.md contents, six
Python tools, any Claude Code instance, a YouTube account, or upload API.
No automatic publication and no external spending are authorized.
The registry is an admission candidate, not a deployed agent. Before
enabling, audit each upstream file and run the six scripts on sanitized
local fixtures in a sandbox; compare outputs and source hashes.

Run `python -m pytest -q tests/test_youtube_skills.py`.
