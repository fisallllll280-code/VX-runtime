# VX Agency Agents — isolated Claude Code admission

Upstream pinned commit: `4e3ac3ca6604c75113f52c695dbddcc7af928b46` (2026-10-19).
License: upstream `LICENSE` (MIT); refer to original copyrighted prompts via URLs, not vendored.
Reviewed source paths and Git blob SHAs:
- engineering/engineering-code-reviewer.md — `fb93291f4b94a8d5687aa1cc0d05741c3352dd22`
- testing/testing-test-automation-engineer.md — `59650291b60ed280f8f5d5da69f15fec2aea3dca`
- testing/testing-evidence-collector.md — `321ce36bd2586254b0d7194c5f62965204170532`

Implemented independent, constrained Claude Code subagent descriptors:
- `.claude/agents/vx-code-reviewer.md`
- `.claude/agents/vx-test-engineer.md`
- `.claude/agents/vx-evidence-reviewer.md`

These expose only Claude Code's Read, Grep and Glob tools. They cannot independently change code, invoke Bash, spend money, read remote GitHub through the VX MCP adapter, or merge/deploy. A client may still have broader capabilities outside these agents, so this prompt-level limitation does **not** replace host policy/sandboxing.

## Operator validation
```bash
python3 -m pytest -q tests/test_agency_agents_admission.py
claude
```
Within a Claude Code workspace rooted at this repository, inspect `/agents` to discover project agents, and select a read-only reviewer. Do not use bypass-permissions.

## Proof boundaries
Files committed is **IMPLEMENTED** only. Offline unit tests require independent CI evidence. Claude Code discovery and subagent invocation have **NOT BEEN RUN** in a real Claude session. No runtime federation edges activated; no user expense or deployment.
