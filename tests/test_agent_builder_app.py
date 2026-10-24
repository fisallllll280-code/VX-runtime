"""Agent Builder admission and real loopback HTTP smoke tests."""
from http.server import HTTPServer
from threading import Thread
from urllib.request import Request, urlopen
from urllib.error import HTTPError
import json
import pytest
from vxruntime.agent_builder_app import Handler, REGISTRY, LOCK, proposal


def sample(agent_id="vx-test-01"):
    return {"agent_id": agent_id, "role": "testing",
            "instructions": "Review evidence and propose isolated tests.",
            "tools": ["Read", "Grep"]}


def test_proposal_digest_and_no_execution():
    item = proposal(sample())
    assert len(item["digest_sha256"]) == 64
    assert item["status"] == "PROPOSED_NOT_RUNNING"
    assert item["execution_authorized"] is False
    assert item["external_spend_sar"] == 0


@pytest.mark.parametrize("change", [
    {"agent_id": "../escape"}, {"role": "admin"}, {"tools": ["Bash"]},
    {"tools": ["Read", "Read"]}, {"instructions": "short"},
    {"execution_authorized": True}
])
def test_invalid_or_privileged_proposals_block(change):
    item = sample()
    item.update(change)
    with pytest.raises((ValueError, TypeError)):
        proposal(item)


def request(server, method, path, payload=None, origin=None):
    headers = {"Content-Type": "application/json"} if payload is not None else {}
    if origin:
        headers["Origin"] = origin
    req = Request(f"http://127.0.0.1:{server.server_port}{path}",
                  method=method, headers=headers,
                  data=json.dumps(payload).encode() if payload is not None else None)
    try:
        with urlopen(req, timeout=3) as response:
            return response.status, response.read()
    except HTTPError as exc:
        return exc.code, exc.read()


def test_http_create_duplicate_list_and_origin():
    with LOCK:
        REGISTRY.clear()
    server = HTTPServer(("127.0.0.1", 0), Handler)
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        status, body = request(server, "GET", "/agents")
        assert status == 200 and b"Agent Factory" in body
        status, body = request(server, "POST", "/api/agents", sample())
        item = json.loads(body)
        assert status == 201 and item["agent_running"] is False
        status, _ = request(server, "POST", "/api/agents", sample())
        assert status == 409
        status, body = request(server, "GET", "/api/agents")
        assert status == 200
        assert json.loads(body)["agents"][0]["agent_id"] == "vx-test-01"
        status, _ = request(server, "POST", "/api/agents", sample("vx-test-02"), "https://evil.example")
        assert status == 403
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=3)
        with LOCK:
            REGISTRY.clear()
