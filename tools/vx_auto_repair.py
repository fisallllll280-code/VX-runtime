"""Bounded test-failure triage and optional repair-adapter runner.

This tool classifies common failure signatures, can pass the captured log to an
explicitly supplied repair adapter, and reruns the test command once. It does
not prove root cause. Use only in an isolated worktree or branch.
"""
from __future__ import annotations
import argparse
import json
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Sequence

RULES = (
    ("IMPORT_ERROR", r"ModuleNotFoundError|ImportError", "Check dependency installation, package layout, and import paths."),
    ("ASSERTION_FAILURE", r"AssertionError|FAILED .*::", "Inspect expected versus actual values and the failing assertion."),
    ("TYPE_ERROR", r"TypeError|AttributeError", "Check value types, interfaces, and None handling."),
    ("TIMEOUT", r"TimeoutError|timed out|Timeout expired", "Inspect waits, external dependencies, and timeout budgets."),
    ("PERMISSION_DENIED", r"PermissionError|Permission denied|EACCES", "Check least-privilege access and runner permissions."),
    ("DEPENDENCY_CONFLICT", r"ResolutionImpossible|dependency conflict|version conflict", "Inspect pinned versions and lockfiles; avoid unbounded upgrades."),
    ("NETWORK_OR_SERVICE", r"ConnectionError|Connection refused|Name or service not known|HTTP 5\\d\\d", "Check service availability and isolate network-dependent tests."),
    ("SYNTAX_ERROR", r"SyntaxError|IndentationError", "Inspect the first syntax error and nearby changed lines."),
    ("SECURITY_OR_POLICY_BLOCK", r"CAPABILITY_DENIED|POLICY_DENIED|blocked by policy", "Treat this as a policy decision; do not bypass the gate."),
)

def classify(log: str) -> list[dict[str, str]]:
    found = []
    for code, pattern, next_step in RULES:
        if re.search(pattern, log, flags=re.IGNORECASE | re.MULTILINE):
            found.append({"code": code, "confidence": "signature_match_not_root_cause_proof", "next_step": next_step})
    if not found:
        found.append({"code": "UNCLASSIFIED_FAILURE", "confidence": "unknown",
                      "next_step": "Review the full log and reproduce in isolation; do not guess a fix."})
    return found

def run(command: Sequence[str], input_text: str | None = None) -> subprocess.CompletedProcess[str]:
    try:
        return subprocess.run(list(command), input=input_text, text=True, capture_output=True, check=False)
    except FileNotFoundError as exc:
        return subprocess.CompletedProcess(list(command), 127, "", f"COMMAND_NOT_FOUND: {exc}")

def main() -> int:
    parser = argparse.ArgumentParser(description="Run tests, classify failures, optionally invoke one repair adapter, then rerun tests.")
    parser.add_argument("--test-command", nargs="+", required=True, help="Test command and arguments; no shell expansion.")
    parser.add_argument("--repair-command", nargs="+", help="Optional trusted adapter; first-run failure log is sent to stdin.")
    parser.add_argument("--report", default="vx-failure-report.json", help="JSON report path.")
    args = parser.parse_args()

    first = run(args.test_command)
    first_log = (first.stdout or "") + "\\n" + (first.stderr or "")
    failures = classify(first_log) if first.returncode else []
    repair_attempted = False
    repair_returncode = None
    final = first
    if first.returncode != 0 and args.repair_command:
        repair_attempted = True
        adapter = run(args.repair_command, input_text=first_log)
        repair_returncode = adapter.returncode
        final = run(args.test_command)

    final_log = (final.stdout or "") + "\\n" + (final.stderr or "")
    report = {
        "schema_version": "1.0.0",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "test_command": list(args.test_command),
        "initial_exit_code": first.returncode,
        "initial_failures": failures,
        "repair_attempted": repair_attempted,
        "repair_command": list(args.repair_command) if args.repair_command else None,
        "repair_adapter_exit_code": repair_returncode,
        "final_exit_code": final.returncode,
        "final_status": "PASS" if final.returncode == 0 else "FAIL",
        "verification_note": "PASS means only that the configured test command exited zero; it does not prove root cause or overall correctness.",
        "final_log_tail": final_log[-12000:],
    }
    report_path = Path(args.report)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\\n", encoding="utf-8")
    print(json.dumps({k: report[k] for k in ("initial_exit_code", "initial_failures", "repair_attempted",
          "repair_adapter_exit_code", "final_exit_code", "final_status")}, indent=2, ensure_ascii=False))
    print(f"Report: {report_path}")
    return 0 if final.returncode == 0 else 1

if __name__ == "__main__":
    sys.exit(main())
