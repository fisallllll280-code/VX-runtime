# VX ONE — Runtime Loader Adapter Contract v1

**Status:** PROPOSED / ADAPTER CONTRACT ONLY  
**Execution boundary:** VX-runtime  
**Shared loader candidate:** VAIXLNS-unified PR #71

## Responsibility

VX-runtime is the controlled execution and evidence boundary for future platform-specific loader adapters. It must not duplicate the catalog, canonical system identity, or manifest schema owned by the shared VX ONE loader.

## Adapter stages

1. Accept a pinned manifest and artifact identity.
2. Revalidate manifest schema, source host, digest, signature, version, and freshness.
3. Check platform compatibility without changing firmware or storage.
4. Produce a deterministic preflight receipt.
5. Require explicit human authorization before any staging operation.
6. Execute only in an isolated test target until the relevant adapter is independently reviewed.
7. Capture boot measurements and post-boot observations where the platform supports them.
8. Preserve recovery and rollback evidence.

## Fail-closed rules

- No network retrieval unless a future bounded downloader is separately admitted.
- No shell command assembled from manifest strings.
- No direct disk, partition, EFI-variable, TPM ownership, Secure Boot key, or reboot action in this contract.
- A hash match without signature verification is not authenticity.
- A successful VM boot is not proof of physical-hardware compatibility.
- A requested reboot or install cannot be inferred from a general execute capability.

## Current boundary

This file is a design contract. It does not add an executable platform adapter, download images, create USB media, install an OS, or claim a boot event. Existing replay/rollback mechanisms remain separate and must be connected through explicit evidence-bearing interfaces.
