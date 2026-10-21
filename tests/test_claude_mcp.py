import json
from vxruntime.claude_mcp import TOOL, handle
from vxruntime.repository_gateway import OWNER


def request(method, arguments=None, request_id=1):
    obj = {"jsonrpc": "2.0", "id": request_id, "method": method}
    if arguments is not None:
        obj["params"] = {"name": TOOL, "arguments": arguments}
    return obj


def test_handshake_and_discovery():
    assert handle(request("initialize"))["result"]["serverInfo"]["name"] == "vx-governed-github"
    assert handle(request("tools/list"))["result"]["tools"][0]["name"] == TOOL


def test_approval_flag_does_not_bypass_operator_gate(monkeypatch):
    monkeypatch.delenv("VX_CLAUDE_READ_ENABLED", raising=False)
    called = []
    res = handle(request("tools/call", {"repository": "VX-runtime", "approved": True}),
                 lambda repo: called.append(repo))
    assert json.loads(res["result"]["content"][0]["text"])["status"] == "blocked"
    assert called == []


def test_explicit_gate_permits_approved_read(monkeypatch):
    monkeypatch.setenv("VX_CLAUDE_READ_ENABLED", "1")
    res = handle(request("tools/call", {"repository": "NEXENT", "approved": True}),
                 lambda repo: {"full_name": f"{OWNER}/{repo}", "default_branch": "main"})
    receipt = json.loads(res["result"]["content"][0]["text"])
    assert receipt["status"] == "success" and receipt["ledger_valid"]


def test_disabled_grant_blocks_even_with_gate(monkeypatch):
    monkeypatch.setenv("VX_CLAUDE_READ_ENABLED", "1")
    res = handle(request("tools/call", {"repository": "NEXENT"}), lambda _: None)
    assert res["result"]["isError"] is True


def test_unrecognized_tool_and_notification():
    assert handle(request("tools/call", {"repository": "NEXENT"}) | {"params": {"name": "other", "arguments": {}}})["error"]["code"] == -32602
    assert handle({"jsonrpc": "2.0", "method": "notifications/initialized"}) is None
