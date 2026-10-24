"""VX local mobile app: loopback-only demonstration of governed execution."""
from __future__ import annotations
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import json
from .core import VXRuntime, ExecutionPolicy

PAGE = Path(__file__).resolve().parents[1] / "web" / "vx-app" / "index.html"
runtime = VXRuntime(policy=ExecutionPolicy(allowed_capabilities=frozenset({"math.add"})))


class Handler(BaseHTTPRequestHandler):
    def respond(self, status: int, payload: dict):
        body = json.dumps(payload, sort_keys=True, default=str).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Content-Security-Policy", "default-src 'none'")
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if self.path == "/":
            body = PAGE.read_bytes()
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-store")
            self.send_header("X-Content-Type-Options", "nosniff")
            self.end_headers()
            self.wfile.write(body)
        elif self.path == "/api/status":
            self.respond(200, {"service": "VX local app", "runtime": "RUNNING_LOCAL",
                "ledger_valid": runtime.verify(), "execution_count": len(runtime.history),
                "external_models_connected": False, "github_federation_live": False,
                "production_ready": False})
        else:
            self.respond(404, {"error": "NOT_FOUND"})

    def do_POST(self):
        if self.path != "/api/demo":
            return self.respond(404, {"error": "NOT_FOUND"})
        if self.headers.get("Origin") not in (None, "http://127.0.0.1:8765", "http://localhost:8765"):
            return self.respond(403, {"error": "ORIGIN_DENIED"})
        if self.headers.get("Content-Type", "").split(";")[0].strip() != "application/json":
            return self.respond(415, {"error": "JSON_REQUIRED"})
        try:
            size = int(self.headers.get("Content-Length", "0"))
            if not 0 < size <= 1024:
                return self.respond(413, {"error": "SIZE_DENIED"})
            data = json.loads(self.rfile.read(size))
            if type(data) is not dict or type(data.get("a")) is not int or type(data.get("b")) is not int:
                return self.respond(400, {"error": "INVALID_INPUT"})
            if abs(data["a"]) > 100000 or abs(data["b"]) > 100000:
                return self.respond(400, {"error": "OUT_OF_BOUNDS"})
            execution_id = f"demo-{len(runtime.history)+1}"
            result = runtime.execute(execution_id, "math.add", data,
                                     lambda p: p["a"] + p["b"])
            self.respond(200, {"execution_id": execution_id, "status": result.status.value,
                "output": result.output, "input_digest": result.input_hash,
                "output_digest": result.output_hash,
                "ledger_valid": runtime.verify(), "demo_only": True})
        except (ValueError, json.JSONDecodeError):
            self.respond(400, {"error": "INVALID_JSON"})


def main():
    server = ThreadingHTTPServer(("127.0.0.1", 8765), Handler)
    print("VX local app: http://127.0.0.1:8765", flush=True)
    server.serve_forever()


if __name__ == "__main__":
    main()
