#!/usr/bin/env python3
"""Audit two external source archives without loading historical result tables."""

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def sha256(path):
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def record(case_id, source_id, archive, runner_id, task_id, runnability,
           identity, budget, path, observer, replay, evidence):
    statuses = [runnability, identity, budget, path, observer, replay]
    return {"case_id": case_id, "source_id": source_id,
            "source_sha256": sha256(archive), "runner_id": runner_id,
            "task_id": task_id, "dimension": 0, "seed": 0,
            "logging_mode": "off", "target_fe": 0, "true_fe": 0,
            "reported_fe": 0, "identity": identity, "budget": budget,
            "path": path, "observer": observer, "replay": replay,
            "runnability": runnability,
            "decision": "PASS" if all(status == "PASS" for status in statuses) else "FAIL",
            "evidence": evidence}


def main():
    lshade_archive = Path(r"E:\postgraduate\first year\PPLO\_official_cec_sources\CEC2017_top\LSHADE_SPACMA_1.0.zip")
    lshade_source = ROOT / "external_sources" / "LSHADE_SPACMA_1.0" / "LSHADE_SPACMA_1.0" / "LSHADE_SPACMA.m"
    lshade_text = lshade_source.read_text(encoding="utf-8", errors="replace")
    nl_archive = Path(r"E:\postgraduate\first year\PPLO\_official_cec_sources\CEC2021_top\Codes-of-top-methods\NL-SHADE-RSP.zip")
    nl_root = ROOT / "external_sources" / "NL_SHADE_RSP" / "E-0125-code"
    nl_readme = (nl_root / "README.txt").read_text(encoding="utf-8", errors="replace")
    lshade = record(
        "external-lshade-spacma-1.0", "LSHADE-SPACMA-CEC2017", lshade_archive,
        "external-smoke-v1", "CEC2017-source-smoke", "FAIL", "PASS",
        "FAIL", "INDETERMINATE", "INDETERMINATE", "INDETERMINATE",
        {"source_file_sha256": sha256(lshade_source),
         "runnability_basis": "MATLAB failed to load cec17_func.mexw64: specified module could not be found",
         "budget_basis": [
             "vectorized feval(fhd,pop') evaluates a full population batch",
             "nfes is incremented after the batch and stops only after nfes exceeds max_nfes",
             "there is no truncation wrapper for the final batch"],
         "path_basis": "candidate-level provenance is not emitted by the upstream script"})
    nl = record(
        "external-nl-shade-rsp", "NL-SHADE-RSP-CEC2021", nl_archive,
        "static-source-audit-v1", "CEC2021-source-smoke", "FAIL", "PASS",
        "INDETERMINATE", "INDETERMINATE", "INDETERMINATE", "INDETERMINATE",
        {"runnability_basis": "README requires cec21_test_func.cpp, absent from frozen archive",
         "readme_declares_dependency": "cec21_test_func.cpp" in nl_readme,
         "dependency_present": (nl_root / "cec21_test_func.cpp").exists(),
         "performance_interpretation": "blocked until dependency-complete replay"})
    rows = [lshade, nl]
    (ROOT / "results" / "external_case_audit.json").write_text(json.dumps(rows, indent=2, sort_keys=True), encoding="utf-8")
    with (ROOT / "results" / "external_case_audit.csv").open("w", encoding="utf-8") as handle:
        handle.write("case_id,source_id,runnability,identity,budget,path,observer,replay,decision\n")
        for row in rows:
            handle.write(",".join(str(row[key]) for key in ("case_id", "source_id", "runnability", "identity", "budget", "path", "observer", "replay", "decision")) + "\n")
    print(json.dumps(rows, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
