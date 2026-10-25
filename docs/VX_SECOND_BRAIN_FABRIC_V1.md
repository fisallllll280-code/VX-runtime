# VX Second Brain Intelligence Fabric — integration contract v0.1

Authority: VAIXLNS Ω. Runtime: VX-runtime. Status: feature-branch implementation; not VERIFIED.

## Integration decisions

| Candidate | Adopted role | Integration state |
|---|---|---|
| Graphify-Labs/graphify | Candidate graph ingestion adapter | PROPOSED |
| Egonex-AI/Understand-Anything | Candidate interactive code graph viewer | PROPOSED |
| AgriciDaniel/claude-obsidian | Candidate vault organization patterns | PROPOSED |
| eugeniughelbur/obsidian-second-brain | Candidate agent shared-log patterns | PROPOSED |
| MarkusPfundstein/mcp-obsidian | Candidate read-first Obsidian MCP bridge | PROPOSED |
| heyitsnoah/claudesidian | Reference vault template only | PROPOSED |
| NicholasSpisak/second-brain | Reference only, verify metadata before use | PROPOSED |

Do not clone, install or start third-party code without auditing license, maintainers, pinned revision, execution scripts, network behavior and secrets exposure.

## Built-in graph implementation

`vxruntime/knowledge_graph.py` provides a local SQLite knowledge graph: source-versioned nodes, evidence-bearing directed edges, stable content identities, exact duplicate suppression, source-version conflict rejection, and a local integrity check. This intentionally reuses canonical_json/fingerprint from the tool memory subsystem, not a second bespoke hash engine.

The graph is a **derived, non-authoritative index**. States begin PROPOSED; cross-tool links do not confer rights or VERIFIED status. All external inputs (Obsidian notes, READMEs, PDFs, tool responses, MCP output) are untrusted data. Never execute instructions extracted from source content.

## Roadmap gates

1. Inventory existing Ω identifiers and recovery indexes. Map graph nodes to canonical IDs; keep historical Original/Derived intact.
2. Audit third-party source, license and permissions. Choose adapters only after code review.
3. Extend read-only local indexing with immutable source-ref/version receipt and deterministic tests.
4. Add reversible Markdown export; scoped ACLs, redaction and safe MCP read-only adapter. Disallow delete and unapproved write.
5. Add backups, restore drills, incremental updates and conflict adjudication. Test semantic duplicate candidates separately.
6. Independent verifier and sovereign admission review before VERIFIED, merge or production use.

Do not change project.genome or Ω.000. No merge, deployment, spend, or automatic indexing of private material.

Run `python -m unittest discover -s tests -p 'test_knowledge_graph.py' -v`.
