# VX Tool Memory & Intelligence Slices v0.1

State: IMPLEMENTED (code on feature branch); tests require independent execution. NOT VERIFIED.

Purpose: persistent memory per tool with deterministic duplicate detection and reproducible specialized agent *definitions* (not generated model weights or semiconductor chips).

- Memory uses SQLite/WAL with stable per-tool identity and original provenance.
- Exact duplicate bodies for the same tool and kind return the existing identity; original source and version are retained.
- Every slice is a content-addressed declarative specialty/capability/memory-reference set, initially PROPOSED.
- A slice cannot reference another tool's private memory.
- Callers must supply source_ref and source_version; do not store tokens, private keys or personal secrets.
- No automated execution, inference, network requests, self-editing, merge, publication or claimed model training.
- Back up SQLite using SQLite's online backup API; copying an open WAL database file alone is not a reliable backup.
- Semantic duplicates, conflicting claims, forgotten unindexed sources, access policies and cross-repository canonical admission are not solved by v0.1.
- For actual tool execution reuse VXRuntime's independent policy gates and the canonical Ω evidence registry.

Example:

```python
from vxruntime.memory import MemoryVault
vault = MemoryVault(".local/vx_memory.sqlite3")
record = vault.remember("github", "finding", {"subject": "example"}, "owner/repo/path", "commit-sha")
slice_ = vault.generate_slice("github", "repository_review", ["inspect"], [record["id"]])
assert vault.integrity_check()
vault.close()
```

Tests: `python -m unittest discover -s tests -p 'test_memory.py' -v`.
