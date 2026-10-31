"""VX Cognitive Fabric: indexed specialist registry and evidence-aware knowledge exchange.

This is a deterministic local coordination substrate, not hosted LLM inference.
"""
from __future__ import annotations
import json
import sqlite3
from pathlib import Path
from .memory import canonical, fingerprint

INDEX_KEYS = (
    "source_index","legacy_master_index","entity_index","terminology_index",
    "innovation_index","architecture_index","capability_index","contract_index",
    "authority_index","event_index","state_index","dependency_index",
    "relation_index","lineage_index","canonical_index","implementation_index",
    "repository_index","artifact_index","test_index","evidence_index",
    "proof_index","operation_index","failure_recovery_index","security_index",
    "observability_index","simulation_index","evolution_index","cross_reference_index"
)
VALID_STATES = frozenset({"PROPOSED","IMPLEMENTED","VERIFIED","RECOVERED","CANONICAL"})

class CognitiveFabric:
    def __init__(self, path):
        self.db = sqlite3.connect(str(path))
        self.db.execute("PRAGMA foreign_keys=ON")
        self.db.execute("PRAGMA journal_mode=WAL")
        self.db.execute("""CREATE TABLE IF NOT EXISTS specialists (
            agent_id TEXT PRIMARY KEY, domain TEXT NOT NULL, capabilities TEXT NOT NULL,
            authority TEXT NOT NULL, version TEXT NOT NULL)""")
        self.db.execute("""CREATE TABLE IF NOT EXISTS knowledge (
            item_id TEXT PRIMARY KEY, creator TEXT NOT NULL REFERENCES specialists(agent_id),
            source_ref TEXT NOT NULL, source_version TEXT NOT NULL, index_key TEXT NOT NULL,
            body TEXT NOT NULL, content_hash TEXT NOT NULL, state TEXT NOT NULL DEFAULT 'PROPOSED',
            UNIQUE(creator, source_ref, source_version, index_key, content_hash))""")
        self.db.execute("""CREATE TABLE IF NOT EXISTS grants (
            agent_id TEXT NOT NULL REFERENCES specialists(agent_id),
            item_id TEXT NOT NULL REFERENCES knowledge(item_id),
            PRIMARY KEY(agent_id,item_id))""")
        self.db.commit()

    def register(self, agent_id, domain, capabilities, authority="read", version="v1"):
        if not all(isinstance(v,str) and v.strip() for v in (agent_id,domain,authority,version)):
            raise ValueError("INVALID_SPECIALIST_IDENTITY")
        if authority not in {"read","write_proposed"}:
            raise ValueError("UNSUPPORTED_AUTHORITY")
        caps=sorted(set(capabilities))
        if not caps or not all(isinstance(c,str) and c.strip() for c in caps):
            raise ValueError("CAPABILITIES_REQUIRED")
        with self.db:
            old=self.db.execute("SELECT domain,capabilities,authority,version FROM specialists WHERE agent_id=?",(agent_id,)).fetchone()
            record=(domain,canonical(caps),authority,version)
            if old and old!=record:
                raise ValueError("SPECIALIST_VERSION_CONFLICT")
            self.db.execute("INSERT OR IGNORE INTO specialists VALUES (?,?,?,?,?)",(agent_id,*record))
        return agent_id

    def publish(self, agent_id, source_ref, source_version, index_key, body):
        owner=self.db.execute("SELECT authority FROM specialists WHERE agent_id=?",(agent_id,)).fetchone()
        if not owner or owner[0]!="write_proposed":
            raise PermissionError("PUBLISH_DENIED")
        if index_key not in INDEX_KEYS:
            raise ValueError("UNKNOWN_OMEGA_INDEX")
        if not isinstance(source_ref,str) or not source_ref.strip() or not isinstance(source_version,str) or not source_version.strip():
            raise ValueError("SOURCE_PROVENANCE_REQUIRED")
        identity={"creator":agent_id,"source_ref":source_ref,"source_version":source_version,
                  "index_key":index_key,"hash":fingerprint(body)}
        item_id="VXK-"+fingerprint(identity)
        with self.db:
            self.db.execute("""INSERT OR IGNORE INTO knowledge
                (item_id,creator,source_ref,source_version,index_key,body,content_hash)
                VALUES(?,?,?,?,?,?,?)""",(item_id,agent_id,source_ref,source_version,
                                          index_key,canonical(body),fingerprint(body)))
        return item_id

    def grant(self, owner_id, reader_id, item_id):
        record=self.db.execute("SELECT creator FROM knowledge WHERE item_id=?",(item_id,)).fetchone()
        if not record or record[0]!=owner_id:
            raise PermissionError("OWNER_GRANT_REQUIRED")
        if not self.db.execute("SELECT 1 FROM specialists WHERE agent_id=?",(reader_id,)).fetchone():
            raise ValueError("UNKNOWN_READER")
        with self.db:
            self.db.execute("INSERT OR IGNORE INTO grants VALUES (?,?)",(reader_id,item_id))

    def recall(self, agent_id, index_key=None):
        if not self.db.execute("SELECT 1 FROM specialists WHERE agent_id=?",(agent_id,)).fetchone():
            raise PermissionError("UNKNOWN_AGENT")
        if index_key is not None and index_key not in INDEX_KEYS:
            raise ValueError("UNKNOWN_OMEGA_INDEX")
        sql="""SELECT k.item_id,k.creator,k.index_key,k.source_ref,k.source_version,
               k.body,k.state,k.content_hash FROM knowledge k
               WHERE (k.creator=? OR EXISTS
               (SELECT 1 FROM grants g WHERE g.agent_id=? AND g.item_id=k.item_id))"""
        args=[agent_id,agent_id]
        if index_key:
            sql+=" AND k.index_key=?"
            args.append(index_key)
        sql+=" ORDER BY k.item_id"
        return [{"item_id":r[0],"creator":r[1],"index_key":r[2],"source_ref":r[3],
                 "source_version":r[4],"body":json.loads(r[5]),"state":r[6],
                 "hash":r[7]} for r in self.db.execute(sql,args)]

    def verify(self):
        if self.db.execute("PRAGMA integrity_check").fetchone()[0]!="ok":
            return False
        return all(fingerprint(json.loads(body))==h for body,h in
                   self.db.execute("SELECT body,content_hash FROM knowledge"))

    def close(self):
        self.db.close()
