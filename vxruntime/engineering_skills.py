"""VX engineering skill router. Explicit, audited workflow definitions only.

Skill names are guidance, not executed programs or remote instructions.
"""
from dataclasses import dataclass
from .core import digest

WORKFLOWS = {
    "clarify": ("grill-with-docs", "to-spec"),
    "design": ("domain-modeling", "codebase-design", "to-spec"),
    "plan": ("to-spec", "to-tickets"),
    "implement": ("tdd", "review", "pr"),
    "debug": ("triage", "tdd", "review"),
    "review": ("review", "pr"),
    "handoff": ("handoff",),
}
# Only confirmed, configured operations may ever map to local skill handlers.
# This registry stores names and decision order; no npx, Claude subprocess or remote install.
@dataclass(frozen=True)
class SkillRoute:
    intent: str
    steps: tuple[str, ...]
    state: str
    provenance: str
    fingerprint: str

def route(intent: str, *, source_ref: str, source_version: str) -> SkillRoute:
    if intent not in WORKFLOWS:
        raise ValueError("UNRECOGNIZED_ENGINEERING_INTENT")
    if not source_ref or not source_version:
        raise ValueError("SOURCE_PIN_REQUIRED")
    steps = WORKFLOWS[intent]
    source = f"{source_ref}@{source_version}"
    return SkillRoute(intent, steps, "PROPOSED", source,
                      digest({"intent": intent, "steps": steps, "source": source}))
