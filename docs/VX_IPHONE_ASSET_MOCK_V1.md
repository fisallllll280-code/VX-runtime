# VX iPhone Asset Mock — Developer Runtime v1

**Identity:** `VX.ASSET.MOCK.001` (new proposed identifier; not confirmed historical VX-001…VX-657).  
**Owner:** VX-runtime. VAIXLNS canonical admission separate.  
**State:** Development-only. Physical iPhone and production server connectivity: **NOT VERIFIED**.

## Scope
Read-only HTTPS/TLS 1.3 asset preview endpoint. It can serve a bounded set of allowlisted files with a JSON manifest containing SHA-256 hashes. It does not run models, build iOS apps, push files to an iPhone, publish release updates, or make canonical decisions.

## Local quick start
Python 3.10+ with TLS 1.3-capable OpenSSL, `openssl` CLI for generating a dev-only certificate.

```sh
mkdir -p .vx-dev-certs vx_iphone_assets
python -c 'import secrets; print(secrets.token_urlsafe(32))'
# Place token output into VX_ASSET_TOKEN privately; never commit it.
export VX_ASSET_TOKEN="SET_YOUR_RANDOM_TOKEN"
openssl req -x509 -newkey rsa:2048 -sha256 -nodes -days 1 \
  -keyout .vx-dev-certs/localhost.key -out .vx-dev-certs/localhost.crt \
  -subj '/CN=localhost' -addext 'subjectAltName=DNS:localhost,IP:127.0.0.1'
chmod 600 .vx-dev-certs/localhost.key
python -m vxruntime.asset_server --assets ./vx_iphone_assets --bind 127.0.0.1 \
  --port 49152 --cert .vx-dev-certs/localhost.crt --key .vx-dev-certs/localhost.key
```

In another shell with same `VX_ASSET_TOKEN`:
```sh
curl --cacert .vx-dev-certs/localhost.crt \
  -H "Authorization: Bearer $VX_ASSET_TOKEN" \
  https://localhost:49152/v1/manifest
```
Do not use `-k` or disable certificate validation. Loopback binding does not make a server reachable from a physical phone. LAN binding requires `VX_ALLOW_LAN_BIND=I_ACCEPT_THE_RISK`, a host address with a matching trusted certificate, and restrictive firewall; do not expose this development mock publicly.

## Protocol
- `GET /v1/health` requires Bearer auth; returns `mock_ready` and `connectivity_verified:false`.
- `GET /v1/manifest` returns filenames, byte sizes, SHA-256 and paths.
- `GET /v1/assets/<one filename>` returns exact bytes and `X-Artifact-SHA256`.
- `POST` always returns 405; no uploads or mutation.
- File size bound defaults to 16 MiB. Dotfiles, traversal, symlinks and disallowed suffixes are rejected.

## Apple compatibility
Use the default HTTPS protection in ATS. Do not add an `NSAllowsArbitraryLoads` exception. Configure `NSLocalNetworkUsageDescription` when connecting to local hosts, and add Bonjour services only if browsing is used. The iPhone must trust the certificate chain and hostname / SAN; do not install or ship the sample localhost certificate as a production trust anchor. `example.com` is reserved documentation space, not your deployment host.

## Verification commands
```sh
python -m pytest -q tests/test_asset_server.py
python -m pytest -q
```
The suite includes a temporary localhost certificate, TLS 1.3 HTTPS client/server handshake, token validation, malicious-path rejection, byte-for-byte match and digest check. CI acceptance alone does **not** prove an iPhone-connected service.

## Production security gaps
This mock has no persistent audit trail, no signed release metadata (TUF or equivalent), no server request quotas, no reverse-proxy isolation, no certificate lifecycle automation, no signed integrity receipt, no iOS device attestation and no recovery/rollback proof. File path checks are not hardened against all concurrent filesystem races. Use an immutable asset snapshot and dedicated hardened file serving stack before production; never serve sensitive assets with this mock.

## VAIXLNS Federation
Register the proposed capability with evidence: `repository=VX-runtime`, source commit SHA, test run, TLS proof, artifact SHA-256, developer certificate metadata, requested target platform, `admission=NOT_ADMITTED`. Existing VAIXLNS `Ω.000`, index histories and source files are never implicitly rewritten.

## External specifications
Python TLS: https://docs.python.org/3/library/ssl.html
Apple ATS: https://developer.apple.com/documentation/security/preventing-insecure-network-connections
Apple local network: https://developer.apple.com/documentation/bundleresources/information-property-list/nslocalnetworkusagedescription
IANA example domains: https://www.iana.org/domains/reserved
TUF metadata: https://theupdateframework.io/docs/metadata/
