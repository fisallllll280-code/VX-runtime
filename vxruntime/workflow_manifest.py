"""Validation for declarative VX-Workflow manifests.

This module validates workflow data only. It never executes commands, tools, or
network requests. Unknown capabilities are rejected when a capability allowlist
is supplied.
"""
from __future__ import annotations

from dataclasses import dataclass
import json
import re
from typing import Any, Iterable

SUPPORTED_VERSION = "1.0"
_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{0,127}$")
_ALLOWED_ROOT = {"workflow_id", "version", "tasks"}
_ALLOWED_TASK = {
    "task_id", "capability", "operation", "depends_on", "inputs",
    "timeout_seconds", "side_effects",
}
_ALLOWED_SIDE_EFFECTS = {"none", "filesystem_read", "filesystem_write", "network", "external_process"}


@dataclass(frozen=True)
class WorkflowValidation:
    valid: bool
    errors: tuple[str, ...]
    normalized: dict[str, Any] | None = None


def _is_id(value: Any) -> bool:
    return isinstance(value, str) and bool(_ID.fullmatch(value))


def validate_workflow(
    manifest: Any,
    *,
    registered_capabilities: Iterable[str] | None = None,
) -> WorkflowValidation:
    """Validate a VX-Workflow v1.0 manifest and return stable, sorted diagnostics."""
    errors: list[str] = []
    if not isinstance(manifest, dict):
        return WorkflowValidation(False, ("ROOT_MUST_BE_OBJECT",))

    unknown_root = sorted(set(manifest) - _ALLOWED_ROOT)
    missing_root = sorted(_ALLOWED_ROOT - set(manifest))
    errors.extend(f"UNKNOWN_ROOT_FIELD:{key}" for key in unknown_root)
    errors.extend(f"MISSING_ROOT_FIELD:{key}" for key in missing_root)

    workflow_id = manifest.get("workflow_id")
    if not _is_id(workflow_id):
        errors.append("INVALID_WORKFLOW_ID")

    version = manifest.get("version")
    if version != SUPPORTED_VERSION:
        errors.append(f"UNSUPPORTED_WORKFLOW_VERSION:{version!r}")

    tasks = manifest.get("tasks")
    if not isinstance(tasks, list) or not tasks:
        errors.append("TASKS_MUST_BE_NONEMPTY_ARRAY")
        tasks = []

    allowed = set(registered_capabilities) if registered_capabilities is not None else None
    seen: set[str] = set()
    parsed: list[dict[str, Any]] = []
    dependency_map: dict[str, list[str]] = {}

    for index, task in enumerate(tasks):
        prefix = f"TASK[{index}]"
        if not isinstance(task, dict):
            errors.append(f"{prefix}:MUST_BE_OBJECT")
            continue
        errors.extend(f"{prefix}:UNKNOWN_FIELD:{key}" for key in sorted(set(task) - _ALLOWED_TASK))
        for field in ("task_id", "capability", "operation", "depends_on", "inputs", "timeout_seconds", "side_effects"):
            if field not in task:
                errors.append(f"{prefix}:MISSING_FIELD:{field}")

        task_id = task.get("task_id")
        if not _is_id(task_id):
            errors.append(f"{prefix}:INVALID_TASK_ID")
            task_id = f"__invalid_{index}"
        elif task_id in seen:
            errors.append(f"DUPLICATE_TASK_ID:{task_id}")
        seen.add(task_id)

        capability = task.get("capability")
        if not _is_id(capability):
            errors.append(f"{prefix}:INVALID_CAPABILITY_ID")
        elif allowed is not None and capability not in allowed:
            errors.append(f"UNREGISTERED_CAPABILITY:{capability}")

        operation = task.get("operation")
        if not _is_id(operation):
            errors.append(f"{prefix}:INVALID_OPERATION")

        deps = task.get("depends_on")
        if not isinstance(deps, list) or any(not _is_id(dep) for dep in deps):
            errors.append(f"{prefix}:DEPENDS_ON_MUST_BE_ID_ARRAY")
            deps = []
        elif len(deps) != len(set(deps)):
            errors.append(f"{prefix}:DUPLICATE_DEPENDENCY")
        dependency_map[task_id] = list(deps)

        inputs = task.get("inputs")
        if not isinstance(inputs, dict):
            errors.append(f"{prefix}:INPUTS_MUST_BE_OBJECT")
            inputs = {}

        timeout = task.get("timeout_seconds")
        if isinstance(timeout, bool) or not isinstance(timeout, (int, float)) or timeout <= 0:
            errors.append(f"{prefix}:TIMEOUT_MUST_BE_POSITIVE_NUMBER")

        effects = task.get("side_effects")
        if not isinstance(effects, list) or any(effect not in _ALLOWED_SIDE_EFFECTS for effect in effects):
            errors.append(f"{prefix}:INVALID_SIDE_EFFECTS")
            effects = []
        elif len(effects) != len(set(effects)):
            errors.append(f"{prefix}:DUPLICATE_SIDE_EFFECT")

        parsed.append({
            "task_id": task_id,
            "capability": capability,
            "operation": operation,
            "depends_on": sorted(deps),
            "inputs": inputs,
            "timeout_seconds": timeout,
            "side_effects": sorted(effects),
        })

    task_ids = {task["task_id"] for task in parsed}
    for task_id, deps in dependency_map.items():
        for dep in deps:
            if dep not in task_ids:
                errors.append(f"UNKNOWN_DEPENDENCY:{task_id}:{dep}")
            if dep == task_id:
                errors.append(f"SELF_DEPENDENCY:{task_id}")

    # Detect cycles deterministically with a three-color DFS.
    graph = {task_id: [dep for dep in deps if dep in task_ids] for task_id, deps in dependency_map.items()}
    visiting: set[str] = set()
    visited: set[str] = set()
    cycle_nodes: set[str] = set()

    def visit(node: str) -> None:
        if node in visiting:
            cycle_nodes.add(node)
            return
        if node in visited:
            return
        visiting.add(node)
        for dep in sorted(graph.get(node, [])):
            if dep in visiting:
                cycle_nodes.update({node, dep})
            else:
                visit(dep)
        visiting.remove(node)
        visited.add(node)

    for node in sorted(graph):
        visit(node)
    if cycle_nodes:
        errors.append("DEPENDENCY_CYCLE:" + ",".join(sorted(cycle_nodes)))

    stable_errors = tuple(sorted(set(errors)))
    if stable_errors:
        return WorkflowValidation(False, stable_errors)

    normalized = {
        "workflow_id": workflow_id,
        "version": version,
        "tasks": sorted(parsed, key=lambda item: item["task_id"]),
    }
    return WorkflowValidation(True, (), normalized)


def parse_workflow_json(
    source: str,
    *,
    registered_capabilities: Iterable[str] | None = None,
) -> WorkflowValidation:
    """Parse JSON and validate it, returning a stable error rather than raising."""
    try:
        manifest = json.loads(source)
    except (TypeError, json.JSONDecodeError):
        return WorkflowValidation(False, ("INVALID_JSON",))
    return validate_workflow(manifest, registered_capabilities=registered_capabilities)
