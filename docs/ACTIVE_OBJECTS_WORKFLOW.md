# VX Active Objects workflow (implementation slice)

Status: **implemented on a feature branch; execution evidence pending**.

## Contract

- Each `ActiveObject` owns a mailbox and handles one message at a time.
- Each accepted task ID is unique within that actor instance; duplicate IDs are rejected instead of silently replacing work.
- Payloads are deep-copied at submission so later caller mutation cannot rewrite the queued input.
- Handler exceptions become explicit `ActorResult(ok=False, error_code="HANDLER_FAILED")` records. They do not terminate the actor's message loop.
- Graceful close rejects new submissions and queues a stop marker behind already accepted work.
- Results are process-local and in-memory in this first slice. This is not durable delivery, exactly-once execution, cross-process isolation, or a security sandbox.

## Workflow

```text
Intent / Task
    -> Scheduler validates task identity and capability
    -> Agent mailbox accepts immutable-by-ownership message snapshot
    -> ActiveObject serializes handler execution
    -> ActorResult records success or failure
    -> Verification checks result and required evidence
    -> Ledger records verified transition
```

The scheduler, capability policy, durable ledger, and verification gate remain separate responsibilities. An actor result is not itself proof that the task is correct, authorized, or VERIFIED.

## Suggested integration sequence

1. Add a bounded scheduler that routes only contract-valid messages to registered actors.
2. Add execution identity and capability checks before submission.
3. Persist accepted messages and results through the existing VX event ledger before claiming crash recovery.
4. Add supervisor health checks, cancellation policy, and restart semantics.
5. Add integration tests for ledger replay, authorization denial, cancellation, and worker restart.
6. Run the complete repository test suite and CI; attach the resulting run URL and commit SHA before promoting the implementation status.

## Limits

- A single actor is sequential; throughput comes from multiple actors and a bounded scheduler.
- `asyncio` provides cooperative concurrency, not CPU parallelism for blocking handlers.
- Process isolation is required for untrusted code or stronger fault/security boundaries.
- In-memory queues lose pending work on process failure. Durable queue/ledger integration is a separate required step for recovery guarantees.
