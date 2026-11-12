"""Offline, governed reference agents; no external calls or autonomous effects."""
from __future__ import annotations
from typing import Mapping
from .core import VXRuntime, ExecutionPolicy, ExecutionStatus
from .memory import MemoryVault

AGENTS = {
    "graphify": ("graph_architect", "analyze"),
    "understand-anything": ("code_analyst", "analyze"),
    "claude-obsidian": ("knowledge_curator", "organize"),
    "obsidian-second-brain": ("memory_guardian", "organize"),
    "mcp-obsidian": ("knowledge_gateway", "inspect"),
    "claudesidian": ("vault_designer", "organize"),
    "second-brain": ("wiki_evolution", "organize"),
}

class AgentRunner:
    """Runs bounded local tasks with VX evidence and per-tool memory."""
    def __init__(self, memory_path):
        self.memory = MemoryVault(memory_path)
        self.runtime = VXRuntime(policy=ExecutionPolicy(
            allowed_capabilities=frozenset({
                "agent.local.inspect", "agent.local.analyze", "agent.local.organize"
            })))

    def run(self, agent_id: str, task_id: str, payload: Mapping):
        if agent_id not in AGENTS:
            raise ValueError("UNKNOWN_AGENT")
        if not task_id or not isinstance(payload, Mapping):
            raise ValueError("TASK_ID_AND_MAPPING_REQUIRED")
        specialty, verb = AGENTS[agent_id]
        if any(r["body"].get("task_id") == task_id
               for r in self.memory.recall(agent_id, "result")):
            raise ValueError("TASK_ALREADY_RECORDED")
        result = self.runtime.execute(
            task_id, "agent.local." + verb,
            {"agent_id": agent_id, "payload": dict(payload)},
            lambda inputs: {"agent_id": agent_id, "specialty": specialty,
                            "task_id": task_id, "mode": "LOCAL_SIMULATION",
                            "observations": sorted(inputs["payload"].keys())})
        if result.status is ExecutionStatus.SUCCESS:
            self.memory.remember(agent_id, "result", result.output,
                                 "local-task:" + task_id, "v0.1")
        return result

    def close(self):
        self.memory.close()
