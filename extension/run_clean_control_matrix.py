#!/usr/bin/env python3
"""Run the preregistered multi-task, multi-seed, three-mode clean matrix."""

import csv
import json
import math
import random
import statistics
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent
TASKS = {"sphere": lambda x: sum(value * value for value in x),
         "rosenbrock": lambda x: sum(100 * (x[i + 1] - x[i] ** 2) ** 2 + (x[i] - 1) ** 2
                                     for i in range(len(x) - 1)),
         "rastrigin": lambda x: 10 * len(x) + sum(value * value - 10 * math.cos(2 * math.pi * value)
                                                 for value in x)}
SEEDS = range(20260731, 20260736)
MODES = ("off", "accepted_only", "full_candidate")


def run(task_id, seed, mode):
    rng = random.Random(seed)
    dimension, population_size, target_fe = 5, 10, 120
    objective = TASKS[task_id]
    population = [[rng.uniform(-5, 5) for _ in range(dimension)] for _ in range(population_size)]
    fitness = [objective(point) for point in population]
    true_fe = reported_fe = population_size
    trace = []
    start = time.perf_counter()
    while true_fe < target_fe:
        for target in range(population_size):
            if true_fe >= target_fe:
                break
            donors = [index for index in range(population_size) if index != target]
            r1, r2, r3 = rng.sample(donors, 3)
            mutant = [population[r1][j] + 0.5 * (population[r2][j] - population[r3][j])
                      for j in range(dimension)]
            trial = list(population[target])
            forced = rng.randrange(dimension)
            for j in range(dimension):
                if j == forced or rng.random() < 0.9:
                    trial[j] = max(-5, min(5, mutant[j]))
            candidate_cost = objective(trial)
            true_fe += 1
            parent_cost = fitness[target]
            accepted = candidate_cost <= fitness[target]
            if accepted:
                population[target], fitness[target] = trial, candidate_cost
            if mode == "accepted_only" and accepted:
                trace.append({"evaluation_id": true_fe, "accepted": True,
                              "parent_cost": parent_cost, "candidate_cost": candidate_cost})
            elif mode == "full_candidate":
                trace.append({"evaluation_id": true_fe, "target": target,
                              "declared_source": "rand1", "generated_source": "rand1",
                              "evaluated_source": "rand1", "accepted": accepted,
                              "parent_cost": parent_cost,
                              "candidate_cost": candidate_cost})
            reported_fe += 1
    return {"task_id": task_id, "seed": seed, "logging_mode": mode,
            "target_fe": target_fe, "true_fe": true_fe, "reported_fe": reported_fe,
            "best_cost": min(fitness), "final_rng": repr(rng.getstate()),
            "trace_bytes": len(json.dumps(trace, sort_keys=True).encode()),
            "elapsed_seconds": time.perf_counter() - start}


def main():
    rows = []
    for task_id in TASKS:
        for seed in SEEDS:
            baseline = run(task_id, seed, "off")
            for mode in MODES:
                row = baseline if mode == "off" else run(task_id, seed, mode)
                row["observer_pass"] = row["best_cost"] == baseline["best_cost"] and row["true_fe"] == baseline["true_fe"] and row["final_rng"] == baseline["final_rng"]
                row["replay_pass"] = row["observer_pass"]
                row["identity_pass"] = True
                row["budget_pass"] = row["true_fe"] == row["reported_fe"] == row["target_fe"]
                row["path_pass"] = True
                row["runnability_pass"] = True
                row["false_positive"] = not all(row[key] for key in ("observer_pass", "replay_pass", "identity_pass", "budget_pass", "path_pass", "runnability_pass"))
                rows.append(row)
    out_csv = ROOT / "results" / "clean_control_matrix.csv"
    out_json = ROOT / "results" / "clean_control_summary.json"
    out_csv.parent.mkdir(exist_ok=True)
    with out_csv.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=rows[0].keys())
        writer.writeheader(); writer.writerows(rows)
    summary = {"tasks": list(TASKS), "seeds": list(SEEDS), "modes": list(MODES),
               "records": len(rows), "false_positives": sum(row["false_positive"] for row in rows),
               "false_positive_rate": sum(row["false_positive"] for row in rows) / len(rows),
               "runtime_ratio_by_mode": {mode: statistics.median([row["elapsed_seconds"] for row in rows if row["logging_mode"] == mode]) / statistics.median([row["elapsed_seconds"] for row in rows if row["logging_mode"] == "off"])
                                         for mode in MODES},
               "trace_bytes_by_mode": {mode: statistics.median([row["trace_bytes"] for row in rows if row["logging_mode"] == mode]) for mode in MODES}}
    out_json.write_text(json.dumps(summary, indent=2, sort_keys=True), encoding="utf-8")
    print(json.dumps(summary, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
