# Claude Code ↔ VX (MCP stdio gateway)

Status: **implemented read-only MCP tool; CI tests required; no live Claude session attested**.

## Integration

From the `VX-runtime` repository root, the operator can configure Claude Code
with an MCP stdio server pointing to `python3 -m vxruntime.claude_mcp`.
In Claude Code, use `claude mcp add --transport stdio vx-runtime -- python3 -m vxruntime.claude_mcp`
from the repository root, then check availability using `claude mcp list`.

- Exposed tool: `vx_repository_metadata`.
- Default: blocked (no outbound network call).
- For explicitly approved **read-only** operations only, set
  `VX_CLAUDE_READ_ENABLED=1` in the host's controlled environment and pass
  `approved=true` for the tool call. The toggle is a local operator guard,
  **not** cryptographic authentication; never expose the stdio process to untrusted callers.
- No private GitHub credentials or write capability are provided. Read of private
  repositories will normally fail with 404 absent separate, deliberately
  implemented authorization; do not add a PAT to this bridge.
- Each result carries a hash-linked in-memory VX receipt.
- Current sovereign federation contract edges remain disabled.
- No shell commands, direct canonical writes, automatic merges or deployments.
- No model subscription or API spend is required for CI tests. Launching Claude
  Code itself may entail subscription/API usage and is not authorized by this file.

Verification: `python3 -m pytest -q tests/test_claude_mcp.py tests/test_repository_gateway.py`

Future work: signed grants, durable audit storage, integration challenge-response,
identity resolution, genuine Claude Code handshake, capability-scoped coding
operations and independent evidence review before production activation.
