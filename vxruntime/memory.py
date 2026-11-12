"""Persistent per-tool VX memory and deterministic intelligence slice registry.

Local SQLite storage; no external models, services or autonomous execution.
"""
from __future__ import annotations

import hashlib
import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path


def canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def fingerprint(value):
    return hashlib.sha256(canonical(value).encode("utf-8")).hexdigest()


class MemoryVault:
    def __init__(self, path):
        self.path = str(path)
        Path(self.path).parent.mkdir(parents=True, exist_ok=True)
        self.db = sqlite3.connect(self.path)
        self.db.execute("PRAGMA foreign_keys=ON")
        self.db.execute("PRAGMA journal_mode=WAL")
        self.db.execute("""CREATE TABLE IF NOT EXISTS memories (
          memory_id INTEGER PRIMARY KEY AUTOINCREMENT,
          tool_id TEXT NOT NULL,
          kind TEXT NOT NULL,
          body TEXT NOT NULL,
          content_hash TEXT NOT NULL,
          source_ref TEXT NOT NULL,
          source_version TEXT NOT NULL,
          state TEXT NOT NULL DEFAULT 'PROPOSED',
          created_at TEXT NOT NULL,
          UNIQUE(tool_id, kind, content_hash)
        )""")
        self.db.execute("""CREATE TABLE IF NOT EXISTS slices (
          slice_id TEXT PRIMARY KEY,
          tool_id TEXT NOT NULL,
          specialty TEXT NOT NULL,
          capabilities TEXT NOT NULL,
          memory_refs TEXT NOT NULL,
          fingerprint TEXT NOT NULL,
          status TEXT NOT NULL DEFAULT 'PROPOSED'
        )""")
        self.db.commit()

    def remember(self, tool_id, kind, body, source_ref, source_version):
        if not all(isinstance(x, str) and x.strip() for x in
                   (tool_id, kind, source_ref, source_version)):
            raise ValueError("IDENTITY_AND_PROVENANCE_REQUIRED")
        raw = canonical(body)
        signature = fingerprint(body)
        with self.db:
            cursor = self.db.execute(
                """INSERT OR IGNORE INTO memories
                (tool_id, kind, body, content_hash, source_ref, source_version, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (tool_id, kind, raw, signature, source_ref, source_version,
                 datetime.now(timezone.utc).isoformat()))
            row = self.db.execute(
                """SELECT memory_id, source_ref, source_version FROM memories
                WHERE tool_id=? AND kind=? AND content_hash=?""",
                (tool_id, kind, signature)).fetchone()
        return {"id": row[0], "created": cursor.rowcount == 1,
                "duplicate": cursor.rowcount == 0,
                "hash": signature, "original_source": row[1],
                "original_version": row[2]}

    def recall(self, tool_id, kind=None):
        query = """SELECT memory_id, kind, body, content_hash, source_ref,
                   source_version, state FROM memories WHERE tool_id=?"""
        args = [tool_id]
        if kind is not None:
            query += " AND kind=?"
            args.append(kind)
        query += " ORDER BY memory_id"
        return [{"id": r[0], "kind": r[1], "body": json.loads(r[2]),
                 "hash": r[3], "source_ref": r[4], "source_version": r[5],
                 "state": r[6]} for r in self.db.execute(query, args)]

    def generate_slice(self, tool_id, specialty, capabilities, memory_refs=()):
        if not tool_id or not specialty or not capabilities:
            raise ValueError("SLICE_IDENTITY_AND_CAPABILITIES_REQUIRED")
        capabilities = sorted(set(capabilities))
        refs = sorted(set(memory_refs))
        found = {r[0] for r in self.db.execute(
            "SELECT memory_id FROM memories WHERE tool_id=?", (tool_id,))}
        if not set(refs).issubset(found):
            raise ValueError("CROSS_TOOL_OR_UNKNOWN_MEMORY_REFERENCE")
        definition = {"tool_id": tool_id, "specialty": specialty,
                      "capabilities": capabilities, "memory_refs": refs}
        sig = fingerprint(definition)
        slice_id = "VXS-" + sig[:20]
        with self.db:
            cur = self.db.execute(
                """INSERT OR IGNORE INTO slices
                (slice_id, tool_id, specialty, capabilities, memory_refs, fingerprint)
                VALUES (?, ?, ?, ?, ?, ?)""",
                (slice_id, tool_id, specialty, canonical(capabilities),
                 canonical(refs), sig))
        return {"slice_id": slice_id, "created": cur.rowcount == 1,
                "fingerprint": sig, "status": "PROPOSED"}

    def integrity_check(self):
        if self.db.execute("PRAGMA integrity_check").fetchone()[0] != "ok":
            return False
        for raw, expected in self.db.execute(
                "SELECT body, content_hash FROM memories"):
            if fingerprint(json.loads(raw)) != expected:
                return False
        return True

    def close(self):
        self.db.close()
