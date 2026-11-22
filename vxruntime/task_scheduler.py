"""Capability-gated dispatch to live VX Active Objects."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

from .active_objects import AgentMessage
from .agent_registry import AgentRegistry


@dataclass(frozen=True)
class DispatchReceipt:
    task_id: str
    agent_id: str
    capability: str
    accepted: bool
    timestamp: str
    evidence: str


class TaskScheduler:
    def __init__(self, registry: AgentRegistry) -> None:
        self._registry = registry
        self._task_ids: set[str] = set()

    async def dispatch(
        self,
        *,
        agent_id: str,
        task_id: str,
        capability: str,
        operation: str,
        payload: dict[str, Any],
    ) -> DispatchReceipt:
        if not task_id.strip():
            raise ValueError("TASK_ID_REQUIRED")
        if task_id in self._task_ids:
            raise ValueError("SCHEDULED_TASK_ID_ALREADY_USED")
        record = self._registry.get(agent_id)
        if not self._registry.is_connected(agent_id):
            raise RuntimeError("AGENT_NOT_CONNECTED")
        if capability not in record.capabilities:
            raise PermissionError("CAPABILITY_DENIED")
        if not operation.strip():
            raise ValueError("OPERATION_REQUIRED")

        # Reserve the ID before enqueueing; rejected submissions are not reported accepted.
        self._task_ids.add(task_id)
        try:
            await record.actor_object.submit(
                AgentMessage(task_id=task_id, operation=operation, payload=dict(payload))
            )
        except Exception:
            self._task_ids.discard(task_id)
            raise
        return DispatchReceipt(
            task_id=task_id,
            agent_id=agent_id,
            capability=capability,
            accepted=True,
            timestamp=datetime.now(timezone.utc).isoformat(),
            evidence="mailbox submission accepted by live registered actor",
        )
