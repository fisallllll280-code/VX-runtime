# VX PR Evidence Auditor v0.1

Status: IMPLEMENTED on isolated branch, tests NOT_RUN, integration NOT_CONNECTED.

Focused first job inspired by public Grok Bot profile separation. This is original minimal local logic, not an imported Grok Bot or installed Grok connection.

Inputs: repo, head_sha, checks with actual URLs and conclusions, independent_review, source_access_confirmed, protected_files_changed, merge_requested. The caller is responsible for obtaining authentic GitHub evidence, correctly scoped to the exact SHA. The auditor does not validate that URLs point to authentic evidence: never treat its advisory PASS as sovereign VERIFIED.

Outputs: PASS, BLOCK or HOLD with explicit reasons and evidence URLs. No API calls, writes, merges, deployments, money transfer, or broker connections. Keep Spec Writer, PR Producer and PR Verifier isolated; PR Verifier must receive independent evidence.

Examples:
```python
from vxruntime.pr_auditor import audit_pr
print(audit_pr({"repo":"owner/repo","head_sha":"abc","checks":[]}).verdict) # HOLD
```

Reference sources for future audited adapters:
- https://github.com/HAEGONG/grok-bot-profiles
- https://github.com/jaskirat1616/grok-skills
- https://github.com/galleonlabs/hypergrok-trading-desk

Before any third-party installation: check source, license, pinned commits, permissions, security, cost and approval. Any financial market agent remains simulation/read-only until separately authorized.

Test: `python -m unittest discover -s tests -p 'test_pr_auditor.py' -v`.
