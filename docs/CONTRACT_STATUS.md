# VX Contract Status

This repository is being moved from specification-only toward an executable contract boundary.

## Current verified scope

- Runtime architecture is documented in README.md.
- The machine-readable contract is stored in contracts/vx_runtime_contract.json.
- The contract defines authority boundaries and mandatory stages.

## Not yet claimed

This file does not claim that a complete VX runtime implementation exists.
Executable runtime behavior must be backed by code and tests before being marked implemented.

## Next implementation gate

1. Implement the ledger boundary.
2. Implement policy-before-execution ordering.
3. Add deterministic replay tests.
4. Add evidence hashing tests.
5. Add a host test proving lifecycle code cannot perform policy decisions.
