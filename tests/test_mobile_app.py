"""Loopback app HTTP smoke tests, with no external services."""
import json
import threading
from http.server import HTTPServer
from urllib.request import Request, urlopen
from urllib.error import HTTPError
from vxruntime.mobile_app import Handler, PAGE


def request(server, path, data=None, origin=None):
    headers = {"Content-Type": "application/json"} if data is not None else {}
    if origin:
        headers["Origin"] = origin
    req = Request(f"http://127.0.0.1:{server.server_port}{path}",
                  data=json.dumps(data).encode() if data is not None else None,
                  headers=headers, method="POST" if data is not None else "GET")
    try:
        with urlopen(req, timeout=3) as response:
            return response.status, response.read()
    except HTTPError as e:
        return e.code, e.read()


def test_vx_mobile_app_contract():
    assert PAGE.exists()
    server = HTTPServer(("127.0.0.1", 0), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        status, body = request(server, "/")
        assert status == 200 and b"VX" in body
        status, body = request(server, "/api/status")
        state = json.loads(body)
        assert status == 200 and state["ledger_valid"] is True
        assert state["external_models_connected"] is False
        assert state["production_ready"] is False
        status, body = request(server, "/api/demo", {"a": 21, "b": 21})
        receipt = json.loads(body)
        assert status == 200 and receipt["output"] == 42
        assert receipt["ledger_valid"] is True and len(receipt["input_digest"]) == 64
        status, body = request(server, "/api/demo", {"a": 1, "b": 1}, "https://evil.example")
        assert status == 403
        status, body = request(server, "/api/demo", {"a": "x", "b": 1})
        assert status == 400
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=3)
