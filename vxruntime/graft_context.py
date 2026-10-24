"""Bounded Graft context-graph integration for VX; no auto-install or implicit execution."""
from __future__ import annotations
import hashlib
import json
from pathlib import Path
import subprocess
from typing import Callable

OPERATIONS = {"check", "ask", "map", "build"}
MAX_QUERY = 500


def plan(operation: str, root: str, query: str = "") -> dict:
    directory = Path(root).resolve(strict=True)
    if not directory.is_dir() or not (directory / ".git").exists():
        raise ValueError("GIT_ROOT_REQUIRED")
    if operation not in OPERATIONS:
        raise ValueError("UNAPPROVED_OPERATION")
    if operation == "ask":
        if not isinstance(query, str) or not query.strip() or len(query) > MAX_QUERY:
            raise ValueError("INVALID_QUERY")
        arguments = ["ask", query, "--json"]
    else:
        if query:
            raise ValueError("UNEXPECTED_QUERY")
        arguments = {"check": ["check", "--json"], "map": ["map"],
                     "build": ["build"]}[operation]
    return {"operation": operation, "root": str(directory), "argv": arguments,
            "provider_calls_authorized": False, "network_authorized": False}


def execute(spec: dict, *, approved: bool = False, executable: str | None = None,
            runner: Callable = subprocess.run) -> dict:
    """Host must sandbox Graft: approval here is not strong IAM/network isolation."""
    if not approved:
        return {"status": "BLOCKED", "reason": "APPROVAL_REQUIRED"}
    try:
        if not isinstance(spec, dict):
            raise ValueError("INVALID_SPEC")
        q = spec["argv"][1] if spec.get("operation") == "ask" and len(spec.get("argv", [])) == 3 else ""
        expected = plan(spec["operation"], spec["root"], q)
        if spec != expected:
            raise ValueError("PLAN_TAMPERED")
        # Command path must be independently supplied/pinned by the operator,
        # not derived from model-controlled arguments or PATH search.
        path = Path(executable or "")
        if not executable or not path.is_absolute() or not path.is_file():
            raise ValueError("PINNED_EXECUTABLE_REQUIRED")
    except (ValueError, KeyError, TypeError, OSError, IndexError):
        return {"status": "BLOCKED", "reason": "INVALID_OR_UNPINNED_PLAN"}
    try:
        result = runner([str(path), *spec["argv"]], cwd=spec["root"],
                        timeout=45, capture_output=True, text=True,
                        check=False, env={"PATH": "/usr/bin:/bin", "DO_NOT_TRACK": "1",
                                          "GRAFT_NO_REFRESH": "1"})
        output = (result.stdout or "")[:16000]
        return {"status": "SUCCESS" if result.returncode == 0 else "FAILED",
                "exit_code": result.returncode,
                "output_sha256": hashlib.sha256(output.encode()).hexdigest(),
                "output_excerpt": output[:1500],
                "operation": spec["operation"],
                "external_network_proven_off": False,
                "verification_status": "LOCAL_PROCESS_ONLY"}
    except (OSError, subprocess.TimeoutExpired) as exc:
        return {"status": "FAILED", "reason": type(exc).__name__}
