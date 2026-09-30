#!/usr/bin/env python3
"""Legacy v1 compatibility evaluator for adaptive-DE audit records.

This module is retained for backward-compatible regression tests. Its linear
``performance_admissible`` output is not the POCA v3 DAG semantics; use
``audit_cli_v2.py`` for the claim frontier and effective-status derivation.
"""

import argparse
import json
import sys
from pathlib import Path

REQUIRED = {
    "case_id", "source_id", "source_sha256", "runner_id", "task_id",
    "dimension", "seed", "logging_mode", "target_fe", "true_fe",
    "reported_fe", "identity", "budget", "path", "observer", "replay",
    "runnability", "decision",
}
VALID = {"PASS", "FAIL", "INDETERMINATE"}


def evaluate(record):
    missing = sorted(REQUIRED - record.keys())
    if missing:
        raise ValueError("missing fields: " + ", ".join(missing))
    statuses = {key: record[key] for key in
                ("identity", "budget", "path", "observer", "replay", "runnability")}
    invalid = {key: value for key, value in statuses.items() if value not in VALID}
    if invalid:
        raise ValueError("invalid statuses: " + json.dumps(invalid, sort_keys=True))
    expected = "PASS" if all(value == "PASS" for value in statuses.values()) else "FAIL"
    supplied = record["decision"]
    if supplied != expected:
        raise ValueError(f"decision mismatch: supplied={supplied}, expected={expected}")
    if record["true_fe"] < 0 or record["reported_fe"] < 0 or record["target_fe"] < 0:
        raise ValueError("FE values must be non-negative")
    return {"case_id": record["case_id"], "decision": expected,
            "performance_admissible": expected == "PASS",
            "failed_layers": [key for key, value in statuses.items() if value != "PASS"]}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("record", type=Path)
    args = parser.parse_args()
    record = json.loads(args.record.read_text(encoding="utf-8"))
    result = evaluate(record)
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    try:
        main()
    except (OSError, ValueError, json.JSONDecodeError) as error:
        print(f"AUDIT_SCHEMA_ERROR: {error}", file=sys.stderr)
        sys.exit(2)
