from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
from typing import Callable, Mapping, Any
from uuid import uuid4


@dataclass(frozen=True)
class ExecutionRequest:
    objective: str
    inputs: Mapping[str, Any]
    approved: bool
    execution_id: str


@dataclass(frozen=True)
class ExecutionResult:
    execution_id: str
    status: str
    output: Any
    output_hash: str


class VXRuntime:
    """Contract-level runtime: policy is checked before execution."""

    def __init__(self, executor: Callable[[ExecutionRequest], Any]):
        self._executor = executor

    @staticmethod
    def request(objective: str, inputs: Mapping[str, Any], approved: bool) -> ExecutionRequest:
        return ExecutionRequest(objective, dict(inputs), approved, str(uuid4()))

    def execute(self, request: ExecutionRequest) -> ExecutionResult:
        if not request.approved:
            raise PermissionError("policy rejected execution")
        output = self._executor(request)
        digest = sha256(repr(output).encode("utf-8")).hexdigest()
        return ExecutionResult(request.execution_id, "EXECUTED", output, digest)
