"""Lifecycle registry for VX agents; connectivity is derived from live runtime evidence."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any


class AgentLifecycle(str, Enum):
    DISCOVERED = "DISCOVERED"
    VALIDATED = "VALIDATED"
    AUTHORIZED = "AUTHORIZED"
    STARTING = "STARTING"
    RUNNING = "RUNNING"
    FAILED = "FAILED"
    STOPPED = "STOPPED"
    QUARANTINED = "QUARANTINED"
    RECOVERY_PENDING = "RECOVERY_PENDING"


_ALLOWED_TRANSITIONS = {
    AgentLifecycle.DISCOVERED: {AgentLifecycle.VALIDATED, AgentLifecycle.FAILED},
    AgentLifecycle.VALIDATED: {AgentLifecycle.AUTHORIZED, AgentLifecycle.FAILED},
    AgentLifecycle.AUTHORIZED: {AgentLifecycle.STARTING, AgentLifecycle.QUARANTINED},
    AgentLifecycle.STARTING: {AgentLifecycle.RUNNING, AgentLifecycle.FAILED},
    AgentLifecycle.RUNNING: {
        AgentLifecycle.FAILED, AgentLifecycle.STOPPED,
        AgentLifecycle.QUARANTINED, AgentLifecycle.RECOVERY_PENDING,
    },
    AgentLifecycle.FAILED: {AgentLifecycle.RECOVERY_PENDING, AgentLifecycle.STOPPED},
    AgentLifecycle.RECOVERY_PENDING: {
        AgentLifecycle.STARTING, AgentLifecycle.FAILED, AgentLifecycle.STOPPED,
    },
    AgentLifecycle.QUARANTINED: {AgentLifecycle.STOPPED},
    AgentLifecycle.STOPPED: set(),
}


@dataclass(frozen=True)
class LifecycleEvent:
    agent_id: str
    previous: AgentLifecycle | None
    current: AgentLifecycle
    timestamp: str
    actor: str
    evidence: str


@dataclass
class AgentRecord:
    agent_id: str
    capabilities: frozenset[str]
    state: AgentLifecycle = AgentLifecycle.DISCOVERED
    actor_object: Any = None
    runtime_task: Any = None
    restart_count: int = 0
    events: list[LifecycleEvent] = field(default_factory=list)

    @property
    def connected(self) -> bool:
        task_live = self.runtime_task is not None and not self.runtime_task.done()
        actor_live = (
            self.actor_object is not None
            and getattr(self.actor_object, "state", None) in {"IDLE", "RUNNING"}
        )
        return self.state is AgentLifecycle.RUNNING and task_live and actor_live


class AgentRegistry:
    def __init__(self) -> None:
        self._agents: dict[str, AgentRecord] = {}

    def discover(self, agent_id: str, capabilities: set[str] | frozenset[str]) -> AgentRecord:
        if not agent_id.strip():
            raise ValueError("AGENT_ID_REQUIRED")
        if agent_id in self._agents:
            raise ValueError("AGENT_ID_ALREADY_REGISTERED")
        if any(not item.strip() for item in capabilities):
            raise ValueError("INVALID_CAPABILITY")
        record = AgentRecord(agent_id=agent_id, capabilities=frozenset(capabilities))
        self._agents[agent_id] = record
        self._append_event(record, None, AgentLifecycle.DISCOVERED, "registry", "discovery request accepted")
        return record

    def transition(
        self,
        agent_id: str,
        target: AgentLifecycle,
        *,
        actor: str,
        evidence: str,
    ) -> LifecycleEvent:
        record = self.get(agent_id)
        if not actor.strip() or not evidence.strip():
            raise ValueError("TRANSITION_REQUIRES_ACTOR_AND_EVIDENCE")
        if target not in _ALLOWED_TRANSITIONS[record.state]:
            raise ValueError(f"INVALID_LIFECYCLE_TRANSITION:{record.state.value}->{target.value}")
        previous = record.state
        record.state = target
        return self._append_event(record, previous, target, actor, evidence)

    def attach_runtime(self, agent_id: str, actor_object: Any, runtime_task: Any) -> None:
        record = self.get(agent_id)
        if record.state is not AgentLifecycle.STARTING:
            raise ValueError("RUNTIME_BINDING_REQUIRES_STARTING_STATE")
        if runtime_task is None or runtime_task.done():
            raise ValueError("RUNTIME_TASK_NOT_LIVE")
        if getattr(actor_object, "state", None) not in {"IDLE", "RUNNING"}:
            raise ValueError("ACTOR_NOT_LIVE")
        record.actor_object = actor_object
        record.runtime_task = runtime_task

    def get(self, agent_id: str) -> AgentRecord:
        try:
            return self._agents[agent_id]
        except KeyError as exc:
            raise KeyError("AGENT_NOT_FOUND") from exc

    def is_connected(self, agent_id: str) -> bool:
        return self.get(agent_id).connected

    def all(self) -> tuple[AgentRecord, ...]:
        return tuple(self._agents.values())

    @staticmethod
    def _append_event(
        record: AgentRecord,
        previous: AgentLifecycle | None,
        current: AgentLifecycle,
        actor: str,
        evidence: str,
    ) -> LifecycleEvent:
        event = LifecycleEvent(
            agent_id=record.agent_id,
            previous=previous,
            current=current,
            timestamp=datetime.now(timezone.utc).isoformat(),
            actor=actor,
            evidence=evidence,
        )
        record.events.append(event)
        return event
