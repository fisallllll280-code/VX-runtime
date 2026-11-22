# VX Active Objects and Bootstrap workflow

Status: implementation and CI tests are present on the feature branch. Production durability and OS-level isolation are not claimed.

## Implemented modules

- `vxruntime/active_objects.py`: actor-owned mailbox, serialized message handling, payload snapshot, explicit success/failure result, graceful close.
- `vxruntime/agent_registry.py`: lifecycle states and transition events carrying UTC timestamp, actor, and evidence. Connectivity is derived from registry state plus a live runtime task and active actor state.
- `vxruntime/task_scheduler.py`: rejects unconnected agents, duplicate task IDs, and capabilities not declared by the registered agent before mailbox submission.
- `vxruntime/health_monitor.py`: checks lifecycle state, asyncio task liveness, and actor state.
- `vxruntime/runtime/supervisor.py`: fail-closed authorization, startup sequencing, graceful stop, and bounded restart attempts.
- `tests/test_active_objects.py` and `tests/test_vx_workflow.py`: concurrency, payload isolation, failure reporting, authorization rejection, connectivity, health, lifecycle evidence, bounded recovery, and stop behavior.

## Lifecycle

```text
DISCOVERED -> VALIDATED -> AUTHORIZED -> STARTING -> RUNNING
       |           |            |           |
       +--------> FAILED     QUARANTINED   FAILED
RUNNING -> FAILED | STOPPED | QUARANTINED | RECOVERY_PENDING
RECOVERY_PENDING -> STARTING -> RUNNING
RECOVERY_PENDING -> FAILED (recovery budget exhausted)
```

Every lifecycle transition requires an actor identity and non-empty evidence, and records a UTC timestamp. Authorization defaults to deny unless the caller supplies an authorizer that explicitly permits the capability set. A discovered or failed agent is never reported as connected merely because its record exists.

## Workflow contract

```text
Discover agent
 -> validate identity and declared capabilities
 -> explicit authorization
 -> start ActiveObject
 -> bind live runtime task in registry
 -> health-check actual task and actor
 -> capability-gated task dispatch
 -> collect ActorResult
 -> verify result and evidence
 -> stop or bounded recovery
```

An `ActorResult` is not itself proof that the result is correct, and task acceptance is not task completion. A production integration must connect the verification result and execution event to VX's durable evidence ledger before making any VERIFIED or crash-recovery claim.

## Limits / follow-up work

- Mailboxes, registry, lifecycle events, and task-ID sets are in-memory; process crashes lose them.
- The scheduler checks declared agent capabilities, not a complete policy engine or signed authority receipt.
- Recovery restarts the actor within a bounded budget but does not restore unacknowledged messages or promise exactly-once side effects.
- `asyncio` provides cooperative concurrency, not CPU parallelism for blocking handlers.
- Untrusted code needs process/container/VM isolation and OS resource limits.
- Next integration gate: persist transitions and task outcomes into the existing event ledger; then test crash/replay and independent evidence verification.
