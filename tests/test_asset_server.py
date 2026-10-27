import hashlib
import http.client
import json
from pathlib import Path
import shutil
import ssl
import subprocess
import threading

import pytest

from vxruntime.asset_server import AssetService, prepare_server

TOKEN = "A" * 48


@pytest.fixture()
def assets(tmp_path):
    folder = tmp_path / "assets"
    folder.mkdir()
    (folder / "asset.json").write_bytes(b'{"v":1}')
    (folder / "iphone image.png").write_bytes(b"\x89PNG\x00HELLO")
    (folder / "private.pem").write_bytes(b"PRIVATE")
    (folder / "huge.zip").write_bytes(b"A" * 300)
    (folder / "linked.txt").symlink_to(tmp_path / "secret.txt")
    return folder


def test_source_inventory(assets):
    service = AssetService(assets, TOKEN, max_bytes=100)
    manifest = service.manifest()
    assert manifest["server_kind"] == "DEVELOPMENT_MOCK"
    assert manifest["attestation"] == "NOT_PRODUCTION_VERIFIED"
    assert {x["name"] for x in manifest["items"]} == {"asset.json", "iphone image.png"}
    assert manifest["items"][0]["sha256"] == hashlib.sha256(b'{"v":1}').hexdigest()


@pytest.mark.parametrize("name", [
    "../bad.json", "../asset.json", "/etc/passwd", ".hidden", "linked.txt",
    "private.pem", "huge.zip", "a\\b.json", "%2e%2e/asset.json",
])
def test_disallowed_paths(assets, name):
    assert AssetService(assets, TOKEN, max_bytes=100)._read_asset(name) is None


def test_reject_short_token(assets):
    with pytest.raises(ValueError, match="TOKEN"):
        AssetService(assets, "short")


def test_tls_cert_required(assets, tmp_path):
    with pytest.raises(ValueError, match="TLS_CERT"):
        prepare_server("127.0.0.1", 0, AssetService(assets, TOKEN),
                       tmp_path / "absent", tmp_path / "absent.key")


@pytest.mark.skipif(shutil.which("openssl") is None, reason="openssl CLI unavailable")
def test_tls13_real_socket_and_auth(assets, tmp_path):
    cert = tmp_path / "cert.pem"
    key = tmp_path / "key.pem"
    subprocess.run([
        "openssl", "req", "-x509", "-newkey", "rsa:2048", "-nodes", "-sha256",
        "-keyout", str(key), "-out", str(cert), "-days", "1", "-subj", "/CN=localhost",
        "-addext", "subjectAltName=DNS:localhost,IP:127.0.0.1",
    ], check=True, capture_output=True)
    srv = prepare_server("127.0.0.1", 0, AssetService(assets, TOKEN, max_bytes=100), cert, key)
    thread = threading.Thread(target=srv.serve_forever, daemon=True)
    thread.start()
    try:
        context = ssl.create_default_context(cafile=str(cert))
        context.minimum_version = ssl.TLSVersion.TLSv1_3
        context.maximum_version = ssl.TLSVersion.TLSv1_3

        def get(path, authorized):
            conn = http.client.HTTPSConnection("localhost", srv.server_port, context=context, timeout=3)
            headers = {"Authorization": "Bearer " + TOKEN} if authorized else {}
            conn.request("GET", path, headers=headers)
            response = conn.getresponse()
            body, headers = response.read(), dict(response.getheaders())
            conn.close()
            return response.status, body, headers

        status, _, _ = get("/v1/health", False)
        assert status == 401
        status, body, _ = get("/v1/health", True)
        assert status == 200 and json.loads(body)["connectivity_verified"] is False
        status, body, headers = get("/v1/assets/asset.json", True)
        assert status == 200 and body == b'{"v":1}'
        assert headers["X-Artifact-SHA256"] == hashlib.sha256(body).hexdigest()
        status, _, _ = get("/v1/assets/%2e%2e%2fprivate.pem", True)
        assert status in (400, 404)
        status, body, _ = get("/v1/manifest", True)
        assert status == 200 and json.loads(body)["schema"] == "VX.ASSET.MANIFEST.v1"
    finally:
        srv.shutdown()
        srv.server_close()
        thread.join(timeout=3)
