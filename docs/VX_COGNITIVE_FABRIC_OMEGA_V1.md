# VX Cognitive Fabric — Ω-native Specialist Minds v0.1

Status: **IMPLEMENTED ON FEATURE BRANCH; independent validation pending**. This is a deterministic coordination substrate, not an LLM service, autonomous market agent, or production deployment.

## Purpose

Give each tool a bounded cognitive identity, capability list and access policy; preserve shared knowledge with exact source identity and the original Ω 28 index *views* without inventing new sovereign roots.

Component: `vxruntime/cognitive_fabric.py`. Reuses `vxruntime/memory.py` canonical hashing helpers; adds a SQLite-backed registry, provenance-preserving knowledge items, owner-granted sharing, exact dedup and tamper checks. Cross-tool access is **deny by default**. New items are PROPOSED. The module never writes Ω.000 or grants CANONICAL / VERIFIED.

## Authority and correspondence

- VAIXLNS owns constitutional governance and canonical Ω.
- VX handles controlled execution and derivative knowledge; VV presents current evidence without promotion.
- Specialist minds are registered with `read` or `write_proposed`, not powers to edit remote tools, merge PRs, deploy, issue payments or market orders.
- The 28 `INDEX_KEYS` are derived views 00–27; do not mutate or fabricate historic 0001–2750 records.

## Minimal usage

```python
from vxruntime.cognitive_fabric import CognitiveFabric
f = CognitiveFabric(".local/fabric.db")
f.register("research", "research", ["inspect","synthesize"], "write_proposed")
f.register("coding", "engineering", ["inspect"], "read")
key = f.publish("research", "repo/analysis.md", "commit-sha",
                "innovation_index", {"finding": "sample"})
assert f.recall("coding") == []
f.grant("research", "coding", key)
assert len(f.recall("coding", "innovation_index")) == 1
assert f.verify()
f.close()
```

## Hard boundaries

- Evidence refs are *claims* until independently checked; simple hashing is not provenance authentication.
- Exact content dedup is not semantic dedup. Historical index gaps remain unresolved.
- Sharing grants are explicit; revocation, encryption at rest, audit log for grants, time-bound identities and multi-process atomicity remain pending.
- No LLM inference, model training, voice, Web UI backend, MCP connection or external financial execution.
- **Security gate before real use:** encrypted backup+restore exercise, independent source verification, scoped OAuth authentication, input-size limits, adversarial prompt-injection evaluation, true isolation per tenant and model-provider policy.
- Any assertion of being stronger, smarter, faster or more capable than market tools requires benchmark baselines, cost envelopes and reproducible empirical results.

## CI

`python -m pytest -q tests/test_cognitive_fabric.py` followed by entire VX Conformance workflow on exact commit SHA. Never merge or release before explicit approval.
