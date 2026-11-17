# VX Supervised Android Device Control — v0.1

**Status:** IMPLEMENTED (policy boundary + adapter contract) / NOT CONNECTED (physical Android device) / NOT VERIFIED ON DEVICE.

## Objective
Provide a fail-closed, supervised control boundary for Android diagnostics and
approved repairs while preserving the existing VX runtime as the execution core.

## Current implementation
- `vxruntime/device_control.py` defines typed device operations, request-bound
  approval receipts, a fail-closed policy, and an injected Android adapter contract.
- `tests/test_device_control.py` verifies read-only inspection, mutation blocking,
  exact-request approval binding, one-time approval use, and permanent denial of root.
- No Android transport, ADB session, Accessibility service, Device Owner agent,
  privileged service, or physical-device connection is included in this change.

## Permission model
| Operation | Default policy |
|---|---|
| Basic diagnostics | Allowed read-only |
| Settings repair | Explicit human approval |
| Package installation | Explicit human approval |
| Data deletion | Explicit human approval |
| Reboot | Explicit human approval |
| Root access | Denied |

Approval must be issued by a trusted host after an authenticated user action.
A Python object or UI flag alone is not a production trust boundary. Production
integration must bind the approval to the exact request, parameters, device
identity, expiry, and a one-time nonce, with durable audit evidence.

## Required next integration gates
1. Identify the target Android device and supported OS/API level.
2. Select and threat-model the bridge: user-authorized ADB, a signed companion
   app, or a managed-device agent. Do not silently enable Accessibility or root.
3. Implement only read-only inventory first; capture device identity minimally.
4. Add reversible repair operations one at a time, each with preview, approval,
   rollback plan, and postcondition verification.
5. Add tamper-evident audit persistence and replay tests.
6. Run tests in CI and a physical-device test matrix before any RUNNING/VERIFIED claim.

## Safety invariants
- No unapproved mutation.
- No destructive operation by default.
- No root escalation.
- No hidden persistence, surveillance, or remote-control channel.
- No device data exfiltration; diagnostics must be minimised and locally scoped.
- A failed or unobserved repair is never recorded as successful.
- No change to `project.genome` or `Ω.000`.

## Evidence classification
- Policy boundary and tests: IMPLEMENTED in this branch.
- Android bridge: NOT IMPLEMENTED.
- Physical-device execution: NOT RUN.
- Device repair verification: NOT RUN.
- Production readiness: HOLD.
