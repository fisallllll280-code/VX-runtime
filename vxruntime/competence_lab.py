"""VX Competence Lab: deterministic, human-reviewed skill evaluation.

An evaluation report is evidence of measured tasks only, not general intelligence.
"""
from __future__ import annotations
from dataclasses import dataclass
from typing import Mapping, Sequence
from .core import digest

@dataclass(frozen=True)
class Evaluation:
    candidate: str
    score: float
    baseline_score: float
    eligible: bool
    reasons: tuple[str, ...]
    receipt: str

def evaluate(candidate: str, baseline: Mapping[str, bool], results: Mapping[str, bool],
             evidence: Mapping[str, str], critical: Sequence[str] = ()) -> Evaluation:
    if not candidate or not baseline or set(baseline) != set(results):
        raise ValueError("COMPARABLE_TASK_SET_REQUIRED")
    if any(type(v) is not bool for v in list(baseline.values())+list(results.values())):
        raise ValueError("BOOLEAN_VERDICTS_REQUIRED")
    names=sorted(results)
    base=sum(baseline[k] for k in names)/len(names)
    score=sum(results[k] for k in names)/len(names)
    reasons=[]
    if any(k not in names for k in critical):
        raise ValueError("UNKNOWN_CRITICAL_TASK")
    if any(not isinstance(evidence.get(k),str) or not evidence[k].strip() for k in names):
        reasons.append("EVIDENCE_INCOMPLETE")
    if score <= base:
        reasons.append("NO_MEASURED_IMPROVEMENT")
    if any(not results[k] for k in critical):
        reasons.append("CRITICAL_REGRESSION")
    # Even eligible results are proposals; evidence strings need external verification.
    receipt=digest({"candidate":candidate,"baseline":dict(baseline),
                    "results":dict(results),"evidence":dict(evidence),
                    "critical":list(critical)})
    return Evaluation(candidate,score,base,not reasons,tuple(reasons),receipt)
