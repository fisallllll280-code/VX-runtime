"""Command-line entry point for supervised read-only Android inspection."""
from __future__ import annotations

import argparse
import json
import sys

from vxruntime.android_adb import AdbError, ReadOnlyAdbBridge


def main() -> int:
    parser = argparse.ArgumentParser(description="VX read-only Android ADB inspector")
    parser.add_argument("--serial", required=True, help="Exact ADB device serial")
    parser.add_argument("--adb-path", default="adb", help="Path to adb executable")
    args = parser.parse_args()

    try:
        report = ReadOnlyAdbBridge(
            serial=args.serial,
            adb_path=args.adb_path,
        ).inspect()
    except (AdbError, ValueError) as exc:
        print(json.dumps({"status": "BLOCKED", "reason": str(exc)}), file=sys.stderr)
        return 2

    print(json.dumps({"status": "INSPECTED", "mode": "READ_ONLY", "device": report}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
