"""Bounded supervisor for VX Active Objects.

Authorization fails closed. Recovery is explicit and bounded; no deployment or
external side effect is performed by this module.
"""
from __future__ import annotations

import asyncio
from typing import Callable

from ..active_objects import ActiveObject, Handler
from ..agent_registry import AgentLifecycle, AgentRecord, AgentRegistry
from ..health_monitor import HealthMonitor


Authorizer = Callable[[str, frozenset[str]], bool]


class Supervisor:
    def __init__(
        self,
        registry: AgentRegistry | None = None,
        *,
        authorizer: Authorizer | None = None,
        max_restarts: int = 1,
    ) -> None:
        if max_restarts < 0:
            raise ValueError("MAX_RESTARTS_MUST_BE_NONNEGATIVE")
        self.registry = registry or AgentRegistry()
        self.health = HealthMonitor(self.registry)
        self._authorizer = authorizer or (lambda _agent_id, _capabilities: False)
        self._max_restarts = max_restarts
        self._handlers: dict[str, Handler] = {}

    async def launch(
        self,
        agent_id: str,
        capabilities: set[str] | frozenset[str],
        handler: Handler,
    ) -> AgentRecord:
        record = self.registry.discover(agent_id, capabilities)
        self._handlers[agent_id] = handler
        self.registry.transition(
            agent_id, AgentLifecycle.VALIDATED, actor="supervisor",
            evidence="agent ID and capability declarations passed structural validation",
        )
        if not self._authorizer(agent_id, record.capabilities):
            self.registry.transition(
                agent_id, AgentLifecycle.FAILED, actor="policy_gate",
                evidence="authorization denied; actor was not started",
            )
            raise PermissionError("AGENT_AUTHORIZATION_DENIED")

        self.registry.transition(
            agent_id, AgentLifecycle.AUTHORIZED, actor="policy_gate",
            evidence="authorizer explicitly allowed the declared capability set",
        )
        await self._start_runtime(agent_id, handler)
        return self.registry.get(agent_id)

    async def _start_runtime(self, agent_id: str, handler: Handler) -> None:
        record = self.registry.get(agent_id)
        self.registry.transition(
            agent_id, AgentLifecycle.STARTING, actor="supervisor",
            evidence="runtime startup requested after authorization",
        )
        try:
            actor = ActiveObject(agent_id, handler)
            runtime_task = actor.start()
            await asyncio.sleep(0)
            self.registry.attach_runtime(agent_id, actor, runtime_task)
            if not self.health.check(agent_id).reason in {
                "LIVE_RUNTIME_TASK_AND_ACTOR", "STATE_STARTING"
            }:
                raise RuntimeError("RUNTIME_HEALTH_CHECK_FAILED")
            self.registry.transition(
                agent_id, AgentLifecycle.RUNNING, actor="health_monitor",
                evidence="live asyncio task and active-object state observed",
            )
        except Exception as exc:
            if record.state is AgentLifecycle.STARTING:
                self.registry.transition(
                    agent_id, AgentLifecycle.FAILED, actor="supervisor",
                    evidence=f"startup failed: {type(exc).__name__}: {exc}",
                )
            raise

    async def recover(self, agent_id: str) -> bool:
        record = self.registry.get(agent_id)
        health = self.health.check(agent_id)
        if health.healthy:
            return True
        if record.state is AgentLifecycle.RUNNING:
            self.registry.transition(
                agent_id, AgentLifecycle.RECOVERY_PENDING, actor="supervisor",
                evidence=f"health check failed: {health.reason}",
            )
        elif record.state is AgentLifecycle.FAILED:
            self.registry.transition(
                agent_id, AgentLifecycle.RECOVERY_PENDING, actor="supervisor",
                evidence="bounded recovery requested after recorded failure",
            )
        elif record.state is not AgentLifecycle.RECOVERY_PENDING:
            return False

        if record.restart_count >= self._max_restarts:
            self.registry.transition(
                agent_id, AgentLifecycle.FAILED, actor="supervisor",
                evidence="recovery budget exhausted; no further restart attempted",
            )
            return False

        record.restart_count += 1
        try:
            await self._start_runtime(agent_id, self._handlers[agent_id])
        except Exception:
            return False
        return self.health.check(agent_id).healthy

    async def stop(self, agent_id: str) -> None:
        record = self.registry.get(agent_id)
        actor = record.actor_object
        runtime_task = record.runtime_task
        if actor is not None:
            await actor.close()
        if runtime_task is not None and not runtime_task.done():
            await runtime_task
        elif runtime_task is not None and runtime_task.cancelled():
            pass

        if record.state is not AgentLifecycle.STOPPED:
            self.registry.transition(
                agent_id, AgentLifecycle.STOPPED, actor="supervisor",
                evidence="stop requested; runtime task is no longer active",
            )
