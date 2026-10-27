"""Real Ed25519 + SQLite reference acceptance tests, no remote provider."""
from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace
import hashlib
import multiprocessing
from pathlib import Path
import sqlite3
import tempfile
import threading
import unittest
from unittest.mock import patch

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from vxruntime.scck import (
    AdmissionStore, Manifest, Package, SCCKError, MAX_PAYLOAD, MAX_PROOF,
    merkle_leaf, merkle_parent, verify_package,
)


def _child_admit(database, package, result):
    try:
        AdmissionStore(database, clock=lambda: 100).admit(package, principal="host.worker")
        result.put("ACCEPTED")
    except SCCKError as exc:
        result.put(str(exc))


class SCCKTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.database = str(Path(self.tmp.name) / "admission.sqlite")
        self.now = 100
        self.store = AdmissionStore(self.database, clock=lambda: self.now)
        self.key = Ed25519PrivateKey.generate()
        self.public = self.key.public_key().public_bytes_raw()
        self.payload = b"local inert inspection fixture"
        self.payload_hash = hashlib.sha256(self.payload).hexdigest()
        self.root = merkle_leaf(self.payload_hash).hex()
        self.policy = dict(package_id="pkg-a", device_id="device-a", component="asset",
                           revision=1, epoch=1, root=self.root, trusted_keys=(self.public,),
                           principal="host.worker", grant_expires=1000)
        self.store.provision_scope(**self.policy)

    def package(self, **changes):
        m = Manifest("pkg-a", "device-a", "asset", 10, 1, 500,
                     self.payload_hash, self.root)
        m = replace(m, **changes)
        return Package(m, self.payload, self.public, self.key.sign(m.signing_bytes()))

    def admit(self, package=None):
        return self.store.admit(package or self.package(), principal="host.worker")

    def reject(self, code, package=None):
        before = self.store.audit_events()
        with self.assertRaisesRegex(SCCKError, "^" + code + "$"):
            self.admit(package)
        self.assertEqual(before, self.store.audit_events())

    def test_positive_existing_vx_core_and_durable_audit(self):
        package = self.package()
        identity = self.admit(package)
        evidence = self.store.inspect(identity, package, principal="host.worker")
        self.assertEqual(evidence["output"], {"payload_hash": self.payload_hash, "size": len(self.payload)})
        self.assertEqual(evidence["execution_kind"], "LOCAL_FIXED_INSPECTION_ONLY")
        reopened = AdmissionStore(self.database)
        self.assertTrue(reopened.verify_audit())
        self.assertEqual([e["event_type"] for e in reopened.audit_events()],
                         ["SCCK_POLICY_UPDATED", "SCCK_ACCEPTED", "SCCK_EXECUTING", "SCCK_SUCCEEDED"])
        self.assertEqual(reopened.audit_events()[-1]["payload"], evidence)

    def test_10_then_9_rejected(self):
        self.admit()
        self.reject("VERSION_DOWNGRADE_OR_REPLAY_DETECTED", self.package(version=9))

    def test_exact_replay_rejected(self):
        self.admit()
        self.reject("VERSION_DOWNGRADE_OR_REPLAY_DETECTED")

    def test_restart_rejects_replay(self):
        self.admit()
        self.store = AdmissionStore(self.database, clock=lambda: 100)
        self.reject("VERSION_DOWNGRADE_OR_REPLAY_DETECTED")

    def test_new_process_rejects_replay(self):
        self.admit()
        ctx = multiprocessing.get_context("spawn")
        result = ctx.Queue()
        child = ctx.Process(target=_child_admit, args=(self.database, self.package(), result))
        child.start()
        child.join(10)
        if child.is_alive():
            child.terminate()
            child.join()
            self.fail("child timeout")
        self.assertEqual(child.exitcode, 0)
        self.assertEqual(result.get(timeout=2), "VERSION_DOWNGRADE_OR_REPLAY_DETECTED")
        result.close()

    def test_same_version_independent_scopes(self):
        self.admit()
        for field in ("package_id", "device_id", "component"):
            with self.subTest(field=field):
                self.store.provision_scope(**{**self.policy, field: "other"})
                self.admit(self.package(**{field: "other"}))

    def test_unprovisioned_device_rejected(self):
        self.reject("SCOPE_NOT_AUTHORIZED", self.package(device_id="other"))

    def test_payload_tampering_rejected(self):
        self.reject("PAYLOAD_HASH_MISMATCH", replace(self.package(), payload=b"tampered"))

    def test_manifest_tampering_rejected(self):
        p = self.package()
        self.reject("SIGNATURE_VERIFICATION_FAILED", replace(p, manifest=replace(p.manifest, version=11)))

    def test_untrusted_signing_key_rejected(self):
        key = Ed25519PrivateKey.generate()
        p = self.package()
        self.reject("KEY_NOT_TRUSTED", replace(p, public_key=key.public_key().public_bytes_raw(),
                                             signature=key.sign(p.manifest.signing_bytes())))

    def test_revocation_overrides_trust(self):
        self.store.provision_scope(**{**self.policy, "revision": 2, "revoked_keys": (self.public,)})
        self.reject("REVOKED_KEY_ENCOUNTERED")

    def test_epoch_mismatch(self):
        self.reject("EPOCH_MISMATCH", self.package(epoch=2))

    def test_epoch_change_does_not_reset_highwater(self):
        self.admit()
        self.store.provision_scope(**{**self.policy, "revision": 2, "epoch": 2})
        self.reject("VERSION_DOWNGRADE_OR_REPLAY_DETECTED", self.package(epoch=2, version=9))

    def test_expiration_equal_and_after_rejected(self):
        for now in (500, 501):
            self.now = now
            self.reject("PACKAGE_EXPIRED")

    def test_grant_expiry_and_wrong_principal(self):
        with self.assertRaisesRegex(SCCKError, "AUTHORITY_DENIED"):
            self.store.admit(self.package(), principal="untrusted")
        self.now = 1000
        self.reject("AUTHORITY_DENIED")

    def test_root_requires_independent_host_anchor(self):
        other_payload = b"other"
        h = hashlib.sha256(other_payload).hexdigest()
        p = replace(self.package(payload_hash=h, merkle_root=merkle_leaf(h).hex()), payload=other_payload)
        self.reject("CANONICAL_ROOT_MISMATCH", p)

    def test_nonempty_merkle_path_and_invalid_path(self):
        sibling = merkle_leaf(hashlib.sha256(b"sibling").hexdigest())
        root = merkle_parent(merkle_leaf(self.payload_hash), sibling).hex()
        self.store.provision_scope(**{**self.policy, "revision": 2, "root": root})
        p = replace(self.package(merkle_root=root), merkle_path=(sibling,))
        self.reject("MERKLE_PROOF_INVALID", replace(p, merkle_path=(b"x" * 32,)))
        self.admit(p)

    def test_leaf_and_node_domains_distinct(self):
        leaf = merkle_leaf(self.payload_hash)
        self.assertNotEqual(leaf.hex(), self.payload_hash)
        self.assertEqual(merkle_parent(leaf, b"x" * 32), merkle_parent(b"x" * 32, leaf))
        self.assertNotEqual(merkle_parent(leaf, leaf), leaf)

    def test_two_threads_independent_connections_one_acceptance(self):
        barrier = threading.Barrier(2)
        package = self.package()
        def submit():
            store = AdmissionStore(self.database, clock=lambda: 100)
            barrier.wait(timeout=5)
            try:
                store.admit(package, principal="host.worker")
                return "ACCEPTED"
            except SCCKError as exc:
                return str(exc)
        with ThreadPoolExecutor(2) as pool:
            futures = [pool.submit(submit) for _ in range(2)]
            outcomes = [f.result(timeout=10) for f in futures]
        self.assertCountEqual(outcomes, ["ACCEPTED", "VERSION_DOWNGRADE_OR_REPLAY_DETECTED"])
        self.assertEqual(sum(e["event_type"] == "SCCK_ACCEPTED" for e in self.store.audit_events()), 1)

    def test_audit_write_failure_rolls_back_highwater_and_acceptance(self):
        with sqlite3.connect(self.database) as db:
            db.execute("CREATE TRIGGER fail_audit BEFORE INSERT ON scck_audit "
                       "BEGIN SELECT RAISE(ABORT, 'injected failure'); END")
        with self.assertRaises(sqlite3.IntegrityError):
            self.admit()
        with sqlite3.connect(self.database) as db:
            self.assertEqual(db.execute("SELECT COUNT(*) FROM scck_highwater").fetchone()[0], 0)
            self.assertEqual(db.execute("SELECT COUNT(*) FROM scck_acceptance").fetchone()[0], 0)
            db.execute("DROP TRIGGER fail_audit")
        self.admit()

    def test_revoke_between_crypto_and_transaction_is_rechecked(self):
        def verified_then_revoked(package):
            result = verify_package(package)
            self.store.provision_scope(**{**self.policy, "revision": 2, "revoked_keys": (self.public,)})
            return result
        with patch("vxruntime.scck.verify_package", side_effect=verified_then_revoked):
            with self.assertRaisesRegex(SCCKError, "REVOKED_KEY_ENCOUNTERED"):
                self.admit()

    def test_expiry_rechecked_after_crypto(self):
        def verified_then_expired(package):
            result = verify_package(package)
            self.now = 500
            return result
        with patch("vxruntime.scck.verify_package", side_effect=verified_then_expired):
            self.reject("PACKAGE_EXPIRED")

    def test_revocation_after_acceptance_blocks_execution(self):
        p = self.package()
        identity = self.admit(p)
        self.store.provision_scope(**{**self.policy, "revision": 2, "revoked_keys": (self.public,)})
        with self.assertRaisesRegex(SCCKError, "REVOKED_KEY_ENCOUNTERED"):
            self.store.inspect(identity, p, principal="host.worker")

    def test_old_accepted_package_cannot_execute_after_newer_acceptance(self):
        old = self.package(version=9)
        identity = self.admit(old)
        self.admit()
        with self.assertRaisesRegex(SCCKError, "ACCEPTANCE_SUPERSEDED"):
            self.store.inspect(identity, old, principal="host.worker")

    def test_execution_claim_cannot_repeat_after_success(self):
        p = self.package()
        identity = self.admit(p)
        self.store.inspect(identity, p, principal="host.worker")
        with self.assertRaisesRegex(SCCKError, "EXECUTION_STATE_CONFLICT"):
            self.store.inspect(identity, p, principal="host.worker")

    def test_execution_two_threads_claim_once(self):
        p = self.package()
        identity = self.admit(p)
        barrier = threading.Barrier(2)
        def claim():
            store = AdmissionStore(self.database, clock=lambda: 100)
            barrier.wait(timeout=5)
            try:
                store.begin_inspection(identity, p, principal="host.worker")
                return "EXECUTING"
            except SCCKError as exc:
                return str(exc)
        with ThreadPoolExecutor(2) as pool:
            futures = [pool.submit(claim) for _ in range(2)]
            outcomes = [f.result(timeout=10) for f in futures]
        self.assertCountEqual(outcomes, ["EXECUTING", "EXECUTION_STATE_CONFLICT"])

    def test_expiry_after_acceptance_blocks_execution(self):
        p = self.package()
        identity = self.admit(p)
        self.now = 500
        with self.assertRaisesRegex(SCCKError, "PACKAGE_EXPIRED"):
            self.store.inspect(identity, p, principal="host.worker")

    def test_different_package_cannot_reuse_acceptance(self):
        p = self.package()
        identity = self.admit(p)
        with self.assertRaisesRegex(SCCKError, "ACCEPTANCE_MISMATCH"):
            self.store.inspect(identity, self.package(version=11), principal="host.worker")

    def test_claim_audit_failure_leaves_accepted_not_executing(self):
        p = self.package()
        identity = self.admit(p)
        with sqlite3.connect(self.database) as db:
            db.execute("CREATE TRIGGER fail_claim BEFORE INSERT ON scck_audit "
                       "BEGIN SELECT RAISE(ABORT, 'injected failure'); END")
        with self.assertRaises(sqlite3.IntegrityError):
            self.store.begin_inspection(identity, p, principal="host.worker")
        self.assertEqual(self.store.recovery_holds(), ())
        with sqlite3.connect(self.database) as db:
            db.execute("DROP TRIGGER fail_claim")
        self.store.inspect(identity, p, principal="host.worker")

    def test_interrupted_execution_holds_on_restart(self):
        p = self.package()
        identity = self.admit(p)
        self.store.begin_inspection(identity, p, principal="host.worker")
        reopened = AdmissionStore(self.database, clock=lambda: 100)
        self.assertEqual(reopened.recovery_holds(), (identity,))
        with self.assertRaisesRegex(SCCKError, "EXECUTION_STATE_CONFLICT"):
            reopened.inspect(identity, p, principal="host.worker")

    def test_worker_failure_records_failed_without_lowering_highwater(self):
        p = self.package()
        identity = self.admit(p)
        with patch("vxruntime.scck._inspect_payload", side_effect=RuntimeError("synthetic")):
            with self.assertRaisesRegex(SCCKError, "LOCAL_INSPECTION_FAILED"):
                self.store.inspect(identity, p, principal="host.worker")
        self.assertEqual(self.store.audit_events()[-1]["event_type"], "SCCK_FAILED")
        self.reject("VERSION_DOWNGRADE_OR_REPLAY_DETECTED", self.package(version=9))

    def test_policy_revision_and_epoch_cannot_regress(self):
        with self.assertRaisesRegex(SCCKError, "POLICY_ROLLBACK"):
            self.store.provision_scope(**self.policy)
        with self.assertRaisesRegex(SCCKError, "POLICY_ROLLBACK"):
            self.store.provision_scope(**{**self.policy, "revision": 2, "epoch": 0})

    def test_limits_and_bad_types_fail_closed(self):
        self.reject("PAYLOAD_LIMIT", replace(self.package(), payload=b"x" * (MAX_PAYLOAD + 1)))
        self.reject("PROOF_LIMIT", replace(self.package(), merkle_path=(b"x" * 32,) * (MAX_PROOF + 1)))
        self.reject("INVALID_KEY", replace(self.package(), public_key=b"short"))
        self.reject("INVALID_SIGNATURE", replace(self.package(), signature=b"short"))
        with self.assertRaisesRegex(SCCKError, "INVALID_INTEGER"):
            self.package(version=True)
        with self.assertRaisesRegex(SCCKError, "INVALID_IDENTIFIER"):
            self.package(package_id="../x")
        with self.assertRaisesRegex(SCCKError, "UNSUPPORTED_PROTOCOL_OR_OPERATION"):
            self.package(operation="install")

    def test_audit_tampering_detected(self):
        self.admit()
        with sqlite3.connect(self.database) as db:
            db.execute("UPDATE scck_audit SET event_json=replace(event_json,'SCCK_ACCEPTED','SCCK_REJECTED') "
                       "WHERE sequence=2")
        self.assertFalse(self.store.verify_audit())

    def test_memory_database_refused(self):
        with self.assertRaisesRegex(SCCKError, "DURABLE_DATABASE_REQUIRED"):
            AdmissionStore(":memory:")
