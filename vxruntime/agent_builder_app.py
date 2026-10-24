"""VX Agent Builder application: proposal-only, loopback, in-memory registry."""
from __future__ import annotations
from copy import deepcopy
import hashlib
from http.server import ThreadingHTTPServer
import json
import re
from pathlib import Path
from threading import RLock
from .mobile_app import Handler as BaseHandler

HTML = Path(__file__).resolve().parents[1] / "web/vx-app/agents.html"
LOCK = RLock()
REGISTRY: dict[str, dict] = {}
ROLES = frozenset({"coding", "research", "testing", "security", "design", "integration"})
TOOL_OPTIONS = frozenset({"Read", "Grep", "Glob"})
ID_RE = re.compile(r"^[a-z][a-z0-9-]{2,39}$")


def proposal(payload: object) -> dict:
    if type(payload) is not dict or set(payload) != {"agent_id", "role", "instructions", "tools"}:
        raise ValueError("INVALID_SCHEMA")
    identifier, role, instructions, tools = (
        payload["agent_id"], payload["role"], payload["instructions"], payload["tools"])
    if type(identifier) is not str or not ID_RE.fullmatch(identifier):
        raise ValueError("INVALID_AGENT_ID")
    if role not in ROLES:
        raise ValueError("UNKNOWN_ROLE")
    if type(instructions) is not str or not (10 <= len(instructions.strip()) <= 2000):
        raise ValueError("INVALID_INSTRUCTIONS")
    if type(tools) is not list or len(tools) > 3 or len(set(map(str, tools))) != len(tools) or any(t not in TOOL_OPTIONS for t in tools):
        raise ValueError("TOOLS_NOT_ALLOWLISTED")
    record = {"agent_id": identifier, "role": role, "instructions": instructions.strip(),
              "tools": sorted(tools), "status": "PROPOSED_NOT_RUNNING",
              "execution_authorized": False, "external_spend_sar": 0}
    record["digest_sha256"] = hashlib.sha256(json.dumps(
        record, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
    return record


class Handler(BaseHandler):
    def do_GET(self):
        if self.path == "/agents":
            data = HTML.read_bytes()
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(data)))
            self.send_header("Cache-Control", "no-store")
            self.send_header("X-Content-Type-Options", "nosniff")
            self.end_headers()
            self.wfile.write(data)
        elif self.path == "/api/agents":
            with LOCK:
                values = [{k: v for k, v in x.items() if k != "instructions"} for x in REGISTRY.values()]
            self.respond(200, {"agents": values, "execution_enabled": False, "persistent": False})
        else:
            super().do_GET()

    def do_POST(self):
        if self.path != "/api/agents":
            return super().do_POST()
        if self.headers.get("Origin") not in (None, "http://127.0.0.1:8765", "http://localhost:8765"):
            return self.respond(403, {"error": "ORIGIN_DENIED"})
        if self.headers.get("Content-Type", "").split(";")[0].strip() != "application/json":
            return self.respond(415, {"error": "JSON_REQUIRED"})
        try:
            size = int(self.headers.get("Content-Length", "0"))
            if size < 2 or size > 4096:
                return self.respond(413, {"error": "SIZE_DENIED"})
            data = json.loads(self.rfile.read(size))
            item = proposal(data)
            with LOCK:
                if item["agent_id"] in REGISTRY:
                    return self.respond(409, {"error": "AGENT_ID_EXISTS"})
                REGISTRY[item["agent_id"]] = deepcopy(item)
            self.respond(201, {"agent": item, "persisted": False, "agent_running": False})
        except (ValueError, TypeError) as exc:
            self.respond(400, {"error": str(exc)})


def main():
    server = ThreadingHTTPServer(("127.0.0.1", 8765), Handler)
    print("VX Agent Builder: http://127.0.0.1:8765/agents", flush=True)
    server.serve_forever()


if __name__ == "__main__":
    main()
