# Graft (Trail-Code) ↔ VX / Claude Code

Status: **IMPLEMENTED_ISOLATED**, not live-verified.

Upstream was requested as `trailhq/Graft` but GitHub now redirects its repository.
See https://github.com/trailhq/Graft and https://github.com/trailhq/Trail-Code.
Graft CLI is provided as `@nanonets/graft`; Trail-Code maintains compatibility.
The upstream describes these safe structural CLI operations:
`graft build`, `graft check --json`, `graft ask "<task>" --json`,
and `graft map`. No `--deep` requests are authorized in this adapter.

The new `vxruntime.graft_context` adapter creates canonical command plans,
rejects unknown operations and modified flags, requires an explicit approved
call and an absolute executable path supplied by the local operator, captures
bounded output and its SHA-256, and refuses implicit package installation.
It does not grant network isolation. Run only in a host/container that enforces
outbound egress denial, no secrets, no production file writes, and zero spend.

## Claude Code setup (operator-reviewed, not auto-executed)
Inside a disposable worktree with Node.js, Claude Code and the pinned Graft package:
1. `npm view @nanonets/graft version` — inspection only; review the version and package source.
2. `npx @nanonets/graft init --dry-run` — preview proposed changes.
3. Review proposed edits to `.claude/`, `.mcp.json`, instructions and hooks.
4. Only after permission and sandbox review, run `npx @nanonets/graft init --agents claude --no-global --no-statusline` in the disposable worktree.
5. Run `graft build` locally, then `graft check --json` and `graft ask "VX policy boundaries" --json`. Preserve command exit codes, timestamps, pinned package version and output hashes.

Graft's generated `graft/` graph is a local regenerated cache, not a replacement
for VAIXLNS sovereign `Ω.000` or any canonical index.
Never automatically commit generated hook configurations or transfer cache content
across trust boundaries. No implicit provider keys, `build --deep`, cloud spend,
automatic merges, or deployment.

Tests: `python -m pytest -q tests/test_graft_context.py`.

No Claude Code runtime invocation, installed Graft binary, or external network
is attested by these unit tests.
