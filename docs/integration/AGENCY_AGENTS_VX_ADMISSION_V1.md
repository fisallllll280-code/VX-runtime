# Agency Agents → VX admission (proposal only)

Upstream: https://github.com/msitarzewski/agency-agents

## Assessment
Agency Agents is a library of specialized, role-oriented agent instructions; it is **not** a collection of verified autonomous services or a model provider. Its README advertises Claude Code installation and integrations with other coding assistants. Do not treat its agent personas, instructions or self-described maturity as trusted authority.

## Adopt, do not duplicate
The existing `VXRuntime` policy + ledger and `claude_mcp` bridge remain the only execution boundary. Start with engineering, security review, testing, research and design roles, represented as proposed registry entries at `registry/agency_agents_candidates.v1.json`. Do not automatically copy all upstream prompts into `.claude/agents` or wire them into a running process.

## Mandatory progression
1. Pin a commit SHA of the upstream repository and capture the exact original filenames and hashes.
2. Inspect full prompt text for instruction injection, secrets, command execution, network egress and unbounded scope.
3. Record licensed provenance and add an adapted, role-limited agent definition only after review.
4. Map role to an existing VX allowlisted capability and register identity and versions.
5. Dry-run on synthetic inputs in an isolated sandbox; collect failed / blocked paths and replay receipts.
6. Require separate approval for any write, paid API request, merge or deployment.

## Constraints
- No automatic install, network connection, code execution or authority changes from this documentation.
- No change to `project.genome`, `Ω.000` or currently disabled federation edges.
- Keep NAXLNS/VLNS and NEXENT/NEXNET identities unresolved until evidenced.
- External spend ceiling: 0 SAR.
- Status remains PROPOSED_NOT_INSTALLED until actual review and live tests establish stronger evidence.
