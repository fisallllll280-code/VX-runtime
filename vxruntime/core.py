"""Dependency-free VX runtime reference implementation.

The runtime deliberately keeps policy/authorization outside worker functions,
records an append-only event chain, and makes replay a pure verification step.
"""

from __future__ import annotations

from dataclasses import dataclass, asdict
from enum import Enum
import hashlib
import json
from typing import Any, Callable, Mapping


def canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, default=str)


def digest(value: Any) -> str:
    return hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()


class ExecutionStatus(str, Enum):
    SUCCESS = "success"
    FAILED = "failed"
    BLOCKED = "blocked"


@dataclass(frozen=True)
class ExecutionPolicy:
    allowed_capabilities: frozenset[str] = frozenset()
    require_capability: bool = True

    def allows(self, capability: str) -> bool:
        if not self.require_capability:
            return True
        return capability in self.allowed_capabilities


@dataclass(frozen=True)
class Event:
    event_id: str
    event_type: str
    execution_id: str
    capability: str
    payload: Mapping[str, Any]
    previous_hash: str
    event_hash: str

    @staticmethod
    def build(
        event_id: str,
        event_type: str,
        execution_id: str,
        capability: str,
        payload: Mapping[str, Any],
        previous_hash: str,
    ) -> "Event":
        unsigned = {
            "event_id": event_id,
            "event_type": event_type,
            "execution_id": execution_id,
            "capability": capability,
            "payload": dict(payload),
            "previous_hash": previous_hash,
        }
        return Event(
            **unsigned,
            event_hash=digest(unsigned),
        )


class EventLedger:
    """In-memory append-only hash chain suitable for deterministic tests."""

    def __init__(self) -> None:
        self._events: list[Event] = []

    @property
    def events(self) -> tuple[Event, ...]:
        return tuple(self._events)

    def append(self, event: Event) -> str:
        expected_previous = self._events[-1].event_hash if self._events else "GENESIS"
        if event.previous_hash != expected_previous:
            raise ValueError("LEDGER_PREVIOUS_HASH_MISMATCH")
        unsigned = {
            "event_id": event.event_id,
            "event_type": event.event_type,
            "execution_id": event.execution_id,
            "capability": event.capability,
            "payload": dict(event.payload),
            "previous_hash": event.previous_hash,
        }
        if event.event_hash != digest(unsigned):
            raise ValueError("LEDGER_EVENT_HASH_MISMATCH")
        self._events.append(event)
        return event.event_hash

    def verify(self) -> bool:
        previous = "GENESIS"
        for event in self._events:
            if event.previous_hash != previous:
                return False
            unsigned = {
                "event_id": event.event_id,
                "event_type": event.event_type,
                "execution_id": event.execution_id,
                "capability": event.capability,
                "payload": dict(event.payload),
                "previous_hash": event.previous_hash,
            }
            if event.event_hash != digest(unsigned):
                return False
            previous = event.event_hash
        return True


@dataclass(frozen=True)
class Execution:
    execution_id: str
    capability: str
    inputs: Mapping[str, Any]
    output: Any
    input_hash: str
    output_hash: str
    status: ExecutionStatus
    event_hash: str | None = None
    error: str | None = None

    def replay_matches(self, output: Any) -> bool:
        return self.output_hash == digest(output)


class VXRuntime:
    """Governed deterministic execution boundary."""

    def __init__(self, ledger: EventLedger | None = None, policy: ExecutionPolicy | None = None) -> None:
        self.ledger = ledger or EventLedger()
        self.policy = policy or ExecutionPolicy()
        self.history: dict[str, Execution] = {}

    def execute(
        self,
        execution_id: str,
        capability: str,
        inputs: Mapping[str, Any],
        worker: Callable[[Mapping[str, Any]], Any],
    ) -> Execution:
        if not execution_id:
            raise ValueError("EXECUTION_ID_REQUIRED")
        captured_inputs = dict(inputs)
        if not self.policy.allows(capability):
            blocked = Execution(
                execution_id=execution_id,
                capability=capability,
                inputs=captured_inputs,
                output=None,
                input_hash=digest(captured_inputs),
                output_hash=digest(None),
                status=ExecutionStatus.BLOCKED,
                error="CAPABILITY_DENIED",
            )
            self.history[execution_id] = blocked
            self._record(blocked, "EXECUTION_BLOCKED")
            return blocked

        try:
            output = worker(captured_inputs)
            result = Execution(
                execution_id=execution_id,
                capability=capability,
                inputs=captured_inputs,
                output=output,
                input_hash=digest(captured_inputs),
                output_hash=digest(output),
                status=ExecutionStatus.SUCCESS,
            )
            event_hash = self._record(result, "EXECUTION_COMPLETED")
            result = Execution(**{**asdict(result), "event_hash": event_hash})
        except Exception as exc:  # noqa: BLE001
            result = Execution(
                execution_id=execution_id,
                capability=capability,
                inputs=captured_inputs,
                output=None,
                input_hash=digest(captured_inputs),
                output_hash=digest(None),
                status=ExecutionStatus.FAILED,
                error=str(exc),
            )
            self._record(result, "EXECUTION_FAILED")

        self.history[execution_id] = result
        return result

    def replay(
        self,
        execution_id: str,
        worker: Callable[[Mapping[str, Any]], Any],
    ) -> bool:
        original = self.history.get(execution_id)
        if original is None:
            raise KeyError("EXECUTION_NOT_FOUND")
        if original.status is not ExecutionStatus.SUCCESS:
            return False
        replay_output = worker(dict(original.inputs))
        return original.replay_matches(replay_output)

    def verify(self) -> bool:
        return self.ledger.verify()

    def _record(self, execution: Execution, event_type: str) -> str:
        previous = self.ledger.events[-1].event_hash if self.ledger.events else "GENESIS"
        payload = {
            "execution_id": execution.execution_id,
            "input_hash": execution.input_hash,
            "output_hash": execution.output_hash,
            "status": execution.status.value,
            "error": execution.error,
        }
        event = Event.build(
            event_id=f"{execution.execution_id}:{event_type}",
            event_type=event_type,
            execution_id=execution.execution_id,
            capability=execution.capability,
            payload=payload,
            previous_hash=previous,
        )
        return self.ledger.append(event)
