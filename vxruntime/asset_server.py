"""Development-only HTTPS/TLS 1.3 read-only asset server for VX iPhone clients.

A mock is not proof of an iPhone connection, trusted publisher, or production deployment.
"""
from __future__ import annotations

import argparse
import hashlib
import hmac
import json
import logging
import mimetypes
import os
from pathlib import Path
import ssl
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import quote, unquote, urlsplit

LOG = logging.getLogger("vx.asset_mock")
DEFAULT_MAX_ASSET_BYTES = 16 * 1024 * 1024
ALLOWED_SUFFIXES = frozenset({".json", ".txt", ".png", ".jpg", ".jpeg", ".webp", ".zip", ".bin"})


class AssetService:
    def __init__(self, directory: Path, token: str, max_bytes: int = DEFAULT_MAX_ASSET_BYTES):
        self.directory = directory.resolve(strict=True)
        if not self.directory.is_dir():
            raise ValueError("ASSET_DIR_NOT_DIRECTORY")
        if not token or len(token) < 24:
            raise ValueError("TOKEN_MUST_BE_AT_LEAST_24_CHARS")
        if max_bytes < 1:
            raise ValueError("BAD_ASSET_LIMIT")
        self.token = token
        self.max_bytes = max_bytes

    def _read_asset(self, name: str) -> bytes | None:
        # Single path component, no symlinks/dotfiles, allowlisted formats and bounded bytes.
        if not name or name in {".", ".."} or name.startswith(".") or "/" in name or "\\" in name or "\x00" in name:
            return None
        candidate = self.directory / name
        if candidate.suffix.lower() not in ALLOWED_SUFFIXES or candidate.is_symlink() or not candidate.is_file():
            return None
        if not candidate.resolve().is_relative_to(self.directory):
            return None
        if candidate.stat().st_size > self.max_bytes:
            return None
        with candidate.open("rb") as source:
            data = source.read(self.max_bytes + 1)
        return data if len(data) <= self.max_bytes else None

    def manifest(self) -> dict:
        items = []
        for path in sorted(self.directory.iterdir(), key=lambda p: p.name):
            data = self._read_asset(path.name)
            if data is None:
                continue
            items.append({
                "name": path.name, "sha256": hashlib.sha256(data).hexdigest(),
                "bytes": len(data), "path": "/v1/assets/" + quote(path.name, safe=""),
            })
        return {
            "schema": "VX.ASSET.MANIFEST.v1", "server_kind": "DEVELOPMENT_MOCK",
            "items": items, "attestation": "NOT_PRODUCTION_VERIFIED",
        }


def make_handler(service: AssetService):
    class Handler(BaseHTTPRequestHandler):
        server_version = "VXAssetMock/1.0"
        sys_version = ""
        protocol_version = "HTTP/1.1"

        def _send(self, status: HTTPStatus, data: bytes, content_type: str, *, sha256: str | None = None) -> None:
            self.send_response(status)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(data)))
            self.send_header("Cache-Control", "no-store")
            self.send_header("X-Content-Type-Options", "nosniff")
            self.send_header("X-VAIXLNS-Protocol", "VX-ASSET-MOCK-v1")
            if sha256 is not None:
                self.send_header("X-Artifact-SHA256", sha256)
            self.end_headers()
            self.wfile.write(data)

        def _json(self, status: HTTPStatus, value: dict) -> None:
            encoded = (json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")
            self._send(status, encoded, "application/json; charset=utf-8")

        def do_GET(self) -> None:
            provided = self.headers.get("Authorization", "")
            if not hmac.compare_digest(provided, "Bearer " + service.token):
                self._json(HTTPStatus.UNAUTHORIZED, {"error": "AUTH_REQUIRED"})
                return
            request = urlsplit(self.path)
            if request.query or request.fragment:
                self._json(HTTPStatus.BAD_REQUEST, {"error": "UNSUPPORTED_QUERY"})
                return
            if request.path == "/v1/health":
                self._json(HTTPStatus.OK, {
                    "status": "mock_ready", "protocol": "VX-ASSET-MOCK-v1",
                    "connectivity_verified": False, "deployment": "development_only",
                })
                return
            if request.path == "/v1/manifest":
                self._json(HTTPStatus.OK, service.manifest())
                return
            prefix = "/v1/assets/"
            if not request.path.startswith(prefix):
                self._json(HTTPStatus.NOT_FOUND, {"error": "NOT_FOUND"})
                return
            encoded = request.path[len(prefix):]
            if "%" in unquote(encoded):
                self._json(HTTPStatus.BAD_REQUEST, {"error": "ENCODING_UNSUPPORTED"})
                return
            try:
                name = unquote(encoded, errors="strict")
            except UnicodeDecodeError:
                self._json(HTTPStatus.BAD_REQUEST, {"error": "BAD_PATH_ENCODING"})
                return
            data = service._read_asset(name)
            if data is None:
                self._json(HTTPStatus.NOT_FOUND, {"error": "ASSET_NOT_FOUND"})
                return
            mime = mimetypes.guess_type(name)[0] or "application/octet-stream"
            self._send(HTTPStatus.OK, data, mime, sha256=hashlib.sha256(data).hexdigest())

        def do_POST(self) -> None:
            self._json(HTTPStatus.METHOD_NOT_ALLOWED, {"error": "READ_ONLY"})

        def log_message(self, fmt: str, *args) -> None:
            # Do not log token or untrusted path/query.
            LOG.info("%s response served", self.client_address[0])

    return Handler


def prepare_server(bind: str, port: int, service: AssetService, cert: Path, key: Path) -> ThreadingHTTPServer:
    if not cert.is_file() or not key.is_file():
        raise ValueError("TLS_CERT_AND_KEY_REQUIRED")
    context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    context.minimum_version = ssl.TLSVersion.TLSv1_3
    context.maximum_version = ssl.TLSVersion.TLSv1_3
    context.load_cert_chain(certfile=str(cert), keyfile=str(key))
    server = ThreadingHTTPServer((bind, port), make_handler(service))
    server.daemon_threads = True
    server.socket = context.wrap_socket(server.socket, server_side=True)
    return server


def main() -> int:
    parser = argparse.ArgumentParser(description="VX iPhone read-only TLS1.3 development mock")
    parser.add_argument("--assets", type=Path, default=Path("./vx_iphone_assets"))
    parser.add_argument("--bind", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=49152)
    parser.add_argument("--cert", type=Path, required=True)
    parser.add_argument("--key", type=Path, required=True)
    parser.add_argument("--token-env", default="VX_ASSET_TOKEN")
    args = parser.parse_args()
    token = os.environ.get(args.token_env, "")
    if args.bind not in {"127.0.0.1", "::1", "localhost"} and os.environ.get("VX_ALLOW_LAN_BIND") != "I_ACCEPT_THE_RISK":
        parser.error("LAN_BIND_REQUIRES_EXPLICIT_OPT_IN_AND_NETWORK_RESTRICTIONS")
    if not 0 <= args.port <= 65535:
        parser.error("BAD_PORT")
    logging.basicConfig(level=logging.INFO, format="[%(asctime)s] [VX-ASSET-MOCK] [%(levelname)s] %(message)s")
    try:
        service = AssetService(args.assets, token)
        server = prepare_server(args.bind, args.port, service, args.cert, args.key)
    except (OSError, ValueError, ssl.SSLError) as error:
        LOG.error("Cannot start TLS development mock: %s", type(error).__name__)
        return 2
    LOG.info("TLS1.3 development mock on bind=%s port=%s; no iPhone connectivity claim", args.bind, server.server_port)
    try:
        server.serve_forever(poll_interval=0.1)
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
