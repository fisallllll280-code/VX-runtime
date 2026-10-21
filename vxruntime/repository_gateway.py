"""Governed, read-only GitHub repository metadata adapter for existing VXRuntime."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Callable
from urllib.request import Request, urlopen
import json

from .core import VXRuntime, ExecutionPolicy, ExecutionStatus

OWNER = "fisallllll280-code"
KNOWN = frozenset({"VAIXLNS", "verbose-engine", "VAIXLNS-unified", "VX-runtime", "NEXENT", "NAXLNS", "quickstart-resources"})
CAPABILITY = "github.repository.read_metadata.v1"


@dataclass(frozen=True)
class ReadGrant:
    repository: str
    capability: str
    approved: bool = False


def github_metadata_fetch(repo: str) -> dict:
    request = Request(
        f"https://api.github.com/repos/{OWNER}/{repo}",
        headers={"Accept": "application/vnd.github+json", "User-Agent": "VX-ReadGateway/1"},
    )
    with urlopen(request, timeout=8) as response:
        data = json.load(response)
    return {
        "full_name": data["full_name"],
        "default_branch": data["default_branch"],
        "private": bool(data["private"]),
        "archived": bool(data["archived"]),
    }


def governed_repository_read(
    execution_id: str,
    grant: ReadGrant,
    fetcher: Callable[[str], dict] = github_metadata_fetch,
) -> dict:
    """Executes only an explicitly permitted read; evidence is local and ephemeral."""
    repo = grant.repository
    allowed = (
        type(repo) is str
        and repo in KNOWN
        and grant.capability == CAPABILITY
        and grant.approved is True
    )
    runtime = VXRuntime(policy=ExecutionPolicy(
        allowed_capabilities=frozenset({CAPABILITY}) if allowed else frozenset()
    ))

    def worker(inputs):
        metadata = fetcher(inputs["repository"])
        if not isinstance(metadata, dict) or metadata.get("full_name") != f"{OWNER}/{repo}":
            raise ValueError("REPOSITORY_IDENTITY_MISMATCH")
        if not isinstance(metadata.get("default_branch"), str) or not metadata["default_branch"]:
            raise ValueError("INVALID_REPOSITORY_METADATA")
        return metadata

    result = runtime.execute(execution_id, CAPABILITY, {"repository": repo}, worker)
    return {
        "execution_id": execution_id,
        "repository": repo,
        "status": result.status.value,
        "error": result.error,
        "metadata": result.output if result.status is ExecutionStatus.SUCCESS else None,
        "input_digest": result.input_hash,
        "output_digest": result.output_hash,
        "event_digest": runtime.ledger.events[-1].event_hash,
        "ledger_valid": runtime.verify(),
        "federation_edge_activated": False,
        "canonical_write": False,
        "live_connection_verified": False,
    }
