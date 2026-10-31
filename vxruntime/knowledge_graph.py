"""Evidence-linked per-tool knowledge graph, without external services."""
import json
import sqlite3
from pathlib import Path
from .memory import canonical, fingerprint


class KnowledgeGraph:
    def __init__(self, path):
        self.path = str(path)
        Path(self.path).parent.mkdir(parents=True, exist_ok=True)
        self.db = sqlite3.connect(self.path)
        self.db.execute("PRAGMA foreign_keys=ON")
        self.db.execute("PRAGMA journal_mode=WAL")
        self.db.execute("""CREATE TABLE IF NOT EXISTS nodes(
            node_id TEXT PRIMARY KEY, tool_id TEXT NOT NULL, kind TEXT NOT NULL,
            stable_ref TEXT NOT NULL, source_version TEXT NOT NULL, data TEXT NOT NULL,
            data_hash TEXT NOT NULL, state TEXT NOT NULL DEFAULT 'PROPOSED',
            UNIQUE(tool_id, kind, stable_ref, source_version))""")
        self.db.execute("""CREATE TABLE IF NOT EXISTS edges(
            edge_id TEXT PRIMARY KEY, source_id TEXT NOT NULL REFERENCES nodes(node_id),
            target_id TEXT NOT NULL REFERENCES nodes(node_id), relation TEXT NOT NULL,
            evidence_ref TEXT NOT NULL, state TEXT NOT NULL DEFAULT 'PROPOSED')""")
        self.db.commit()

    def add_node(self, tool_id, kind, stable_ref, source_version, data):
        if not all(isinstance(x, str) and x.strip() for x in
                   (tool_id, kind, stable_ref, source_version)):
            raise ValueError("NODE_PROVENANCE_REQUIRED")
        key = {"tool_id":tool_id,"kind":kind,"stable_ref":stable_ref,
               "source_version":source_version}
        node_id = "VXG-" + fingerprint(key)
        encoded = canonical(data)
        with self.db:
            row = self.db.execute(
                "SELECT data_hash FROM nodes WHERE node_id=?", (node_id,)).fetchone()
            if row and row[0] != fingerprint(data):
                raise ValueError("SOURCE_VERSION_CONFLICT")
            self.db.execute("""INSERT OR IGNORE INTO nodes
                (node_id,tool_id,kind,stable_ref,source_version,data,data_hash)
                VALUES(?,?,?,?,?,?,?)""",
                (node_id,tool_id,kind,stable_ref,source_version,encoded,fingerprint(data)))
        return node_id

    def add_edge(self, source_id, target_id, relation, evidence_ref):
        if not relation or not evidence_ref:
            raise ValueError("RELATION_EVIDENCE_REQUIRED")
        nodes = self.db.execute("SELECT node_id,tool_id FROM nodes WHERE node_id IN (?,?)",
                                (source_id,target_id)).fetchall()
        if len({row[0] for row in nodes}) != len({source_id,target_id}):
            raise ValueError("UNKNOWN_NODE")
        # Cross-tool links are proposed evidence references, not automatic trust transfer.
        key = {"source":source_id,"target":target_id,"relation":relation,
               "evidence":evidence_ref}
        edge_id = "VXE-" + fingerprint(key)
        with self.db:
            self.db.execute("""INSERT OR IGNORE INTO edges
                (edge_id,source_id,target_id,relation,evidence_ref)
                VALUES(?,?,?,?,?)""",(edge_id,source_id,target_id,relation,evidence_ref))
        return edge_id

    def neighbors(self, node_id):
        return [{"edge_id":r[0],"target_id":r[1],"relation":r[2],
                 "evidence_ref":r[3],"state":r[4]} for r in self.db.execute(
                 """SELECT edge_id,target_id,relation,evidence_ref,state FROM edges
                    WHERE source_id=? ORDER BY edge_id""",(node_id,))]

    def verify(self):
        if self.db.execute("PRAGMA integrity_check").fetchone()[0] != "ok":
            return False
        for raw, stored in self.db.execute("SELECT data,data_hash FROM nodes"):
            if fingerprint(json.loads(raw)) != stored:
                return False
        return True

    def close(self):
        self.db.close()
