# VX Apple Device Adapter v1

**Status:** IMPLEMENTED / HOST PnP READ-ONLY PROTOTYPE; PHYSICAL iPhone 17 NOT VERIFIED  
**Repository:** VX-runtime  
**Execution boundary:** VX capability layer  
**Target host:** Windows  
**Protected canonical assets:** `project.genome` and `Ω.000` are out of scope and must not be modified.

## Scope

The first vertical slice queries present Windows Plug-and-Play devices matching Apple's USB vendor ID or Apple/iPhone/iBoot/Recovery/DFU labels. It hashes the PnP instance identifier before recording it and never persists the raw identifier. It distinguishes:

- `DETECTED`: exactly one matching PnP interface was returned (not proof of a fully usable iPhone session).
- `NOT_DETECTED`: query succeeded and returned no matching interfaces.
- `AMBIGUOUS`: multiple matching interfaces require correlation; no update plan is admitted.
- `UNAVAILABLE`: the host query could not be completed; this is not equivalent to no device.

Mode classification is conservative. A label containing DFU is classified as DFU; Recovery/iBoot as Recovery. A generic Apple USB interface remains UNKNOWN and is not promoted to NORMAL.

## Safety boundary

The adapter is read-only. It does not:

- install, update, remove, or repair Windows drivers;
- install Apple Devices, iTunes, Python packages, or other software;
- pair/trust/unlock the iPhone or read user content;
- download firmware or contact Apple endpoints;
- call Apple Devices/iTunes update or restore commands;
- erase data, reboot, change firmware, or bypass Activation Lock.

Update planning returns `PREPARED_NOT_EXECUTED` only for an unambiguous single-device observation in NORMAL or RECOVERY mode. It is a plan receipt, not a command. A separate human approval and a separately reviewed execution adapter are required before opening the official Apple update flow. Restore remains outside this adapter and is prohibited by default.

## Known limitations

Windows PnP labels are not a complete Apple protocol implementation. The initial adapter does not yet establish Lockdown pairing, query the iPhone product type/build version, distinguish all USB interfaces belonging to one physical device, or cryptographically attest device identity. Multiple matching PnP rows are deliberately AMBIGUOUS until a tested correlation strategy exists.

The iPhone 17 model claim must come from an authenticated Apple device session or another trusted source; it must not be inferred from USB vendor/product identifiers alone. Recovery/DFU observations must be validated on physical hardware before any VERIFIED claim.

## Test map

- `vxruntime/apple_device.py`
- `tests/test_apple_device.py`

Local deterministic tests use a fake PnP provider. They validate classification, serial redaction, fail-closed behavior, and the non-executable update-plan boundary. They do not prove Windows USB discovery or iPhone compatibility.

## Acceptance gates

1. CI compiles the runtime and passes the adapter tests.
2. A Windows host preflight produces a timestamped report without raw serial exposure.
3. A physical iPhone 17 is observed and independently confirmed as that model.
4. Recovery and DFU classification are tested separately on hardware where safely available.
5. The update plan is reviewed; actual Update requires a separate explicit user approval at the time of action.
6. Independent verification confirms the adapter did not invoke update/restore, mutate drivers, or modify canonical assets.

No merge, release, deployment, spend, restore, or data-erasure action is authorized by this specification.
