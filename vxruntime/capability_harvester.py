"""Derived capability inventory and bounded evidence; never canonical authority.

The initial smoke test hashes inert artifact bytes in a fresh Python process.
It neither imports third-party code nor claims to sandbox arbitrary programs.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
import hashlib
import json
import re
import sqlite3
import subprocess
import sys
import tempfile
from uuid import uuid4

from .admission import AdmissionDecision, AdmissionStatus, ProofBundle, evaluate_admission
from .core import Execution, ExecutionStatus, VXRuntime, canonical_json, digest

SMOKE = "capability.artifact.smoke.v1"
MAX_BYTES = 1024 * 1024


@dataclass(frozen=True)
class CapabilityPassport:
    capability_id: str
    version: str
    license: str
    source_url: str
    source_commit: str
    artifact_sha256: str
    contract_ref: str
    permissions: tuple[str, ...] = ()
    dependencies: tuple[tuple[str, str], ...] = ()
    schema_version: int = 1

    @property
    def fingerprint(self) -> str:
        return digest(asdict(self))


@dataclass(frozen=True)
class CompatibilityPolicy:
    """Host-supplied policy snapshot, not authority inferred from a passport."""
    revision: str
    allowed_licenses: frozenset[str]
    allowed_permissions: frozenset[str] = frozenset()


def check_passport(p: CapabilityPassport, policy: CompatibilityPolicy) -> tuple[str, ...]:
    reasons = []
    for name in ("capability_id", "version", "license", "source_url", "contract_ref"):
        if not isinstance(getattr(p, name), str) or not getattr(p, name).strip():
            reasons.append("REQUIRED:" + name)
    if p.schema_version != 1:
        reasons.append("UNKNOWN_SCHEMA")
    if not isinstance(p.source_commit, str) or not re.fullmatch(r"[0-9a-f]{40}", p.source_commit):
        reasons.append("UNPINNED_SOURCE")
    if not isinstance(p.artifact_sha256, str) or not re.fullmatch(r"[0-9a-f]{64}", p.artifact_sha256):
        reasons.append("INVALID_ARTIFACT_DIGEST")
    if not isinstance(p.source_url, str) or not p.source_url.startswith("https://"):
        reasons.append("SOURCE_SCHEME_DENIED")
    if not policy.revision:
        reasons.append("POLICY_REVISION_MISSING")
    if p.license not in policy.allowed_licenses:
        reasons.append("LICENSE_DENIED")
    if not set(p.permissions) <= policy.allowed_permissions:
        reasons.append("PERMISSION_DENIED")
    if any(len(d) != 2 or not all(isinstance(v, str) and v for v in d) for d in p.dependencies):
        reasons.append("INVALID_DEPENDENCY")
    return tuple(reasons)


class CapabilityRegistry:
    """SQLite projection for Nexus consumption, with immutable version identities.

    Local receipts and inventories are derived evidence, not an execution ledger
    or independent source of governance. Callers own the database access boundary.
    """
    def __init__(self, path: str):
        self.db = sqlite3.connect(path)
        self.db.execute("PRAGMA foreign_keys = ON")
        self.db.executescript("""
            CREATE TABLE IF NOT EXISTS passports (
              capability_id TEXT NOT NULL, version TEXT NOT NULL,
              fingerprint TEXT NOT NULL UNIQUE, body TEXT NOT NULL,
              PRIMARY KEY(capability_id, version));
            CREATE TABLE IF NOT EXISTS relationships (
              passport TEXT NOT NULL REFERENCES passports(fingerprint),
              dependency_id TEXT NOT NULL, dependency_version TEXT NOT NULL,
              PRIMARY KEY(passport, dependency_id, dependency_version));
            CREATE TABLE IF NOT EXISTS receipts (
              execution_id TEXT PRIMARY KEY, passport TEXT NOT NULL
                REFERENCES passports(fingerprint), body TEXT NOT NULL,
              fingerprint TEXT NOT NULL);
        """)

    def close(self):
        self.db.close()

    def register(self, passport: CapabilityPassport, policy: CompatibilityPolicy):
        reasons = check_passport(passport, policy)
        if reasons:
            raise ValueError(",".join(reasons))
        existing = self.db.execute(
            "SELECT fingerprint FROM passports WHERE capability_id=? AND version=?",
            (passport.capability_id, passport.version),
        ).fetchone()
        if existing and existing[0] != passport.fingerprint:
            raise ValueError("IMMUTABLE_VERSION_CONFLICT")
        with self.db:
            self.db.execute("INSERT OR IGNORE INTO passports VALUES (?,?,?,?)", (
                passport.capability_id, passport.version, passport.fingerprint,
                canonical_json(asdict(passport)),
            ))
            self.db.executemany("INSERT OR IGNORE INTO relationships VALUES (?,?,?)", (
                (passport.fingerprint, dep, version) for dep, version in passport.dependencies
            ))

    def get(self, capability_id: str, version: str) -> CapabilityPassport:
        row = self.db.execute(
            "SELECT body, fingerprint FROM passports WHERE capability_id=? AND version=?",
            (capability_id, version),
        ).fetchone()
        if row is None:
            raise KeyError((capability_id, version))
        body = json.loads(row[0])
        body["permissions"] = tuple(body["permissions"])
        body["dependencies"] = tuple(tuple(d) for d in body["dependencies"])
        p = CapabilityPassport(**body)
        if p.fingerprint != row[1]:
            raise ValueError("PASSPORT_INTEGRITY_FAILURE")
        return p

    def record(self, execution_id: str, passport: str, receipt: dict):
        with self.db:
            self.db.execute("INSERT INTO receipts VALUES (?,?,?,?)", (
                execution_id, passport, canonical_json(receipt), digest(receipt),
            ))

    def receipt(self, execution_id: str) -> dict:
        row = self.db.execute("SELECT body, fingerprint FROM receipts WHERE execution_id=?", (execution_id,)).fetchone()
        if row is None:
            raise KeyError(execution_id)
        body = json.loads(row[0])
        if digest(body) != row[1]:
            raise ValueError("RECEIPT_INTEGRITY_FAILURE")
        return body


class EvidenceRunner:
    """Runs only a fixed inert-byte smoke operation through the existing VX core.

    The runtime, policy and ledger are supplied by the host. No grant is created
    here. A successful smoke result still needs external VV review and authority.
    """
    def __init__(self, registry: CapabilityRegistry, runtime: VXRuntime, policy: CompatibilityPolicy):
        self.registry, self.runtime, self.policy = registry, runtime, policy

    def run(self, capability_id: str, version: str, artifact: bytes, *, timeout: float = 5) -> Execution:
        if type(artifact) is not bytes or len(artifact) > MAX_BYTES:
            raise ValueError("ARTIFACT_SIZE_OR_TYPE_DENIED")
        if not 0 < timeout <= 30:
            raise ValueError("INVALID_TIMEOUT")
        p = self.registry.get(capability_id, version)
        # Bind the actual bytes, passport and host policy into VX's replay inputs.
        inputs = {"passport": p.fingerprint, "artifact_hex": artifact.hex(),
                  "policy": asdict(self.policy) | {
                      "allowed_licenses": sorted(self.policy.allowed_licenses),
                      "allowed_permissions": sorted(self.policy.allowed_permissions)},
                  "timeout": timeout}

        def worker(captured):
            reasons = check_passport(p, self.policy)
            if reasons:
                raise ValueError(",".join(reasons))
            # Dependencies are inventory links only; none are implicitly activated.
            for dep, dep_version in p.dependencies:
                self.registry.get(dep, dep_version)
            payload = bytes.fromhex(captured["artifact_hex"])
            if hashlib.sha256(payload).hexdigest() != p.artifact_sha256:
                raise ValueError("ARTIFACT_DIGEST_MISMATCH")
            script = (
                "import sys,hashlib,json; b=sys.stdin.buffer.read(1048577); "
                "print(json.dumps({'sha256':hashlib.sha256(b).hexdigest(),'size':len(b)}))"
            )
            # Only trusted fixed code executes. Empty environment and temporary cwd
            # prevent incidental configuration use; these are not an OS sandbox.
            with tempfile.TemporaryDirectory(prefix="vx-smoke-") as cwd:
                result = subprocess.run(
                    [sys.executable, "-I", "-S", "-c", script], input=payload,
                    stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                    timeout=captured["timeout"], check=True, cwd=cwd, env={},
                )
            observed = json.loads(result.stdout)
            if observed != {"sha256": p.artifact_sha256, "size": len(payload)}:
                raise ValueError("SMOKE_OUTPUT_MISMATCH")
            return {"passport": p.fingerprint, "artifact": observed, "test": "inert_artifact_smoke"}

        execution = self.runtime.execute(str(uuid4()), SMOKE, inputs, worker)
        receipt = {
            "execution": asdict(execution), "source_revision": p.source_commit,
            "observed_at": datetime.now(timezone.utc).isoformat(),
            "passport": p.fingerprint, "policy_revision": self.policy.revision,
            "events": [asdict(e) for e in self.runtime.ledger.events
                       if e.execution_id == execution.execution_id],
            "ledger_valid": self.runtime.verify(),
            "risk": "REVIEW_REQUIRED" if p.permissions else "LOW_INERT_SMOKE_ONLY",
            "integration_status": "PENDING SOURCE VALIDATION",
            "canonical_write": False, "independent_verification": False,
        }
        self.registry.record(execution.execution_id, p.fingerprint, receipt)
        return execution

    def review(self, execution: Execution, proof: ProofBundle | None, *,
               trusted_verifiers: frozenset[str]) -> AdmissionDecision:
        """Local eligibility only: delegate VV checks; never promotes canonical state."""
        receipt = self.registry.receipt(execution.execution_id)
        if receipt["execution"]["input_hash"] != execution.input_hash or receipt["execution"]["output_hash"] != execution.output_hash:
            return AdmissionDecision(AdmissionStatus.BLOCKED, ("RECEIPT_EXECUTION_MISMATCH",))
        if proof is not None and (proof.source_commit != receipt["source_revision"] or
                                  proof.evidence_hashes.get("capability_smoke") != digest(receipt)):
            return AdmissionDecision(AdmissionStatus.BLOCKED, ("PROOF_PASSPORT_EVIDENCE_MISMATCH",))
        return evaluate_admission(execution, self.runtime.ledger, proof,
                                  trusted_verifiers=trusted_verifiers)
