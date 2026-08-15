#!/usr/bin/env python3
"""Evaluate local audit evidence and derive prerequisite-ordered claim status."""

import argparse
import json
import sys
from pathlib import Path

REQUIRED = {
    "case_id", "source_id", "source_sha256", "runner_id", "task_id",
    "dimension", "seed", "logging_mode", "target_fe", "true_fe",
    "reported_fe", "runnability", "identity", "budget", "path",
    "observer", "replay", "control", "incremental_value",
}
LOCAL_STATUS = {"PASS", "FAIL", "INDETERMINATE", "NOT_TESTED"}
BLOCKED = "BLOCKED_BY_UPSTREAM"


def _effective(local_value, prerequisites):
    """Return local status only when every prerequisite has passed."""
    if all(value == "PASS" for value in prerequisites):
        return local_value
    return BLOCKED


def _derive_effective(local):
    """Derive POCA effective statuses from an immutable local-status vector."""
    l0 = local["runnability"]
    l1 = _effective(local["identity"], [l0])
    validity = [local["observer"], local["replay"]]
    l2 = _effective(local["budget"], [l0, l1, *validity])
    l3 = _effective(local["path"], [l0, l1, l2, *validity])
    l4 = _effective(local["control"], [l0, l1, l2, l3, *validity])
    l5 = _effective(local["incremental_value"],
                    [l0, l1, l2, l3, l4, *validity])
    return {
        "L0_runnability": l0,
        "L1_identity": l1,
        "L2_budget": l2,
        "L3_path": l3,
        "L4_control": l4,
        "L5_incremental_value": l5,
    }


def evaluate(record):
    missing = sorted(REQUIRED - record.keys())
    if missing:
        raise ValueError("missing fields: " + ", ".join(missing))

    local = {
        key: record[key]
        for key in (
            "runnability", "identity", "budget", "path", "observer",
            "replay", "control", "incremental_value"
        )
    }
    invalid = {key: value for key, value in local.items()
               if value not in LOCAL_STATUS}
    if invalid:
        raise ValueError("invalid local statuses: "
                         + json.dumps(invalid, sort_keys=True))

    for field in ("target_fe", "true_fe", "reported_fe"):
        if record[field] < 0:
            raise ValueError(f"{field} must be non-negative")

    effective = _derive_effective(local)
    l0 = effective["L0_runnability"]
    l2 = effective["L2_budget"]
    l3 = effective["L3_path"]
    l4 = effective["L4_control"]
    l5 = effective["L5_incremental_value"]
    ordered = list(effective.items())
    highest = "NONE"
    for name, value in ordered:
        if value != "PASS":
            break
        highest = name

    blocking = []
    for key, value in local.items():
        if value != "PASS":
            blocking.append({"condition": key, "status": value})

    execution_admissible = l3 == "PASS"
    control_admissible = execution_admissible and l4 == "PASS"
    incremental_admissible = control_admissible and l5 == "PASS"

    repeated_effective = _derive_effective(dict(local))
    downstream_local = dict(local)
    downstream_local["control"] = "PASS"
    downstream_local["incremental_value"] = "PASS"
    downstream_effective = _derive_effective(downstream_local)
    protocol_properties = {
        "evidence_conservation": local == {
            key: local[key] for key in local
        },
        "idempotence": repeated_effective == effective,
        "blocking_monotonicity": (
            effective["L4_control"] != "PASS"
            or downstream_effective["L4_control"] == effective["L4_control"]
        ),
        "repair_isolation": "enforced_by_new_versioned_case_id",
    }

    return {
        "case_id": record["case_id"],
        "local_status": local,
        "effective_claim_status": effective,
        "highest_admissible_layer": highest,
        "execution_claim_admissible": execution_admissible,
        "control_claim_admissible": control_admissible,
        "incremental_value_claim_admissible": incremental_admissible,
        "blocked_by": blocking,
        "protocol_properties": protocol_properties,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("record", type=Path)
    args = parser.parse_args()
    record = json.loads(args.record.read_text(encoding="utf-8"))
    print(json.dumps(evaluate(record), indent=2, sort_keys=True))


if __name__ == "__main__":
    try:
        main()
    except (OSError, ValueError, json.JSONDecodeError) as error:
        print(f"AUDIT_SCHEMA_ERROR: {error}", file=sys.stderr)
        sys.exit(2)
