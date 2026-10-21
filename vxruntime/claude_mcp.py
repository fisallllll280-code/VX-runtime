"""Minimal read-only MCP stdio bridge: Claude Code -> VX governed repository gateway.

No third-party dependencies, shell invocation, subprocesses, credentials, or
network access before an explicitly approved tool call. Private repository data
is not made available by this bridge.
"""
from __future__ import annotations
import json
import sys
from .repository_gateway import CAPABILITY, OWNER, ReadGrant, governed_repository_read

PROTOCOL = "2025-06-18"
TOOL = "vx_repository_metadata"
TOOL_SCHEMA = {
    "name": TOOL,
    "description": "Read allowlisted public GitHub repository metadata through VX policy and ledger. Explicit approval is required.",
    "inputSchema": {
        "type": "object",
        "properties": {
            "repository": {"type": "string", "description": "Repository short name, e.g. VX-runtime"},
            "approved": {"type": "boolean", "description": "An externally granted read authorization; defaults false"}
        },
        "required": ["repository"],
        "additionalProperties": False
    }
}


def handle(message, fetcher=None):
    if not isinstance(message, dict):
        return None
    method = message.get("method")
    req_id = message.get("id")
    if req_id is None:  # MCP notifications must not be answered.
        return None
    def ok(value):
        return {"jsonrpc": "2.0", "id": req_id, "result": value}
    def error(code, detail):
        return {"jsonrpc": "2.0", "id": req_id, "error": {"code": code, "message": detail}}
    if method == "initialize":
        return ok({"protocolVersion": PROTOCOL, "capabilities": {"tools": {}},
                   "serverInfo": {"name": "vx-governed-github", "version": "0.1.0"}})
    if method == "ping":
        return ok({})
    if method == "tools/list":
        return ok({"tools": [TOOL_SCHEMA]})
    if method != "tools/call":
        return error(-32601, "Method not found")
    params = message.get("params")
    if not isinstance(params, dict) or params.get("name") != TOOL:
        return error(-32602, "Unknown tool")
    args = params.get("arguments") or {}
    if not isinstance(args, dict) or set(args) - {"repository", "approved"}:
        return error(-32602, "Invalid tool arguments")
    repo = args.get("repository")
    if not isinstance(repo, str) or not repo or type(args.get("approved", False)) is not bool:
        return error(-32602, "Invalid repository or approval type")
    # Boolean tool arguments are NOT an authorization boundary. Activation
    # requires the operator to set VX_CLAUDE_READ_ENABLED=1 in the host process.
    import os
    permitted = os.environ.get("VX_CLAUDE_READ_ENABLED") == "1"
    grant = ReadGrant(repo, CAPABILITY, args.get("approved") is True and permitted)
    kwargs = {"fetcher": fetcher} if fetcher else {}
    receipt = governed_repository_read(f"mcp-{req_id}", grant, **kwargs)
    return ok({"content": [{"type": "text", "text": json.dumps(receipt, sort_keys=True)}],
               "isError": receipt["status"] != "success"})


def main():
    for line in sys.stdin:
        try:
            response = handle(json.loads(line))
            if response is not None:
                sys.stdout.write(json.dumps(response, separators=(",", ":")) + "\n")
                sys.stdout.flush()
        except (ValueError, TypeError) as exc:
            sys.stdout.write(json.dumps({"jsonrpc": "2.0", "id": None,
                "error": {"code": -32700, "message": str(exc)}}) + "\n")
            sys.stdout.flush()


if __name__ == "__main__":
    main()
