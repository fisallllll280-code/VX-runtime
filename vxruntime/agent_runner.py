"""Bounded local agent runner over the existing VX execution boundary.

The host authenticates callers and supplies grants out of band. No HTTP,
shell, plugin loading, model provider or arbitrary worker registration.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
import json
import math
from pathlib import Path
import re
import sqlite3
import time
from typing import Callable

from .core import ExecutionPolicy, ExecutionStatus, VXRuntime, canonical_json, digest
from .municipal import (
    AGENT, CAPABILITY, PROFILE, BoundaryError, DataPolicy,
    check_readiness, validate_facts,
)


def _safe_worker(facts: dict) -> dict:
    try:
        return check_readiness(facts)
    except Exception:
        # The existing core records exception messages; never let dependency text
        # reach its ledger or a durable receipt from this lane.
        raise BoundaryError("WORKER_FAILED") from None


@dataclass(frozen=True)
class HostGrant:
    principal: str
    issuer: str
    capability: str
    expires_epoch: int
    approved: bool = False


class AgentRunner:
    """A single fixed local role; config/grants belong to the trusted host.

    SQLite transactions serialize duplicate claims. Unknown crash outcomes HOLD;
    no automatic retries. Dedupe lasts until receipt expiry, at most 24 hours.
    Cancellation/deadlines are cooperative for this bounded pure worker only.
    """
    def __init__(
        self, database: str | Path, *, policy: DataPolicy,
        grants: tuple[HostGrant, ...] = (),
        clock: Callable[[], float] = time.time,
    ) -> None:
        self.database = str(database)
        self.policy = policy
        self.grants = tuple(grants)
        self.clock = clock
        with self._connect() as db:
            db.execute("""CREATE TABLE IF NOT EXISTS receipts (
                task_key TEXT PRIMARY KEY, request_hash TEXT NOT NULL,
                expires REAL NOT NULL, state TEXT NOT NULL,
                receipt TEXT NOT NULL)""")

    def _connect(self):
        return sqlite3.connect(self.database, timeout=5)

    def _authorized(self, now: float) -> bool:
        return any(
            g.principal == AGENT and g.issuer == "VX-HOST-AUTHORITY"
            and g.issuer != g.principal and g.capability == CAPABILITY
            and g.approved is True and type(g.expires_epoch) is int
            and g.expires_epoch > now for g in self.grants
        )

    def run(
        self, task_key: str, facts: object, *, deadline_epoch: float,
        cancelled: Callable[[], bool] = lambda: False,
    ) -> dict:
        # Opaque random keys only. Callers must not derive keys from personal data.
        if type(task_key) is not str or re.fullmatch(r"[0-9a-f]{32}", task_key) is None:
            return {"status": "BLOCKED", "reason": "TASK_KEY_DENIED"}
        now = self.clock()
        if not self._authorized(now):
            return {"status": "BLOCKED", "reason": "AUTHORITY_DENIED"}
        try:
            self.policy.validate()
            normal = validate_facts(facts)
        except BoundaryError as exc:
            return {"status": "BLOCKED", "reason": str(exc)}
        if (type(deadline_epoch) not in (float, int)
                or not math.isfinite(deadline_epoch) or deadline_epoch <= now):
            return {"status": "BLOCKED", "reason": "DEADLINE_EXCEEDED"}
        if cancelled():
            return {"status": "CANCELLED", "reason": "CANCELLED_BEFORE_EXECUTION"}
        request_hash = digest({"facts": normal, "policy": asdict(self.policy),
                               "capability": CAPABILITY, "profile": PROFILE})
        db = self._connect()
        try:
            db.execute("BEGIN IMMEDIATE")
            # Deletes ONLY this lane's expired, nonpersonal readiness receipts.
            db.execute("DELETE FROM receipts WHERE expires <= ?", (now,))
            row = db.execute("SELECT request_hash,state,receipt FROM receipts WHERE task_key=?",
                             (task_key,)).fetchone()
            if row:
                db.commit()
                if row[0] != request_hash:
                    return {"status": "BLOCKED", "reason": "IDEMPOTENCY_CONFLICT"}
                if row[1] != "COMPLETE":
                    return {"status": "HOLD", "reason": "OUTCOME_REVIEW_REQUIRED"}
                try:
                    cached = json.loads(row[2])
                    body = {k: v for k, v in cached.items() if k != "receipt_hash"}
                    if (digest(body) != cached["receipt_hash"]
                            or cached["request_hash"] != request_hash
                            or cached["task_key"] != task_key):
                        raise ValueError
                except (ValueError, KeyError, TypeError, AttributeError):
                    return {"status": "HOLD", "reason": "RECEIPT_INTEGRITY_FAILED"}
                return {**cached, "deduplicated": True}
            db.execute("INSERT INTO receipts VALUES (?,?,?,?,?)",
                       (task_key, request_hash, now + self.policy.retention_seconds,
                        "RUNNING", "{}"))
            # Fixed worker receives minimised booleans only, after host authorization.
            runtime = VXRuntime(policy=ExecutionPolicy(frozenset({CAPABILITY})))
            result = runtime.execute(task_key, CAPABILITY, normal, _safe_worker)
            finished = self.clock()
            if cancelled():
                status, reason = "CANCELLED", "CANCELLED_DURING_EXECUTION"
            elif finished >= deadline_epoch or not self._authorized(finished):
                status, reason = "BLOCKED", "DEADLINE_OR_GRANT_EXPIRED"
            elif result.status is not ExecutionStatus.SUCCESS:
                status, reason = "FAILED", "WORKER_FAILED"
            else:
                status, reason = "SUCCESS", None
            body = {
                "schema_version": "1", "status": status, "reason": reason,
                "agent": AGENT, "capability": CAPABILITY,
                "task_key": task_key, "request_hash": request_hash,
                "input_hash": result.input_hash,
                "output_hash": result.output_hash,
                "output": result.output if status == "SUCCESS" else None,
                "events": [asdict(e) for e in runtime.ledger.events],
                "ledger_valid": runtime.verify(),
                "replay_match": runtime.replay(task_key, _safe_worker)
                    if status == "SUCCESS" else False,
                "environment": "LOCAL_TEST", "external_calls": 0,
                "production_gate": "HOLD", "pdpl_certification": "NOT_CLAIMED",
            }
            receipt = {**body, "receipt_hash": digest(body)}
            db.execute("UPDATE receipts SET state='COMPLETE',receipt=? WHERE task_key=?",
                       (canonical_json(receipt), task_key))
            db.commit()
            return {**receipt, "deduplicated": False}
        except Exception:
            db.rollback()
            # Fixed pure worker has no external effects; DB failure still propagates.
            raise
        finally:
            db.close()
