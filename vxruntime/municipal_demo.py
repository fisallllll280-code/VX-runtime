"""Reproducible LOCAL_TEST batch, benchmark and receipt integrity checks.

Run: python -m vxruntime.municipal_demo --output-dir /tmp/vx-municipal-test
"""
from __future__ import annotations

import argparse
from dataclasses import asdict
import json
from pathlib import Path
import platform
import statistics
import time

from .agent_runner import AgentRunner, HostGrant
from .core import Event, EventLedger, canonical_json, digest
from .municipal import AGENT, CAPABILITY, CHECKS, DataPolicy, check_readiness


def verify_receipt(receipt: dict) -> bool:
    """Integrity only, not an authenticated attestation or government acceptance."""
    try:
        body = {k: v for k, v in receipt.items()
                if k not in {"receipt_hash", "deduplicated"}}
        if digest(body) != receipt["receipt_hash"] or receipt["status"] != "SUCCESS":
            return False
        ledger = EventLedger()
        for raw in receipt["events"]:
            ledger.append(Event(**raw))
        if len(ledger.events) != 1:
            return False
        event = ledger.events[0]
        return (
            ledger.verify() and event.execution_id == receipt["task_key"]
            and event.capability == CAPABILITY
            and event.event_type == "EXECUTION_COMPLETED"
            and event.payload["status"] == "success"
            and event.payload["input_hash"] == receipt["input_hash"]
            and event.payload["output_hash"] == receipt["output_hash"]
            and digest(receipt["output"]) == receipt["output_hash"]
        )
    except (KeyError, TypeError, ValueError):
        return False


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True, mode=0o700)
    now = time.time()
    # Synthetic host fixture, never a production identity or permission grant.
    grant = HostGrant(AGENT, "VX-HOST-AUTHORITY", CAPABILITY, int(now) + 300, True)
    policy = DataPolicy(notice_reviewed=True, processing_basis_reviewed=True)
    runner = AgentRunner(args.output_dir / "receipts.sqlite3", policy=policy, grants=(grant,))
    complete = dict.fromkeys(CHECKS, True)
    incomplete = {**complete, "risk_mitigation": False, "measurable_kpis": False}
    a = runner.run("1" * 32, complete, deadline_epoch=now + 120)
    b = runner.run("2" * 32, incomplete, deadline_epoch=now + 120)
    duplicate = runner.run("1" * 32, complete, deadline_epoch=now + 120)
    conflict = runner.run("1" * 32, incomplete, deadline_epoch=now + 120)
    rejected = runner.run("3" * 32, {"applicant_name": "SYNTHETIC_REJECT_ME"},
                          deadline_epoch=now + 120)
    denied = AgentRunner(args.output_dir / "receipts.sqlite3", policy=policy).run(
        "4" * 32, complete, deadline_epoch=now + 120)
    assert a["status"] == b["status"] == "SUCCESS"
    assert a["output"]["status"] == "READY_FOR_REVIEW"
    assert b["output"]["missing"] == ["measurable_kpis", "risk_mitigation"]
    assert duplicate["deduplicated"] is True
    assert conflict["reason"] == "IDEMPOTENCY_CONFLICT"
    assert rejected["reason"] == "FACT_SCHEMA_DENIED"
    assert denied["reason"] == "AUTHORITY_DENIED"
    assert verify_receipt(a) and verify_receipt(b)
    cases = ((complete, "READY_FOR_REVIEW"), (incomplete, "INCOMPLETE"))
    durations, errors = [], 0
    for index in range(1000):
        facts, expected = cases[index % 2]
        start = time.perf_counter_ns()
        actual = check_readiness(facts)
        durations.append((time.perf_counter_ns() - start) / 1_000_000)
        errors += actual["status"] != expected
    logs = [a, b, duplicate, conflict, rejected, denied]
    (args.output_dir / "execution.jsonl").write_text(
        "\n".join(canonical_json(item) for item in logs) + "\n", encoding="utf-8")
    summary = {
        "environment": "LOCAL_TEST", "synthetic_host_grant": True,
        "python": platform.python_version(), "platform": platform.platform(),
        "scenarios_passed": 6, "receipt_integrity_checks": 2,
        "benchmark_scope": "pure local presence checker; excludes DB, network and human work",
        "benchmark_requests": 1000, "fixture_label_errors": errors,
        "latency_ms_p50": statistics.median(durations),
        "latency_ms_p95": sorted(durations)[949],
        "host_policy": asdict(policy), "live_government_e2e": "NOT_RUN",
        "production_gate": "HOLD", "external_spend_sar": 0,
        "execution_log_sha256": __import__("hashlib").sha256(
            (args.output_dir / "execution.jsonl").read_bytes()).hexdigest(),
    }
    (args.output_dir / "metrics.json").write_text(
        json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
