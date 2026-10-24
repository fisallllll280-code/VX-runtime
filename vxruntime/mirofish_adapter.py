"""Fail-closed MiroFish simulation adapter. No live calls without external authority.

Matches upstream MiroFish /api/simulation/create (POST) contract.
Only mocked transport is used in tests. The adapter never starts paid LLM jobs.
"""
from __future__ import annotations
from typing import Callable, Mapping, Any
from urllib.parse import urlparse
from .core import VXRuntime, ExecutionPolicy, ExecutionStatus

CAPABILITY = "mirofish.simulation.create.v1"
UPSTREAM = "https://github.com/666ghj/MiroFish"
PATH = "/api/simulation/create"


def submit_simulation(
    execution_id: str,
    payload: Mapping[str, Any],
    *,
    approval: bool = False,
    budget_sar: float = 0,
    endpoint: str = "http://127.0.0.1:5001",
    transport: Callable[[str, dict], dict] | None = None,
) -> dict:
    """Explicit simulation-creation boundary; network transport never implicit."""
    valid = (
        type(approval) is bool and approval
        and type(budget_sar) in (int, float) and budget_sar == 0
        and isinstance(payload, Mapping)
        and isinstance(payload.get("project_id"), str)
        and bool(payload["project_id"].strip())
        and len(payload["project_id"]) <= 128
        and set(payload) <= {"project_id", "graph_id", "enable_twitter", "enable_reddit"}
        and all(isinstance(payload[k], bool) for k in ("enable_twitter", "enable_reddit") if k in payload)
        and ("graph_id" not in payload or isinstance(payload["graph_id"], str))
        and callable(transport)
        and isinstance(endpoint, str)
        and urlparse(endpoint).scheme == "http"
        and urlparse(endpoint).hostname in ("127.0.0.1", "localhost")
        and urlparse(endpoint).port == 5001
        and urlparse(endpoint).username is None
        and urlparse(endpoint).password is None
        and urlparse(endpoint).path in ("", "/")
        and urlparse(endpoint).query == ""
        and urlparse(endpoint).fragment == ""
    )
    runtime = VXRuntime(policy=ExecutionPolicy(
        allowed_capabilities=frozenset({CAPABILITY}) if valid else frozenset()
    ))
    def worker(data):
        response = transport(endpoint + PATH, data)
        if not isinstance(response, dict) or response.get("success") is not True:
            raise ValueError("MIROFISH_RESPONSE_NOT_SUCCESS")
        detail = response.get("data")
        if not isinstance(detail, dict) or not isinstance(detail.get("simulation_id"), str):
            raise ValueError("MIROFISH_SIMULATION_ID_MISSING")
        if detail.get("project_id") != data["project_id"]:
            raise ValueError("MIROFISH_PROJECT_MISMATCH")
        return {"simulation_id": detail["simulation_id"], "project_id": detail["project_id"],
                "status": detail.get("status", "unknown")}
    # Never include credentials or unbounded inputs in ledger receipts.
    inputs = dict(payload) if isinstance(payload, Mapping) else {}
    result = runtime.execute(execution_id, CAPABILITY, inputs, worker)
    return {"execution_id": execution_id, "status": result.status.value,
            "error": result.error, "output": result.output if result.status is ExecutionStatus.SUCCESS else None,
            "input_sha256": result.input_hash, "output_sha256": result.output_hash,
            "ledger_sha256": runtime.ledger.events[-1].event_hash, "ledger_valid": runtime.verify(),
            "external_spend_sar": 0, "canonical_write": False,
            "simulation_completed": False, "prediction_verified": False}
