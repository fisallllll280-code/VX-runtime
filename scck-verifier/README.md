# SCCK Proof-Gated Asset Verifier v0.1

**Boundary:** This is a `no_std`, allocation-free, network-independent Rust verification primitive inside VX-runtime. This is NOT a complete Sovereign Computational Kernel, operating system, hosted service, formal mathematical proof engine, TUF implementation, or production iPhone installer.

## Included
- Deterministic fixed-byte SCCKAS01 envelope (148-byte signed metadata, 64-byte Ed25519 signature, payload).
- `verify_strict` against an externally authorized trusted publisher key; the key ID is SHA-256 of the configured verifying key.
- SHA-256 of the entire payload (not a Merkle root).
- Nonzero expiration check supplied by a trusted wall clock; tenant/environment ID binding.
- Sequence+previous-envelope hash checks to reject replay/rollback once prior state has been committed.
- Pure `verify_and_prepare`: no input mutation, no I/O, no heap, no canonical admission. Returns a candidate transition and receipt for the host to persist atomically.
- Cross-platform Rust target intent, and CI for host tests and wasm32-unknown-unknown compilation.

## Build
Requires Rust >=1.85 and network access for first dependency resolution.

```sh
cargo test --manifest-path scck-verifier/Cargo.toml --all-targets
rustup target add wasm32-unknown-unknown
cargo build --manifest-path scck-verifier/Cargo.toml --target wasm32-unknown-unknown --release
```

The fixture's private key `[7;32]` in tests is public and MUST NEVER be used outside tests.

## Protocol layout
All numeric fields little-endian. No Rust struct memory layout is used.

| Offset | Bytes | Field |
|---:|---:|---|
| 0 | 8 | ASCII `SCCKAS01` |
| 8 | 1 | version=1 |
| 9 | 1 | flags=0 |
| 10 | 2 | reserved=0 |
| 12 | 8 | sequence, strictly previous+1 |
| 20 | 8 | expires_at_unix |
| 28 | 8 | payload byte length |
| 36 | 32 | SHA-256(payload) |
| 68 | 32 | previous envelope SHA-256 |
| 100 | 32 | SHA-256(authorized verifying pubkey) |
| 132 | 16 | environment identifier |
| 148 | 64 | Ed25519 signature on DOMAIN || bytes 0..147 |
| 212 | variable, max 8 MiB | payload bytes |

DOMAIN exact bytes: `VAIXLNS/SCCK/ASSET/V1\0`. This is **application-level signed-message prefixing**, not Ed25519ctx.

Envelope digest is SHA-256(bytes 0..211), binding signed metadata and signature. SHA-256 on the payload is intentionally called a **payload hash** and not a cryptographic Merkle proof. No Merkle inclusion proof is defined.

## Host contract and transaction safety

The embedder MUST supply the public key from an **independently authenticated and authorized** publisher policy, a trusted current timestamp, an expected environment ID, and a durable monotonic `SequenceState`. No trusted key may be accepted from the unverified envelope itself.

```text
Receive untrusted bytes
    -> Parse canonical header and enforce bounds
    -> Bind environment and authorized publisher
    -> Verify strict Ed25519 over signed metadata
    -> SHA-256 exact payload
    -> Enforce trusted expiry, sequence, and predecessor
    -> PreparedTransition (candidate only)
    -> Host atomic durable commit of asset+state+receipt
    -> VX may authorize downstream use via separate execution policy
```

The pure gate **cannot** guarantee crash durability or global replay prevention. If the host loses/replaces its saved SequenceState, an older valid signed package can be accepted. State must be committed transactionally and anti-rollback state protected against tampering. A signature cannot prove the physical world, correctness of model output or formal validity of arbitrary state transitions.

## Fault model
- Untrusted adapter or HTTPS transport cannot bypass signature, key authorization, environment or payload checks inside this verifier.
- A compromised publisher private key, malicious authorized content, host memory corruption, compromised boot chain, manipulated host clock, or rollback of trusted durable state remain threats.
- No automatic fallback to weaker verification; no `allow-unsigned` mode.
- Fail closed on syntax, length, publisher, signature, environment, expiry, hash, sequence or previous hash errors.
- External adapter failure does not alter accepted canonical state; independent state store durability is still necessary.

## Open security engineering work (before production)
1. TUF / equivalent: root, targets, snapshot and timestamp roles, thresholds, expiry, key rotation/revocation, snapshot consistency.
2. Trusted clock and durable atomic state+asset commit, crash recovery tests, power-loss fault injection and tamper-resistant monotonic rollback counter.
3. Key provisioning/attestation, allowlists per asset class and issuer, key compromise response and decommissioning.
4. Streaming verification for large assets; eliminate time-of-check/time-of-use races, enforce immutability of verified bytes.
5. Integration with iOS Swift bridge and Linux/Windows/macOS/Linux-edge runtimes; actual device deployment, protected storage and network capability permissions.
6. Formal property specification and model checking of transition safety, fuzzing, supply-chain audit, pin Cargo.lock and reproducible build artifacts.
7. Multiple signatures and threshold policy when required; this v0.1 trusts exactly one key per verification request.

## Documentation basis
- https://docs.rs/ed25519-dalek/3.0.0/ed25519_dalek/
- https://www.rfc-editor.org/rfc/rfc8032
- https://theupdateframework.io/docs/metadata/

**Promotion:** This package is REVIEW/TEST only and does not modify Ω.000 or declare VX runtime VERIFIED.
