"""Command-line entry point for the read-only VX Apple host preflight.

Run from the repository root:
    python -m vxruntime.apple_preflight --output-dir "$env:USERPROFILE\\Desktop\\VX-Diagnostics"
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path

from .apple_device import AppleDeviceAdapter, DetectionStatus


def main() -> int:
    parser = argparse.ArgumentParser(description="Read-only Windows Apple device preflight")
    parser.add_argument("--output-dir", default=str(Path.home() / "Desktop" / "VX-Diagnostics"))
    args = parser.parse_args()

    adapter = AppleDeviceAdapter()
    report = adapter.discover()
    update_plan = adapter.prepare_update_plan(report)
    output_dir = Path(args.output_dir).expanduser()
    output_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    payload = {
        "schema": "vx.apple-device-preflight.v1",
        "discovery": report.to_dict(),
        "update_plan": update_plan,
        "safety": {
            "device_modified": False,
            "driver_modified": False,
            "network_used": False,
            "update_executed": False,
            "restore_executed": False,
        },
    }
    destination = output_dir / f"vx-apple-preflight-{stamp}.json"
    destination.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(json.dumps({
        "status": report.status.value,
        "device_interfaces": len(report.devices),
        "update_plan": update_plan["status"],
        "report_path": str(destination),
    }, ensure_ascii=False))
    return 0 if report.status is not DetectionStatus.UNAVAILABLE else 2


if __name__ == "__main__":
    raise SystemExit(main())
