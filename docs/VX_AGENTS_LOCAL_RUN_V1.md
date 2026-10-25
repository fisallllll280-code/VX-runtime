# VX Seven-Agent Local Simulation v0.1

Implemented on a non-main feature branch, not deployed, not VERIFIED.

This is a bounded, **local simulation**, not installation, authentication, or execution of Graphify, Obsidian, Claude, MCP or any other external agent. Named agents are VX role definitions, not third-party integrations. No secrets, network calls, commits, autonomous changes, or external spend.

`AgentRunner` uses the existing `VXRuntime` capability policy, event chain and `MemoryVault` SQLite persistence. The seven IDs are listed in `AGENTS`. Memory is tool-scoped and task IDs are reserved in the current execution ledger.

Quick local smoke test:
```bash
python -m unittest discover -s tests -p 'test_agents.py' -v
```

For production: require globally unique task IDs across processes, persistent event ledger, transactionally atomic idempotency keys, stable replay, scoped ACLs, human admission, sandboxing, and external adapter review. This demonstration does not solve concurrent dedup or crash-atomic task completion; do not expose as production gateway.
