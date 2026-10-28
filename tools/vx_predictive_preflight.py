"""Predictive preflight for proposed code changes; no code execution or auto-merge."""
from __future__ import annotations
import argparse
import json
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import PurePosixPath

PROTECTED_NAMES = {"project.genome", "Ω.000"}
RULES = (
    ("BLOCK", "SECRET_LITERAL", re.compile(r"(?i)(api[_-]?key|secret|password|access[_-]?token)\s*[:=]\s*['\"][^'\"]{8,}['\"]"), "Remove the literal credential and rotate it if real; use secret storage."),
    ("BLOCK", "DYNAMIC_CODE_EXECUTION", re.compile(r"\b(eval|exec)\s*\("), "Replace dynamic code execution with explicit, typed operations."),
    ("HIGH", "SHELL_TRUE", re.compile(r"subprocess\.(run|Popen|call|check_output)\([^\n]*shell\s*=\s*True"), "Prefer an argv list and shell=False; validate all arguments."),
    ("HIGH", "UNSAFE_DESERIALIZATION", re.compile(r"\bpickle\.(load|loads)\s*\("), "Do not deserialize untrusted data with pickle."),
    ("MEDIUM", "BROAD_EXCEPTION", re.compile(r"except\s+Exception\s*:"), "Catch expected exception types or document why the broad boundary is safe."),
    ("MEDIUM", "UNBOUNDED_SUBPROCESS", re.compile(r"subprocess\.(run|Popen|call|check_output)\("), "Review timeout, cancellation, output limits, and process cleanup."),
)

def analyze_diff(changed_paths: list[str], diff_text: str) -> dict:
    findings = []
    protected = [p for p in changed_paths if PurePosixPath(p).name in PROTECTED_NAMES]
    for path in protected:
        findings.append({"severity": "BLOCK", "code": "PROTECTED_CANON_CHANGED", "path": path,
                         "message": "Protected canonical file must not be changed."})
    for severity, code, pattern, advice in RULES:
        for match in pattern.finditer(diff_text):
            line = diff_text.count("\n", 0, match.start()) + 1
            findings.append({"severity": severity, "code": code, "line_in_diff": line,
                             "message": advice, "matched_text": match.group(0)[:100]})
    source_paths = [p for p in changed_paths if p.endswith((".py", ".ts", ".tsx", ".js", ".go", ".rs")) and not p.startswith("tests/")]
    test_paths = [p for p in changed_paths if p.startswith(("tests/", "test/")) or PurePosixPath(p).name.startswith("test_")]
    if source_paths and not test_paths:
        findings.append({"severity": "MEDIUM", "code": "NO_TEST_CHANGED", "paths": source_paths[:20],
                         "message": "Source changed without a corresponding test change; assess regression coverage."})
    blocking = any(f["severity"] == "BLOCK" for f in findings)
    high = any(f["severity"] == "HIGH" for f in findings)
    return {
        "schema_version": "1.0.0",
        "status": "BLOCKED" if blocking else ("REVIEW_REQUIRED" if high or findings else "PREFLIGHT_CLEAR"),
        "changed_paths": changed_paths,
        "findings": findings,
        "decision_note": "Static heuristics only: a clear result is not proof of correctness or absence of defects.",
    }

def git_output(args: list[str]) -> str:
    result = subprocess.run(args, text=True, capture_output=True, check=False, timeout=30)
    if result.returncode:
        raise RuntimeError((result.stderr or result.stdout or "git command failed").strip())
    return result.stdout

def main() -> int:
    parser = argparse.ArgumentParser(description="Inspect proposed diff for known engineering risks before tests.")
    parser.add_argument("--base-ref", default="origin/main", help="Git ref to compare against.")
    parser.add_argument("--report", default="vx-preflight-report.json")
    args = parser.parse_args()
    try:
        paths = [p for p in git_output(["git", "diff", "--name-only", f"{args.base_ref}...HEAD"]).splitlines() if p]
        diff = git_output(["git", "diff", "--unified=0", f"{args.base_ref}...HEAD", "--", *paths]) if paths else ""
    except (RuntimeError, subprocess.TimeoutExpired) as exc:
        print(f"PRECHECK_ERROR: {exc}", file=sys.stderr)
        return 2
    report = analyze_diff(paths, diff)
    report["generated_at"] = datetime.now(timezone.utc).isoformat()
    with open(args.report, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
        f.write("\n")
    print(json.dumps({"status": report["status"], "changed_files": len(paths), "findings": report["findings"]}, ensure_ascii=False, indent=2))
    return 1 if report["status"] == "BLOCKED" else 0

if __name__ == "__main__":
    sys.exit(main())
