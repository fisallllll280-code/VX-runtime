import asyncio

import pytest

from vxruntime.active_objects import ActiveObject, AgentMessage


def test_actor_serializes_messages_and_returns_results():
    async def scenario():
        active = 0
        maximum_active = 0

        async def handler(message):
            nonlocal active, maximum_active
            active += 1
            maximum_active = max(maximum_active, active)
            await asyncio.sleep(0.01)
            active -= 1
            return {"seen": message.payload["value"]}

        actor = ActiveObject("agent-A", handler)
        task = actor.start()
        await actor.submit(AgentMessage("task-1", "inspect", {"value": 1}))
        await actor.submit(AgentMessage("task-2", "inspect", {"value": 2}))
        await actor.wait_idle()
        first = await actor.next_result()
        second = await actor.next_result()
        await actor.close()
        await task

        assert maximum_active == 1
        assert [(first.task_id, first.ok), (second.task_id, second.ok)] == [
            ("task-1", True), ("task-2", True)
        ]
        assert actor.state == "CLOSED"

    asyncio.run(scenario())


def test_actor_snapshots_payload_at_submission():
    async def scenario():
        gate = asyncio.Event()

        async def handler(message):
            await gate.wait()
            return message.payload["nested"]["items"]

        actor = ActiveObject("agent-snapshot", handler)
        task = actor.start()
        payload = {"nested": {"items": [1]}}
        await actor.submit(AgentMessage("task-snapshot", "inspect", payload))
        payload["nested"]["items"].append(2)
        gate.set()
        await actor.wait_idle()
        result = await actor.next_result()
        await actor.close()
        await task

        assert result.ok
        assert result.value == [1]

    asyncio.run(scenario())


def test_handler_failure_is_reported_and_actor_keeps_processing():
    async def scenario():
        async def handler(message):
            if message.task_id == "task-bad":
                raise RuntimeError("expected test failure")
            return "ok"

        actor = ActiveObject("agent-resilient", handler)
        task = actor.start()
        await actor.submit(AgentMessage("task-bad", "run", {}))
        await actor.submit(AgentMessage("task-good", "run", {}))
        await actor.wait_idle()
        failed = await actor.next_result()
        succeeded = await actor.next_result()
        await actor.close()
        await task

        assert not failed.ok
        assert failed.error_code == "HANDLER_FAILED"
        assert "expected test failure" in failed.error
        assert succeeded.ok and succeeded.value == "ok"

    asyncio.run(scenario())


def test_duplicate_task_id_is_rejected_without_overwriting_first_message():
    async def scenario():
        async def handler(message):
            return message.payload["value"]

        actor = ActiveObject("agent-unique", handler)
        task = actor.start()
        await actor.submit(AgentMessage("task-unique", "run", {"value": 1}))
        with pytest.raises(ValueError, match="TASK_ID_ALREADY_ACCEPTED"):
            await actor.submit(
                AgentMessage("task-unique", "run", {"value": 999})
            )
        await actor.wait_idle()
        result = await actor.next_result()
        await actor.close()
        await task

        assert result.value == 1

    asyncio.run(scenario())


def test_actor_rejects_submission_after_close():
    async def scenario():
        async def handler(message):
            return message.task_id

        actor = ActiveObject("agent-closed", handler)
        task = actor.start()
        await actor.close()
        await task
        with pytest.raises(RuntimeError, match="ACTOR_NOT_ACCEPTING"):
            await actor.submit(AgentMessage("task-late", "run", {}))

    asyncio.run(scenario())
