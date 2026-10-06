# VX Repository Contract

- System ID: VX
- Repository: fisallllll280-code/VX-runtime
- Role: GOVERNED EXECUTION RUNTIME
- Family: Execution
- State: IMPLEMENTED

## Authority
VX owns the execution boundary. VAIXLNS owns federation authority and canonical admission.

## Evidence boundary
The deterministic VX runtime reference core is implemented and tested. Production-scale deployment remains outside this evidence scope.

## Required invariants
Policy precedes capability execution; execution identities are stable; inputs/outputs are evidence-bearing; failed or unverified work is not VERIFIED; replay uses original execution inputs; evolution remains proposal/verification gated.

## Verification Evidence

- Implementation commits: `320751ff1c0852346e465729a01e3f96071616a1`, `8e05377eb81865794821348f690dc0e665303857`, `9f1fafbdda547392892893dfdc814ba0514c6221`
- CI run: `37391569335` — SUCCESS
- Coverage: governed execution, capability policy, append-only event hash chain, replay comparison, ledger verification.
- Epistemic state: IMPLEMENTED + TESTED; governed admission remains pending.

## Admission
No runtime claim is promoted to VERIFIED without executable evidence and governed admission.
