"""Health observations for registered VX agents."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone

from .agent_registry import AgentRegistry, AgentLifecycle


@dataclass(frozen=True)
class HealthReport:
    agent_id: str
    healthy: bool
    state: str
    checked_at: str
    reason: str


class HealthMonitor:
    def __init__(self, registry: AgentRegistry) -> None:
        self._registry = registry

    def check(self, agent_id: str) -> HealthReport:
        record = self._registry.get(agent_id)
        task = record.runtime_task
        actor = record.actor_object
        if record.state is not AgentLifecycle.RUNNING:
            healthy, reason = False, f"STATE_{record.state.value}"
        elif task is None:
            healthy, reason = False, "RUNTIME_TASK_MISSING"
        elif task.done():
            healthy, reason = False, "RUNTIME_TASK_TERMINATED"
        elif actor is None or getattr(actor, "state", None) not in {"IDLE", "RUNNING"}:
            healthy, reason = False, "ACTOR_NOT_LIVE"
        else:
            healthy, reason = True, "LIVE_RUNTIME_TASK_AND_ACTOR"
        return HealthReport(
            agent_id=agent_id,
            healthy=healthy,
            state=record.state.value,
            checked_at=datetime.now(timezone.utc).isoformat(),
            reason=reason,
        )
