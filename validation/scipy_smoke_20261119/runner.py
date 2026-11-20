#!/usr/bin/env python3
"""Run one pinned SciPy DE accounting and observer smoke test."""

import argparse
import csv
import json
import platform
import shutil
import sys
from pathlib import Path

import numpy as np
import scipy
from scipy.optimize import differential_evolution

from verify_evidence import _hash_file, verify_manifest


SEED = 20261119
DIMENSION = 3
POPULATION_MULTIPLIER = 4
MAXITER = 3


def _run(record_calls):
    generator = np.random.default_rng(SEED)
    before = json.dumps(generator.bit_generator.state, sort_keys=True)
    calls = []
    call_count = 0

    def objective(vector):
        nonlocal call_count
        call_count += 1
        if record_calls:
            calls.append({
                "schema_version": "poca-call-1.0",
                "campaign_id": "scipy-smoke-20261119",
                "run_id": "scipy-smoke-logged",
                "call_index": call_count,
                "caller": "objective",
            })
        return float(np.dot(vector, vector))

    result = differential_evolution(
        objective,
        [(-5.0, 5.0)] * DIMENSION,
        rng=generator,
        maxiter=MAXITER,
        popsize=POPULATION_MULTIPLIER,
        tol=0.0,
        atol=0.0,
        workers=1,
        vectorized=False,
        updating="deferred",
        polish=False,
        disp=False,
    )
    after = json.dumps(generator.bit_generator.state, sort_keys=True)
    return result, call_count, calls, before, after


def _write_json(path, value):
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _artifact(root, path, role, mode):
    return {"path": path, "role": role, "hash_mode": mode,
            "sha256": _hash_file(Path(root) / path, mode)}


def run(output_dir):
    output_dir = Path(output_dir).resolve()
    if output_dir.exists() and any(output_dir.iterdir()):
        raise FileExistsError("output directory is not empty: " + str(output_dir))
    output_dir.mkdir(parents=True, exist_ok=True)

    objective_spec = {
        "objective_id": "sphere-3d-v1",
        "definition": "sum(x_i squared)",
        "dimension": DIMENSION,
        "bounds": [[-5.0, 5.0]] * DIMENSION,
    }
    config = {
        "seed": SEED, "maxiter": MAXITER, "popsize": POPULATION_MULTIPLIER,
        "tol": 0.0, "atol": 0.0, "workers": 1, "vectorized": False,
        "updating": "deferred", "polish": False,
        "init": "latinhypercube-default", "strategy": "best1bin-default",
        "budget_policy": "upper_bound",
    }
    _write_json(output_dir / "objective_spec.json", objective_spec)
    _write_json(output_dir / "config.json", config)
    shutil.copy2(Path(__file__), output_dir / "runner.py")

    baseline, baseline_calls, unused_base_log, base_before, base_after = _run(False)
    traced, traced_calls, call_log, trace_before, trace_after = _run(True)
    maximum_calls = (MAXITER + 1) * POPULATION_MULTIPLIER * DIMENSION
    comparisons = {
        "scipy_version": scipy.__version__,
        "python_version": platform.python_version(),
        "platform": platform.platform(),
        "baseline_nfev": int(baseline.nfev),
        "traced_nfev": int(traced.nfev),
        "traced_wrapper_calls": traced_calls,
        "conditional_maximum_call_count": maximum_calls,
        "same_nfev": int(baseline.nfev) == int(traced.nfev),
        "same_nit": int(baseline.nit) == int(traced.nit),
        "same_best_value": float(baseline.fun) == float(traced.fun),
        "same_best_position": bool(np.array_equal(baseline.x, traced.x)),
        "same_final_population": bool(np.array_equal(baseline.population, traced.population)),
        "same_population_energies": bool(np.array_equal(baseline.population_energies,
                                                         traced.population_energies)),
        "same_rng_before": base_before == trace_before,
        "same_rng_after": base_after == trace_after,
        "wrapper_matches_nfev": traced_calls == int(traced.nfev),
        "within_conditional_maximum": traced_calls <= maximum_calls,
        "call_indices_contiguous": [item["call_index"] for item in call_log]
                                      == list(range(1, traced_calls + 1)),
    }
    comparison_keys = [key for key, value in comparisons.items() if key.startswith("same_")]
    comparisons["observer_comparison_pass"] = (
        all(comparisons[key] for key in comparison_keys)
        and comparisons["wrapper_matches_nfev"]
        and comparisons["within_conditional_maximum"]
        and comparisons["call_indices_contiguous"]
    )
    if not comparisons["observer_comparison_pass"]:
        _write_json(output_dir / "baseline_comparison.json", comparisons)
        raise RuntimeError("SciPy logging comparison failed; see baseline_comparison.json")

    with (output_dir / "calls.jsonl").open("w", encoding="utf-8", newline="") as stream:
        for item in call_log:
            stream.write(json.dumps(item, sort_keys=True) + "\n")
    result_row = {
        "campaign_id": "scipy-smoke-20261119",
        "run_id": "scipy-smoke-logged",
        "result_row_id": "scipy-row-logged",
        "source_id": "sphere-objective-spec-v1",
        "source_sha256": _hash_file(output_dir / "objective_spec.json", "text-lf-v1"),
        "runner_id": "poca-scipy-smoke-v1",
        "task_id": "sphere-3d",
        "dimension": str(DIMENSION),
        "seed": str(SEED),
        "logging_mode": "objective-call-jsonl",
        "run_status": "completed",
        "target_fe": str(maximum_calls),
        "reported_fe": str(int(traced.nfev)),
        "solver_nfev": str(int(traced.nfev)),
    }
    result_fields = list(result_row)
    with (output_dir / "results.csv").open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=result_fields, lineterminator="\n")
        writer.writeheader()
        writer.writerow(result_row)

    artifacts = [
        _artifact(output_dir, "objective_spec.json", "source", "text-lf-v1"),
        _artifact(output_dir, "runner.py", "runner", "text-lf-v1"),
        _artifact(output_dir, "config.json", "configuration", "text-lf-v1"),
        _artifact(output_dir, "results.csv", "results", "text-lf-v1"),
        _artifact(output_dir, "calls.jsonl", "call_log", "text-lf-v1"),
    ]
    manifest = {
        "schema_version": "poca-verify-1.0",
        "campaign_id": "scipy-smoke-20261119",
        "artifacts": artifacts,
        "results": {
            "files": [{"path": "results.csv"}],
            "columns": {
                "campaign_id_column": "campaign_id", "run_id_column": "run_id",
                "result_row_id_column": "result_row_id", "source_id_column": "source_id",
                "source_sha256_column": "source_sha256", "runner_id_column": "runner_id",
                "task_id_column": "task_id", "dimension_column": "dimension",
                "seed_column": "seed", "logging_mode_column": "logging_mode",
                "run_status_column": "run_status", "target_fe_column": "target_fe",
                "reported_fe_column": "reported_fe", "solver_nfev_column": "solver_nfev",
                "solver_nfev_required": True,
            },
        },
        "call_log_path": "calls.jsonl",
        "engine": {
            "name": "scipy.optimize.differential_evolution",
            "version": scipy.__version__, "python": platform.python_version(),
            "platform": platform.platform(),
        },
        "runs": [{
            "run_id": "scipy-smoke-logged", "result_row_id": "scipy-row-logged",
            "results_path": "results.csv", "source_id": "sphere-objective-spec-v1",
            "source_path": "objective_spec.json", "runner_id": "poca-scipy-smoke-v1",
            "budget_policy": "upper_bound",
            "requested_checks": {"path": True, "replay": False, "observer": False},
        }],
    }
    _write_json(output_dir / "manifest.json", manifest)
    _write_json(output_dir / "baseline_comparison.json", comparisons)
    report, audit_records = verify_manifest(output_dir / "manifest.json")
    _write_json(output_dir / "verify_report.json", report)
    _write_json(output_dir / "audit_records.json", audit_records)

    local = report["runs"][0]["statuses"]
    if not (local["identity"] == "PASS" and local["budget"] == "PASS"
            and local["runnability"] == "PASS" and local["path"] == "INDETERMINATE"):
        raise RuntimeError("verifier did not produce the preregistered local statuses")
    return {
        "output_dir": str(output_dir), "scipy_version": scipy.__version__,
        "nfev": int(traced.nfev), "wrapper_calls": traced_calls,
        "observer_comparison_pass": comparisons["observer_comparison_pass"],
        "verify_status": report["status"], "local_statuses": local,
        "effective_L3": report["runs"][0]["derived"]["effective_claim_status"]["L3"],
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", required=True, type=Path)
    args = parser.parse_args(argv)
    try:
        print(json.dumps(run(args.output_dir), indent=2, sort_keys=True))
    except (OSError, ValueError, RuntimeError) as error:
        print("SCIPY_SMOKE_ERROR: " + str(error), file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
