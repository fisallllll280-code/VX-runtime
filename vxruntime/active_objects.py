"""Small asyncio Active Object primitive for the VX runtime.

Each actor owns its mailbox and processes one message at a time. This provides
logical state isolation and per-actor serialization, not an OS security sandbox.
"""
from __future__ import annotations

import asyncio
import copy
from dataclasses import dataclass
from typing import Any, Awaitable, Callable


@dataclass(frozen=True)
class AgentMessage:
    task_id: str
    operation: str
    payload: dict[str, Any]


@dataclass(frozen=True)
class ActorResult:
    actor_id: str
    task_id: str
    ok: bool
    value: Any = None
    error_code: str | None = None
    error: str | None = None


Handler = Callable[[AgentMessage], Awaitable[Any]]
_STOP = object()


class ActiveObject:
    """A long-lived actor with an owned mailbox and serialized message handling."""

    def __init__(self, actor_id: str, handler: Handler) -> None:
        if not actor_id.strip():
            raise ValueError("ACTOR_ID_REQUIRED")
        self.actor_id = actor_id
        self._handler = handler
        self._mailbox: asyncio.Queue[AgentMessage | object] = asyncio.Queue()
        self._results: asyncio.Queue[ActorResult] = asyncio.Queue()
        self._accepted_task_ids: set[str] = set()
        self._accepting = True
        self._started = False
        self._closed = asyncio.Event()
        self.state = "CREATED"

    def start(self) -> asyncio.Task[None]:
        """Start the actor once and return its lifecycle task."""
        if self._started:
            raise RuntimeError("ACTOR_ALREADY_STARTED")
        if not self._accepting:
            raise RuntimeError("ACTOR_ALREADY_CLOSED")
        self._started = True
        self.state = "IDLE"
        return asyncio.create_task(self.run(), name=f"vx-actor:{self.actor_id}")

    async def submit(self, message: AgentMessage) -> None:
        """Enqueue a unique task message after taking an owned payload snapshot."""
        if not self._accepting:
            raise RuntimeError("ACTOR_NOT_ACCEPTING")
        if not message.task_id.strip():
            raise ValueError("TASK_ID_REQUIRED")
        if message.task_id in self._accepted_task_ids:
            raise ValueError("TASK_ID_ALREADY_ACCEPTED")
        if not message.operation.strip():
            raise ValueError("OPERATION_REQUIRED")
        snapshot = AgentMessage(
            task_id=message.task_id,
            operation=message.operation,
            payload=copy.deepcopy(message.payload),
        )
        self._accepted_task_ids.add(message.task_id)
        self._mailbox.put_nowait(snapshot)

    async def next_result(self) -> ActorResult:
        """Wait for the next completed message result."""
        return await self._results.get()

    async def wait_idle(self) -> None:
        """Wait until all currently queued messages have been handled."""
        await self._mailbox.join()

    async def close(self) -> None:
        """Stop accepting new work and enqueue a graceful stop marker."""
        if not self._accepting:
            return
        self._accepting = False
        if self._started:
            self._mailbox.put_nowait(_STOP)
        else:
            self.state = "CLOSED"
            self._closed.set()

    async def run(self) -> None:
        """Consume messages sequentially; handler failures become explicit results."""
        try:
            while True:
                item = await self._mailbox.get()
                try:
                    if item is _STOP:
                        self.state = "CLOSED"
                        return
                    assert isinstance(item, AgentMessage)
                    self.state = "RUNNING"
                    try:
                        value = await self._handler(item)
                    except Exception as exc:
                        self._results.put_nowait(
                            ActorResult(
                                actor_id=self.actor_id,
                                task_id=item.task_id,
                                ok=False,
                                error_code="HANDLER_FAILED",
                                error=f"{type(exc).__name__}: {exc}",
                            )
                        )
                    else:
                        self._results.put_nowait(
                            ActorResult(
                                actor_id=self.actor_id,
                                task_id=item.task_id,
                                ok=True,
                                value=value,
                            )
                        )
                finally:
                    self._mailbox.task_done()
                if self._accepting:
                    self.state = "IDLE"
        finally:
            self.state = "CLOSED"
            self._closed.set()
