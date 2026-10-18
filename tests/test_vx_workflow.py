import asyncio

import pytest

from vxruntime.agent_registry import AgentLifecycle, AgentRegistry
from vxruntime.health_monitor import HealthMonitor
from vxruntime.runtime.supervisor import Supervisor
from vxruntime.task_scheduler import TaskScheduler


def test_bootstrap_dispatch_health_and_clean_stop():
    async def scenario():
        async def handler(message):
            return {"task_id": message.task_id, "value": message.payload["value"]}

        supervisor = Supervisor(
            authorizer=lambda _agent_id, capabilities: "task.execute" in capabilities,
            max_restarts=1,
        )
        record = await supervisor.launch("agent-boot", {"task.execute"}, handler)
        assert record.connected
        assert [event.current for event in record.events] == [
            AgentLifecycle.DISCOVERED,
            AgentLifecycle.VALIDATED,
            AgentLifecycle.AUTHORIZED,
            AgentLifecycle.STARTING,
            AgentLifecycle.RUNNING,
        ]

        scheduler = TaskScheduler(supervisor.registry)
        receipt = await scheduler.dispatch(
            agent_id="agent-boot",
            task_id="task-boot-1",
            capability="task.execute",
            operation="echo",
            payload={"value": 42},
        )
        assert receipt.accepted
        await record.actor_object.wait_idle()
        result = await record.actor_object.next_result()
        assert result.ok and result.value == {"task_id": "task-boot-1", "value": 42}
        assert HealthMonitor(supervisor.registry).check("agent-boot").healthy

        await supervisor.stop("agent-boot")
        assert supervisor.registry.get("agent-boot").state is AgentLifecycle.STOPPED
        assert not supervisor.registry.is_connected("agent-boot")

    asyncio.run(scenario())


def test_unauthorized_agent_is_never_started_or_reported_connected():
    async def scenario():
        async def handler(_message):
            raise AssertionError("unauthorized handler must never run")

        supervisor = Supervisor(authorizer=lambda _agent_id, _caps: False)
        with pytest.raises(PermissionError, match="AGENT_AUTHORIZATION_DENIED"):
            await supervisor.launch("agent-denied", {"dangerous.write"}, handler)

        record = supervisor.registry.get("agent-denied")
        assert record.state is AgentLifecycle.FAILED
        assert record.actor_object is None
        assert record.runtime_task is None
        assert not record.connected
        assert record.events[-1].evidence == "authorization denied; actor was not started"

    asyncio.run(scenario())


def test_scheduler_rejects_unauthorized_capability_and_unconnected_agent():
    async def scenario():
        async def handler(message):
            return message.task_id

        supervisor = Supervisor(authorizer=lambda _agent_id, _caps: True)
        record = await supervisor.launch("agent-limited", {"read.only"}, handler)
        scheduler = TaskScheduler(supervisor.registry)

        with pytest.raises(PermissionError, match="CAPABILITY_DENIED"):
            await scheduler.dispatch(
                agent_id="agent-limited", task_id="task-denied",
                capability="system.admin", operation="mutate", payload={},
            )

        record.runtime_task.cancel()
        with pytest.raises(asyncio.CancelledError):
            await record.runtime_task
        with pytest.raises(RuntimeError, match="AGENT_NOT_CONNECTED"):
            await scheduler.dispatch(
                agent_id="agent-limited", task_id="task-offline",
                capability="read.only", operation="read", payload={},
            )

    asyncio.run(scenario())


def test_supervisor_recovers_once_then_fails_closed_when_budget_exhausted():
    async def scenario():
        async def handler(message):
            return message.task_id

        supervisor = Supervisor(authorizer=lambda _agent_id, _caps: True, max_restarts=1)
        record = await supervisor.launch("agent-recover", {"task.execute"}, handler)

        record.runtime_task.cancel()
        with pytest.raises(asyncio.CancelledError):
            await record.runtime_task
        assert not supervisor.health.check("agent-recover").healthy
        assert await supervisor.recover("agent-recover")
        assert record.restart_count == 1
        assert record.connected

        record.runtime_task.cancel()
        with pytest.raises(asyncio.CancelledError):
            await record.runtime_task
        assert not await supervisor.recover("agent-recover")
        assert record.state is AgentLifecycle.FAILED
        assert not record.connected
        assert "recovery budget exhausted" in record.events[-1].evidence

        await supervisor.stop("agent-recover")
        assert record.state is AgentLifecycle.STOPPED

    asyncio.run(scenario())


def test_lifecycle_transitions_require_actor_and_evidence():
    registry = AgentRegistry()
    registry.discover("agent-lifecycle", {"read.only"})
    with pytest.raises(ValueError, match="TRANSITION_REQUIRES_ACTOR_AND_EVIDENCE"):
        registry.transition(
            "agent-lifecycle", AgentLifecycle.VALIDATED, actor="", evidence=""
        )
    with pytest.raises(ValueError, match="INVALID_LIFECYCLE_TRANSITION"):
        registry.transition(
            "agent-lifecycle", AgentLifecycle.RUNNING,
            actor="test", evidence="not authorized",
        )

    record = registry.get("agent-lifecycle")
    assert record.state is AgentLifecycle.DISCOVERED
    assert record.events[0].timestamp
    assert record.events[0].evidence

    with pytest.raises(KeyError, match="AGENT_NOT_FOUND"):
        registry.is_connected("not-registered")

