"""VX agent relationship analyzer: candidate overlaps, coverage and activation gates.

Read-only deterministic projection. Similarity is NOT identity equivalence.
"""
from __future__ import annotations
import json
import re
from collections import defaultdict
from pathlib import Path

STOP={"agent","engineer","engineering","and","the","system","review","specialist","vx"}
ALIASES={"verification":"verify","verifier":"verify","testing":"test","tests":"test",
"architecture":"architect","architectural":"architect","innovation":"innovate",
"innovator":"innovate","source":"discover","discovery":"discover",
"research":"research","runtime":"execute","executor":"execute",
"execution":"execute","governance":"govern","security":"secure",
"recovery":"recover","index":"index","auditor":"audit","analysis":"analyze"}

def tokens(name: str) -> set[str]:
    terms=re.findall(r"[a-zA-Z]+",name.lower())
    return {ALIASES.get(t,t) for t in terms if t not in STOP and len(t)>2}

def analyze(roster: dict) -> dict:
    sources=roster.get("sources")
    if not isinstance(sources,list):
        raise ValueError("sources must be a list")
    items=[]
    for group in sources:
        for item in group.get("entries",[]):
            name=item.get("name")
            if not isinstance(name,str) or not name.strip():
                raise ValueError("agent names must be nonempty")
            items.append({"key":f"{group['repository']}::{group['group']}::{item.get('id') or name}",
                          "name":name,"repository":group["repository"],"source_path":group["path"],
                          "terms":tokens(name)})
    links=[]
    for i,a in enumerate(items):
        for b in items[i+1:]:
            overlap=sorted(a["terms"] & b["terms"])
            if overlap:
                links.append({"left":a["key"],"right":b["key"],"shared_terms":overlap,
                              "relation":"OVERLAP_CANDIDATE_NOT_IDENTITY"})
    groups=defaultdict(list)
    for a in items:
        for term in a["terms"]:
            groups[term].append(a["key"])
    return {"schema":"vx.agent.reconciliation.v1","entries":len(items),
            "candidate_links":links,
            "capability_terms":{k:sorted(v) for k,v in sorted(groups.items())},
            "uncovered_requested_capabilities":[k for k in ("physics","mathematics","finance","simulate","deploy") if k not in groups],
            "activation_state":"HOLD_NOT_LIVE_PROBED",
            "identity_merges":0,"authorized_runtime_agents":0,
            "decision":"REVIEW_CAPABILITY_CONTRACTS_BEFORE_ACTIVATION"}

def main() -> int:
    import argparse
    p=argparse.ArgumentParser()
    p.add_argument("roster",type=Path)
    p.add_argument("--out",required=True,type=Path)
    args=p.parse_args()
    result=analyze(json.loads(args.roster.read_text(encoding="utf-8")))
    args.out.parent.mkdir(parents=True,exist_ok=True)
    args.out.write_text(json.dumps(result,ensure_ascii=False,sort_keys=True,indent=2)+"\n",encoding="utf-8")
    return 0

if __name__=="__main__":
    raise SystemExit(main())
