# Android ADB Read-Only Bridge

Status: IMPLEMENTED AS A HOST-SIDE ADAPTER; NOT CONNECTED TO A PHYSICAL DEVICE.

The `vxruntime/android_adb.py` adapter pins one device serial and exposes only
read-only inventory calls: device state, model, manufacturer, Android release,
battery diagnostics, and /data storage. It does not expose arbitrary shell
commands, install/uninstall, reboot, file transfer, settings mutation, or root.

## Host setup
1. Install official Android SDK Platform-Tools on a trusted Windows/Linux/macOS host.
2. Enable Developer options and USB debugging only if the owner chooses to do so.
3. Connect the phone by USB and approve the host's RSA debugging prompt on-device.
4. Run `adb devices -l` locally and identify the exact serial.
5. Invoke the VX adapter with that serial. Never accept a serial from an untrusted remote caller.

Wireless debugging is intentionally out of scope for the first connection.
USB debugging increases device attack surface; disable it after the supervised
diagnostic session if it is no longer needed.

## Acceptance evidence
- Unit tests mock the subprocess boundary and assert the command allowlist.
- A real-device run must separately record device state, model, Android version,
  battery output, storage output, timestamp, and output hashes.
- No physical-device test has been performed by this repository change.

## Next gate
After the owner confirms the exact handset model and host computer, add a
device-specific repair capability with preview, exact-request approval, rollback,
and postcondition verification. Do not use ADB shell as a general-purpose agent.
