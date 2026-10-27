"""Local SCCK reference boundary; no installer, network listener or key issuer.

Only an authenticated trusted host may provision policy or invoke this library.
Python object possession is not authentication. SQLite must be private and on a
local filesystem. The existing VX core executes only the fixed inspection worker.
"""
from __future__ import annotations

from contextlib import contextmanager
from dataclasses import asdict, dataclass
import hashlib
import json
import re
import sqlite3
import time
from typing import Callable

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey

from .core import Event, ExecutionPolicy, ExecutionStatus, VXRuntime

OPERATION = "scck.inspect.v1"
MAX_PAYLOAD = 1024 * 1024
MAX_PROOF = 32
MAX_INTEGER = 2**63 - 1


class SCCKError(ValueError):
    """Stable rejection code, deliberately without payload or exception details."""


def _json(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=True, allow_nan=False)


def _text(value):
    if type(value) is not str or re.fullmatch(r"[A-Za-z0-9_.:-]{1,96}", value) is None:
        raise SCCKError("INVALID_IDENTIFIER")


def _integer(value):
    if type(value) is not int or not 0 <= value <= MAX_INTEGER:
        raise SCCKError("INVALID_INTEGER")


def _hash(value):
    if type(value) is not str or re.fullmatch(r"[0-9a-f]{64}", value) is None:
        raise SCCKError("INVALID_HASH")


@dataclass(frozen=True)
class Manifest:
    package_id: str
    device_id: str
    component: str
    version: int
    epoch: int
    expires_at: int
    payload_hash: str
    merkle_root: str
    operation: str = OPERATION
    protocol: str = "VAIXLNS-SCCK-REFERENCE-1"

    def validate(self):
        for value in (self.package_id, self.device_id, self.component):
            _text(value)
        for value in (self.version, self.epoch, self.expires_at):
            _integer(value)
        for value in (self.payload_hash, self.merkle_root):
            _hash(value)
        if self.operation != OPERATION or self.protocol != "VAIXLNS-SCCK-REFERENCE-1":
            raise SCCKError("UNSUPPORTED_PROTOCOL_OR_OPERATION")

    def signing_bytes(self):
        self.validate()
        # Fixed ASCII JSON fields, integers only; prefix is signed, not metadata.
        return b"VAIXLNS/SCCK/MANIFEST/REFERENCE-1\0" + _json(asdict(self)).encode("ascii")


@dataclass(frozen=True)
class Package:
    manifest: Manifest
    payload: bytes
    public_key: bytes
    signature: bytes
    merkle_path: tuple[bytes, ...] = ()


def merkle_leaf(payload_hash: str) -> bytes:
    _hash(payload_hash)
    return hashlib.sha256(b"VAIXLNS/SCCK/LEAF/1\0" + bytes.fromhex(payload_hash)).digest()


def merkle_parent(left: bytes, right: bytes) -> bytes:
    if type(left) is not bytes or type(right) is not bytes or len(left) != 32 or len(right) != 32:
        raise SCCKError("INVALID_MERKLE_NODE")
    a, b = sorted((left, right))
    return hashlib.sha256(b"VAIXLNS/SCCK/NODE/1\0" + a + b).digest()


def verify_package(package: Package) -> str:
    """Pure bounded verification outside the database write transaction."""
    m = package.manifest
    signed = m.signing_bytes()
    if type(package.payload) is not bytes or len(package.payload) > MAX_PAYLOAD:
        raise SCCKError("PAYLOAD_LIMIT")
    if type(package.public_key) is not bytes or len(package.public_key) != 32:
        raise SCCKError("INVALID_KEY")
    if type(package.signature) is not bytes or len(package.signature) != 64:
        raise SCCKError("INVALID_SIGNATURE")
    if type(package.merkle_path) is not tuple or len(package.merkle_path) > MAX_PROOF:
        raise SCCKError("PROOF_LIMIT")
    if hashlib.sha256(package.payload).hexdigest() != m.payload_hash:
        raise SCCKError("PAYLOAD_HASH_MISMATCH")
    try:
        Ed25519PublicKey.from_public_bytes(package.public_key).verify(package.signature, signed)
    except InvalidSignature:
        raise SCCKError("SIGNATURE_VERIFICATION_FAILED") from None
    current = merkle_leaf(m.payload_hash)
    for sibling in package.merkle_path:
        current = merkle_parent(current, sibling)
    if current.hex() != m.merkle_root:
        raise SCCKError("MERKLE_PROOF_INVALID")
    return hashlib.sha256(signed + package.public_key + package.signature).hexdigest()


class AdmissionStore:
    """Persistent acceptance + high-water mark + audit in one SQLite transaction.

    Configuration is a host administration surface, never an untrusted tool.
    One store may be reopened by independent processes. Unknown EXECUTING
    outcomes stay on HOLD and are never automatically retried or rolled back.
    """
    def __init__(self, database: str, *, clock: Callable[[], float] = time.time):
        if not database or database == ":memory:":
            raise SCCKError("DURABLE_DATABASE_REQUIRED")
        self.database, self.clock = database, clock
        with self._connection() as db:
            db.execute("PRAGMA journal_mode=WAL")
            db.executescript("""
                CREATE TABLE IF NOT EXISTS scck_policy (
                  scope TEXT PRIMARY KEY, revision INTEGER NOT NULL,
                  epoch INTEGER NOT NULL, root TEXT NOT NULL,
                  keys_json TEXT NOT NULL, revoked_json TEXT NOT NULL,
                  principal TEXT NOT NULL, grant_expires INTEGER NOT NULL);
                CREATE TABLE IF NOT EXISTS scck_highwater (
                  scope TEXT PRIMARY KEY, version INTEGER NOT NULL);
                CREATE TABLE IF NOT EXISTS scck_acceptance (
                  acceptance_id TEXT PRIMARY KEY, scope TEXT NOT NULL,
                  version INTEGER NOT NULL, manifest_json TEXT NOT NULL,
                  principal TEXT NOT NULL, state TEXT NOT NULL,
                  UNIQUE(scope,version));
                CREATE TABLE IF NOT EXISTS scck_audit (
                  sequence INTEGER PRIMARY KEY AUTOINCREMENT,
                  event_json TEXT NOT NULL);
            """)

    @contextmanager
    def _connection(self):
        db = sqlite3.connect(self.database, timeout=5, isolation_level=None)
        db.row_factory = sqlite3.Row
        db.execute("PRAGMA synchronous=FULL")
        try:
            yield db
        finally:
            db.close()

    @contextmanager
    def _transaction(self):
        with self._connection() as db:
            db.execute("BEGIN IMMEDIATE")
            try:
                yield db
                db.commit()
            except BaseException:
                db.rollback()
                raise

    @staticmethod
    def scope(package_id: str, device_id: str, component: str) -> str:
        for value in (package_id, device_id, component):
            _text(value)
        # Epoch is deliberately excluded: a new epoch cannot reset rollback state.
        return _json([package_id, device_id, component])

    def _now(self):
        value = self.clock()
        if type(value) not in (int, float) or not 0 <= value <= MAX_INTEGER:
            raise SCCKError("UNTRUSTED_TIME")
        return value

    def _audit(self, db, identity, event_type, payload):
        row = db.execute("SELECT event_json FROM scck_audit ORDER BY sequence DESC LIMIT 1").fetchone()
        previous = json.loads(row[0])["event_hash"] if row else "GENESIS"
        event = Event.build(str(db.execute("SELECT COUNT(*) FROM scck_audit").fetchone()[0] + 1),
                            event_type, identity, OPERATION, payload, previous)
        db.execute("INSERT INTO scck_audit(event_json) VALUES (?)", (_json(asdict(event)),))

    def provision_scope(self, *, package_id: str, device_id: str, component: str,
                        revision: int, epoch: int, root: str, trusted_keys: tuple[bytes, ...],
                        principal: str, grant_expires: int, revoked_keys: tuple[bytes, ...] = ()):
        """Trusted-host policy update with monotonic revision; does not issue authority.

        The host authenticates the administrator and obtains an explicit scoped
        grant before calling. All keys apply ONLY to this exact package/device/
        component and the fixed inspect operation. No wildcard scopes.
        """
        scope = self.scope(package_id, device_id, component)
        _text(principal)
        _hash(root)
        for value in (revision, epoch, grant_expires):
            _integer(value)
        for key in (*trusted_keys, *revoked_keys):
            if type(key) is not bytes or len(key) != 32:
                raise SCCKError("INVALID_KEY")
        with self._transaction() as db:
            old = db.execute("SELECT revision,epoch FROM scck_policy WHERE scope=?", (scope,)).fetchone()
            if old and (revision <= old["revision"] or epoch < old["epoch"]):
                raise SCCKError("POLICY_ROLLBACK")
            db.execute("INSERT OR REPLACE INTO scck_policy VALUES (?,?,?,?,?,?,?,?)",
                       (scope, revision, epoch, root, _json(sorted(k.hex() for k in trusted_keys)),
                        _json(sorted(k.hex() for k in revoked_keys)), principal, grant_expires))
            self._audit(db, scope, "SCCK_POLICY_UPDATED", {"revision": revision, "epoch": epoch})

    def _authorize(self, db, package, principal, scope):
        # Read CURRENT policy under the SAME transaction as state mutation.
        m = package.manifest
        now = self._now()
        row = db.execute("SELECT * FROM scck_policy WHERE scope=?", (scope,)).fetchone()
        if row is None:
            raise SCCKError("SCOPE_NOT_AUTHORIZED")
        key = package.public_key.hex()
        if key in json.loads(row["revoked_json"]):
            raise SCCKError("REVOKED_KEY_ENCOUNTERED")
        if key not in json.loads(row["keys_json"]):
            raise SCCKError("KEY_NOT_TRUSTED")
        if principal != row["principal"] or now >= row["grant_expires"]:
            raise SCCKError("AUTHORITY_DENIED")
        if now >= m.expires_at:
            raise SCCKError("PACKAGE_EXPIRED")
        if m.epoch != row["epoch"]:
            raise SCCKError("EPOCH_MISMATCH")
        if m.merkle_root != row["root"]:
            raise SCCKError("CANONICAL_ROOT_MISMATCH")
        return row["revision"]

    def admit(self, package: Package, *, principal: str) -> str:
        identity = verify_package(package)
        m = package.manifest
        scope = self.scope(m.package_id, m.device_id, m.component)
        with self._transaction() as db:
            revision = self._authorize(db, package, principal, scope)
            row = db.execute("SELECT version FROM scck_highwater WHERE scope=?", (scope,)).fetchone()
            if row and m.version <= row[0]:
                raise SCCKError("VERSION_DOWNGRADE_OR_REPLAY_DETECTED")
            db.execute("INSERT OR REPLACE INTO scck_highwater VALUES (?,?)", (scope, m.version))
            db.execute("INSERT INTO scck_acceptance VALUES (?,?,?,?,?,'ACCEPTED')",
                       (identity, scope, m.version, _json(asdict(m)), principal))
            self._audit(db, identity, "SCCK_ACCEPTED",
                        {"scope": scope, "version": m.version, "policy_revision": revision})
        return identity

    def begin_inspection(self, identity: str, package: Package, *, principal: str):
        """Revalidate exact bytes, revocation, grant, expiry and latest version."""
        if verify_package(package) != identity:
            raise SCCKError("ACCEPTANCE_MISMATCH")
        m = package.manifest
        scope = self.scope(m.package_id, m.device_id, m.component)
        with self._transaction() as db:
            revision = self._authorize(db, package, principal, scope)
            row = db.execute("SELECT * FROM scck_acceptance WHERE acceptance_id=?", (identity,)).fetchone()
            if row is None or row["principal"] != principal or row["state"] != "ACCEPTED":
                raise SCCKError("EXECUTION_STATE_CONFLICT")
            high = db.execute("SELECT version FROM scck_highwater WHERE scope=?", (scope,)).fetchone()
            if high is None or m.version != high[0]:
                raise SCCKError("ACCEPTANCE_SUPERSEDED")
            db.execute("UPDATE scck_acceptance SET state='EXECUTING' WHERE acceptance_id=?", (identity,))
            self._audit(db, identity, "SCCK_EXECUTING", {"policy_revision": revision})

    def _finish(self, identity: str, state: str, evidence: dict):
        with self._transaction() as db:
            row = db.execute("SELECT state FROM scck_acceptance WHERE acceptance_id=?", (identity,)).fetchone()
            if row is None or row[0] != "EXECUTING":
                raise SCCKError("EXECUTION_STATE_CONFLICT")
            db.execute("UPDATE scck_acceptance SET state=? WHERE acceptance_id=?", (state, identity))
            self._audit(db, identity, "SCCK_" + state, evidence)

    def inspect(self, identity: str, package: Package, *, principal: str) -> dict:
        """Invoke only a fixed pure worker in the EXISTING VX runtime, never assets."""
        self.begin_inspection(identity, package, principal=principal)
        runtime = VXRuntime(policy=ExecutionPolicy(frozenset({OPERATION})))
        execution = runtime.execute(identity, OPERATION, {"payload_hex": package.payload.hex()},
                                    _inspect_payload)
        if execution.status is not ExecutionStatus.SUCCESS or not runtime.verify():
            self._finish(identity, "FAILED", {"reason": "LOCAL_INSPECTION_FAILED"})
            raise SCCKError("LOCAL_INSPECTION_FAILED")
        evidence = {"input_hash": execution.input_hash, "output_hash": execution.output_hash,
                    "event_hash": execution.event_hash, "output": execution.output,
                    "execution_kind": "LOCAL_FIXED_INSPECTION_ONLY"}
        self._finish(identity, "SUCCEEDED", evidence)
        return evidence

    def recovery_holds(self) -> tuple[str, ...]:
        with self._connection() as db:
            return tuple(row[0] for row in db.execute(
                "SELECT acceptance_id FROM scck_acceptance WHERE state='EXECUTING' ORDER BY acceptance_id"))

    def audit_events(self) -> tuple[dict, ...]:
        with self._connection() as db:
            return tuple(json.loads(row[0]) for row in db.execute(
                "SELECT event_json FROM scck_audit ORDER BY sequence"))

    def verify_audit(self) -> bool:
        previous = "GENESIS"
        try:
            for item in self.audit_events():
                event = Event.build(item["event_id"], item["event_type"], item["execution_id"],
                                    item["capability"], item["payload"], previous)
                if asdict(event) != item:
                    return False
                previous = event.event_hash
            return True
        except (KeyError, TypeError, ValueError):
            return False


def _inspect_payload(inputs: dict) -> dict:
    payload = bytes.fromhex(inputs["payload_hex"])
    return {"payload_hash": hashlib.sha256(payload).hexdigest(), "size": len(payload)}
