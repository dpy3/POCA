#!/usr/bin/env python3
"""Check declared POCA artifact, row, and wrapper-call consistency."""

import argparse
import csv
import hashlib
import json
import re
import sys
from pathlib import Path, PurePosixPath

from audit_cli_v2 import evaluate


STATUS_VALUES = {"PASS", "FAIL", "INDETERMINATE", "NOT_TESTED"}
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
MANIFEST_VERSION = "poca-verify-1.0"
CALL_VERSION = "poca-call-1.0"
REQUIRED_COLUMNS = (
    "campaign_id_column", "run_id_column", "result_row_id_column",
    "source_id_column", "source_sha256_column", "runner_id_column",
    "task_id_column", "dimension_column", "seed_column",
    "logging_mode_column", "run_status_column", "target_fe_column",
    "reported_fe_column", "solver_nfev_required",
)


class InputError(ValueError):
    """An unparseable or unsupported input contract."""


def _combine(statuses):
    statuses = list(statuses)
    if "FAIL" in statuses:
        return "FAIL"
    if "INDETERMINATE" in statuses:
        return "INDETERMINATE"
    if "PASS" in statuses:
        return "PASS"
    return "NOT_TESTED"


def _safe_path(root, relative):
    if not isinstance(relative, str) or not relative:
        raise InputError("artifact path must be a non-empty string")
    if chr(92) in relative:
        raise InputError("artifact paths must use forward slashes")
    posix = PurePosixPath(relative)
    drive_like = bool(posix.parts and len(posix.parts[0]) >= 2 and posix.parts[0][1] == ":")
    if (posix.is_absolute() or drive_like or str(posix) != relative or
            any(part in ("", ".", "..") for part in posix.parts)):
        raise InputError("artifact path must be a normalized relative path")
    root = root.resolve()
    candidate = root.joinpath(*posix.parts)
    resolved = candidate.resolve(strict=False)
    if not resolved.is_relative_to(root):
        raise InputError("artifact path escapes the manifest directory")
    cursor = root
    for part in posix.parts:
        cursor = cursor / part
        if cursor.is_symlink():
            raise InputError("symlink artifacts are not supported")
    return candidate


def _hash_file(path, mode):
    data = path.read_bytes()
    if mode == "text-lf-v1":
        try:
            text = data.decode("utf-8", errors="strict")
        except UnicodeDecodeError as error:
            raise ValueError("text artifact is not valid UTF-8") from error
        data = text.replace("\r\n", "\n").replace("\r", "\n").encode("utf-8")
    elif mode != "binary-exact-v1":
        raise InputError("unsupported hash_mode: " + str(mode))
    return hashlib.sha256(data).hexdigest()


def _read_json(path, label):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise InputError(f"cannot read {label}: {error}") from error


def _missing_manifest_fields(manifest):
    missing = [key for key in ("schema_version", "campaign_id", "artifacts",
                               "results", "call_log_path", "engine", "runs")
               if key not in manifest]
    if missing:
        return ["manifest." + key for key in missing]
    if not isinstance(manifest.get("artifacts"), list):
        raise InputError("manifest.artifacts must be an array")
    for index, artifact in enumerate(manifest["artifacts"]):
        if not isinstance(artifact, dict):
            raise InputError(f"manifest.artifacts[{index}] must be an object")
        missing.extend("artifacts[%d].%s" % (index, key)
                       for key in ("path", "role", "hash_mode", "sha256")
                       if key not in artifact)
    results = manifest.get("results")
    if not isinstance(results, dict):
        raise InputError("manifest.results must be an object")
    if "files" not in results or "columns" not in results:
        missing.extend("results." + key for key in ("files", "columns")
                       if key not in results)
    if isinstance(results.get("columns"), dict):
        columns_missing = [key for key in REQUIRED_COLUMNS
                           if key not in results["columns"]]
        missing.extend("results.columns." + key for key in columns_missing)
    elif "columns" in results:
        raise InputError("manifest.results.columns must be an object")
    if isinstance(results.get("files"), list):
        for index, item in enumerate(results["files"]):
            if not isinstance(item, dict):
                raise InputError(f"manifest.results.files[{index}] must be an object")
            if "path" not in item:
                missing.append(f"results.files[{index}].path")
            elif not isinstance(item["path"], str) or not item["path"]:
                raise InputError(f"manifest.results.files[{index}].path must be a non-empty string")
    if not isinstance(manifest.get("engine"), dict):
        raise InputError("manifest.engine must be an object")
    missing.extend("engine." + key for key in ("name", "version", "python", "platform")
                   if key not in manifest["engine"])
    if not isinstance(manifest.get("runs"), list):
        raise InputError("manifest.runs must be an array")
    run_keys = ("run_id", "result_row_id", "results_path", "source_id",
                "source_path", "runner_id", "budget_policy", "requested_checks")
    for index, run in enumerate(manifest["runs"]):
        if not isinstance(run, dict):
            raise InputError(f"manifest.runs[{index}] must be an object")
        missing.extend("runs[%d].%s" % (index, key) for key in run_keys if key not in run)
        if isinstance(run.get("requested_checks"), dict):
            missing.extend("runs[%d].requested_checks.%s" % (index, key)
                           for key in ("path", "replay", "observer")
                           if key not in run["requested_checks"])
        elif "requested_checks" in run:
            raise InputError(f"runs[{index}].requested_checks must be an object")
    return missing


def _validate_manifest(manifest, root):
    if not isinstance(manifest, dict):
        raise InputError("manifest root must be an object")
    missing = _missing_manifest_fields(manifest)
    if missing:
        return missing
    if manifest["schema_version"] != MANIFEST_VERSION:
        raise InputError("unsupported manifest schema_version")
    if not isinstance(manifest["campaign_id"], str) or not manifest["campaign_id"]:
        raise InputError("campaign_id must be a non-empty string")
    results = manifest["results"]
    if not isinstance(results["files"], list) or not results["files"]:
        raise InputError("results.files must be a non-empty array")
    if not isinstance(results["columns"]["solver_nfev_required"], bool):
        raise InputError("solver_nfev_required must be boolean")
    solver_column = results["columns"].get("solver_nfev_column")
    if results["columns"]["solver_nfev_required"] and not solver_column:
        raise InputError("required solver_nfev column is not declared")
    if solver_column is not None and not isinstance(solver_column, str):
        raise InputError("solver_nfev_column must be a string or null")
    seen_paths = set()
    for artifact in manifest["artifacts"]:
        if not isinstance(artifact["path"], str) or not artifact["path"]:
            raise InputError("artifact path must be a non-empty string")
        if artifact["path"] in seen_paths:
            raise InputError("duplicate artifact path: " + artifact["path"])
        seen_paths.add(artifact["path"])
        _safe_path(root, artifact["path"])
        if artifact["role"] not in ("source", "runner", "configuration", "results", "call_log"):
            raise InputError("unsupported artifact role: " + str(artifact["role"]))
        if artifact["hash_mode"] not in ("text-lf-v1", "binary-exact-v1"):
            raise InputError("unsupported hash_mode: " + str(artifact["hash_mode"]))
        if not isinstance(artifact["sha256"], str) or not SHA256_RE.fullmatch(artifact["sha256"]):
            raise InputError("invalid SHA-256 digest for " + artifact["path"])
    for result_file in results["files"]:
        _safe_path(root, result_file["path"])
    _safe_path(root, manifest["call_log_path"])
    for index, run in enumerate(manifest["runs"]):
        for key in ("run_id", "result_row_id", "results_path", "source_id", "source_path", "runner_id"):
            if not isinstance(run[key], str) or not run[key]:
                raise InputError(f"runs[{index}].{key} must be a non-empty string")
        if run["budget_policy"] not in ("upper_bound", "exact"):
            raise InputError(f"runs[{index}].budget_policy must be upper_bound or exact")
        if any(not isinstance(value, bool) for value in run["requested_checks"].values()):
            raise InputError(f"runs[{index}].requested_checks values must be boolean")
        _safe_path(root, run["results_path"])
        _safe_path(root, run["source_path"])
    return []


def _artifact_checks(manifest, root):
    checks = {}
    by_path = {}
    for item in manifest["artifacts"]:
        path = item["path"]
        full = _safe_path(root, path)
        if not full.is_file():
            check = {"path": path, "role": item["role"], "status": "INDETERMINATE",
                     "reason_code": "ARTIFACT_MISSING"}
        else:
            try:
                actual = _hash_file(full, item["hash_mode"])
            except ValueError as error:
                check = {"path": path, "role": item["role"], "status": "FAIL",
                         "reason_code": "ARTIFACT_NOT_VALID_TEXT", "detail": str(error)}
            else:
                matches = actual == item["sha256"]
                check = {"path": path, "role": item["role"],
                         "status": "PASS" if matches else "FAIL",
                         "reason_code": "HASH_MATCH" if matches else "HASH_MISMATCH",
                         "expected_sha256": item["sha256"], "observed_sha256": actual,
                         "hash_mode": item["hash_mode"]}
        checks[path] = check
        by_path[path] = item
    return checks, by_path


def _read_csv(path):
    try:
        with path.open("r", encoding="utf-8-sig", newline="") as stream:
            reader = csv.DictReader(stream)
            headers = reader.fieldnames
            if not headers or len(headers) != len(set(headers)) or None in headers:
                raise InputError("CSV has missing or duplicate column names")
            rows = list(reader)
            if any(None in row for row in rows):
                raise InputError("CSV row has more fields than its header")
            return headers, rows
    except (OSError, UnicodeError, csv.Error) as error:
        raise InputError(f"cannot parse results CSV {path}: {error}") from error


def _read_call_log(path, campaign_id):
    if not path.is_file():
        return [], "INDETERMINATE", ["CALL_LOG_MISSING"]
    records = []
    reasons = []
    status = "PASS"
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeError) as error:
        return [], "FAIL", ["CALL_LOG_UNREADABLE", str(error)]
    for line_number, line in enumerate(text.splitlines(), 1):
        if not line.strip():
            status = "FAIL"
            reasons.append(f"CALL_LOG_BLANK_LINE_{line_number}")
            continue
        try:
            item = json.loads(line)
        except json.JSONDecodeError:
            status = "FAIL"
            reasons.append(f"CALL_LOG_INVALID_JSON_{line_number}")
            continue
        if not isinstance(item, dict):
            status = "FAIL"
            reasons.append(f"CALL_LOG_RECORD_NOT_OBJECT_{line_number}")
            continue
        if item.get("campaign_id") != campaign_id:
            continue
        required = ("schema_version", "run_id", "call_index", "caller")
        if any(key not in item for key in required) or item.get("schema_version") != CALL_VERSION:
            status = "FAIL"
            reasons.append(f"CALL_LOG_SCHEMA_MISMATCH_{line_number}")
            continue
        if not isinstance(item["run_id"], str) or not item["run_id"]:
            status = "FAIL"
            reasons.append(f"CALL_LOG_RUN_ID_INVALID_{line_number}")
            continue
        if not isinstance(item["call_index"], int) or isinstance(item["call_index"], bool) or item["call_index"] < 1:
            status = "FAIL"
            reasons.append(f"CALL_INDEX_INVALID_{line_number}")
            continue
        if not isinstance(item["caller"], str) or not item["caller"]:
            status = "FAIL"
            reasons.append(f"CALLER_INVALID_{line_number}")
            continue
        records.append(item)
    return records, status, reasons


def _as_nonnegative_int(value):
    if isinstance(value, bool):
        return None
    try:
        number = int(str(value).strip())
    except (TypeError, ValueError):
        return None
    if str(value).strip() not in (str(number), "+" + str(number)) or number < 0:
        return None
    return number


def _get(row, columns, key):
    column = columns.get(key + "_column")
    if not column or column not in row:
        return None
    return row[column]


def _read_results(manifest, root, artifact_checks):
    columns = manifest["results"]["columns"]
    file_data = {}
    for item in manifest["results"]["files"]:
        path = item["path"]
        artifact = artifact_checks.get(path)
        if artifact is None:
            file_data[path] = {"status": "INDETERMINATE", "reason": "RESULT_FILE_NOT_DECLARED"}
            continue
        full = _safe_path(root, path)
        if not full.is_file():
            file_data[path] = {"status": "INDETERMINATE", "reason": "RESULT_FILE_MISSING"}
            continue
        try:
            headers, rows = _read_csv(full)
        except InputError as error:
            file_data[path] = {"status": "FAIL", "reason": "RESULT_CSV_INVALID", "detail": str(error)}
            continue
        needed = [value for key, value in columns.items()
                  if key.endswith("_column") and isinstance(value, str) and value]
        absent = sorted(set(needed) - set(headers))
        file_data[path] = {"status": "PASS" if not absent else "INDETERMINATE",
                           "headers": headers, "rows": rows,
                           "reason": "RESULT_COLUMNS_PRESENT" if not absent else "RESULT_COLUMNS_MISSING",
                           "missing_columns": absent}
    return file_data


def _run_calls(records, run_id):
    chosen = [item for item in records if item["run_id"] == run_id]
    indices = [item["call_index"] for item in chosen]
    duplicate = len(indices) != len(set(indices))
    unique = sorted(set(indices))
    gap = bool(unique) and unique != list(range(1, unique[-1] + 1))
    return chosen, duplicate, gap


def _make_audit_record(manifest, run, row, columns, identity, budget,
                       runnability, path_status, observer, replay, observed_calls):
    dimension = _as_nonnegative_int(_get(row, columns, "dimension"))
    target = _as_nonnegative_int(_get(row, columns, "target_fe"))
    reported = _as_nonnegative_int(_get(row, columns, "reported_fe"))
    required_values = [_get(row, columns, key) for key in
                       ("campaign_id", "run_id", "result_row_id", "source_id",
                        "source_sha256", "runner_id", "task_id", "seed", "logging_mode")]
    if any(value is None or value == "" for value in required_values):
        return None
    if dimension is None or target is None or reported is None or observed_calls is None:
        return None
    record = {
        "case_id": manifest["campaign_id"] + ":" + run["run_id"],
        "source_id": str(_get(row, columns, "source_id")),
        "source_sha256": str(_get(row, columns, "source_sha256")),
        "runner_id": str(_get(row, columns, "runner_id")),
        "task_id": str(_get(row, columns, "task_id")),
        "dimension": dimension,
        "seed": str(_get(row, columns, "seed")),
        "logging_mode": str(_get(row, columns, "logging_mode")),
        "target_fe": target,
        "true_fe": observed_calls,
        "reported_fe": reported,
        "runnability": runnability,
        "identity": identity,
        "budget": budget,
        "path": path_status,
        "observer": observer,
        "replay": replay,
        "control": "NOT_TESTED",
        "incremental_value": "NOT_TESTED",
    }
    if any(record[key] not in STATUS_VALUES for key in
           ("runnability", "identity", "budget", "path", "observer", "replay", "control", "incremental_value")):
        raise InputError("internal status mapping produced an invalid status")
    return record


def verify_manifest(manifest_path):
    manifest_path = Path(manifest_path).resolve()
    manifest = _read_json(manifest_path, "manifest")
    missing = _validate_manifest(manifest, manifest_path.parent)
    if missing:
        return {"schema_version": MANIFEST_VERSION,
                "status": "INDETERMINATE",
                "reason_code": "MANIFEST_FIELDS_MISSING",
                "missing_fields": missing,
                "artifact_checks": [], "runs": []}, []
    root = manifest_path.parent
    artifact_checks, artifact_specs = _artifact_checks(manifest, root)
    results = _read_results(manifest, root, artifact_checks)
    call_path = _safe_path(root, manifest["call_log_path"])
    call_log_spec = artifact_specs.get(manifest["call_log_path"])
    if call_log_spec is None or call_log_spec.get("role") != "call_log":
        call_hash_status = "INDETERMINATE"
    else:
        call_hash_status = artifact_checks[manifest["call_log_path"]]["status"]
    call_records, call_parse_status, call_reasons = _read_call_log(call_path, manifest["campaign_id"])
    columns = manifest["results"]["columns"]
    all_rows = []
    for path, info in results.items():
        if "rows" in info:
            for row in info["rows"]:
                if row.get(columns["campaign_id_column"]) == manifest["campaign_id"]:
                    all_rows.append((path, row))
    run_id_counts = {}
    for unused_path, row in all_rows:
        value = row.get(columns["run_id_column"])
        if value:
            run_id_counts[value] = run_id_counts.get(value, 0) + 1
    reports, audit_records = [], []
    manifest_run_ids = {}
    for run in manifest["runs"]:
        manifest_run_ids[run["run_id"]] = manifest_run_ids.get(run["run_id"], 0) + 1
    declared_run_ids = set(manifest_run_ids)
    result_run_ids = [row.get(columns["run_id_column"])
                      for unused_path, row in all_rows]
    unidentified_result_rows = sum(1 for value in result_run_ids if not value)
    result_run_counts = {}
    for value in result_run_ids:
        if value:
            result_run_counts[value] = result_run_counts.get(value, 0) + 1
    undeclared_result_run_ids = sorted(
        value for value in result_run_counts if value not in declared_run_ids)
    undeclared_call_run_ids = sorted(
        {item["run_id"] for item in call_records} - declared_run_ids)
    campaign_checks = []
    if undeclared_result_run_ids:
        campaign_checks.append({
            "check": "declared_result_run_coverage", "status": "FAIL",
            "reason_codes": ["RESULT_RUN_ID_NOT_DECLARED"],
            "run_ids": undeclared_result_run_ids,
        })
    if unidentified_result_rows:
        campaign_checks.append({
            "check": "declared_result_run_coverage", "status": "INDETERMINATE",
            "reason_codes": ["RESULT_RUN_ID_MISSING"],
            "row_count": unidentified_result_rows,
        })
    if undeclared_call_run_ids:
        campaign_checks.append({
            "check": "declared_call_run_coverage", "status": "FAIL",
            "reason_codes": ["CALL_RUN_ID_NOT_DECLARED"],
            "run_ids": undeclared_call_run_ids,
        })
    duplicate_result_run_ids = sorted(
        value for value, count in result_run_counts.items() if count > 1)
    if duplicate_result_run_ids:
        campaign_checks.append({
            "check": "campaign_run_id_uniqueness", "status": "FAIL",
            "reason_codes": ["CAMPAIGN_RUN_ID_DUPLICATED"],
            "run_ids": duplicate_result_run_ids,
        })
    for run in manifest["runs"]:
        run_id = run["run_id"]
        requested = run["requested_checks"]
        reasons = []
        file_info = results.get(run["results_path"])
        row = None
        row_status = "INDETERMINATE"
        if file_info is None:
            reasons.append("RESULT_FILE_NOT_DECLARED")
        elif "rows" not in file_info or file_info["status"] != "PASS":
            reasons.append(file_info.get("reason", "RESULT_FILE_UNAVAILABLE"))
        else:
            row_id_column = columns["result_row_id_column"]
            row_matches = [item for item in file_info["rows"]
                           if item.get(row_id_column) == run["result_row_id"]]
            if len(row_matches) > 1:
                row_status = "FAIL"
                reasons.append("RESULT_ROW_ID_DUPLICATED")
            elif not row_matches:
                reasons.append("RESULT_ROW_NOT_FOUND")
            else:
                row = row_matches[0]
                row_status = "PASS"
                if manifest_run_ids[run_id] > 1 or run_id_counts.get(run_id, 0) > 1:
                    row_status = "FAIL"
                    reasons.append("CAMPAIGN_RUN_ID_DUPLICATED")
                checks = (("campaign_id", manifest["campaign_id"]),
                          ("run_id", run_id),
                          ("result_row_id", run["result_row_id"]),
                          ("source_id", run["source_id"]),
                          ("runner_id", run["runner_id"]))
                for field, expected in checks:
                    observed = _get(row, columns, field)
                    if observed is None or observed == "":
                        row_status = _combine((row_status, "INDETERMINATE"))
                        reasons.append("ROW_FIELD_MISSING_" + field.upper())
                    elif observed != expected:
                        row_status = "FAIL"
                        reasons.append("ROW_FIELD_MISMATCH_" + field.upper())
                source_spec = artifact_specs.get(run["source_path"])
                source_check = artifact_checks.get(run["source_path"])
                if source_spec is None or source_spec.get("role") != "source":
                    row_status = "INDETERMINATE" if row_status != "FAIL" else row_status
                    reasons.append("SOURCE_ARTIFACT_NOT_DECLARED")
                elif source_check and source_check.get("status") == "PASS":
                    source_digest = source_check.get("observed_sha256")
                    row_source_digest = _get(row, columns, "source_sha256")
                    if not row_source_digest:
                        row_status = _combine((row_status, "INDETERMINATE"))
                        reasons.append("ROW_SOURCE_DIGEST_MISSING")
                    elif row_source_digest.lower() != source_digest:
                        row_status = "FAIL"
                        reasons.append("ROW_SOURCE_DIGEST_MISMATCH")
                else:
                    row_status = _combine((row_status, (source_check or {}).get("status", "INDETERMINATE")))
                    reasons.append("SOURCE_ARTIFACT_NOT_VERIFIED")
        run_artifacts = [run["source_path"], run["results_path"]]
        run_artifacts.extend(item["path"] for item in manifest["artifacts"]
                             if item.get("role") in ("runner", "configuration"))
        identity_status = _combine([row_status] + [artifact_checks.get(path, {}).get("status", "INDETERMINATE")
                                                   for path in run_artifacts])
        if not any(item.get("role") == "runner" for item in manifest["artifacts"]):
            identity_status = _combine((identity_status, "INDETERMINATE"))
            reasons.append("RUNNER_ARTIFACT_NOT_DECLARED")
        if not any(item.get("role") == "configuration" for item in manifest["artifacts"]):
            identity_status = _combine((identity_status, "INDETERMINATE"))
            reasons.append("CONFIGURATION_ARTIFACT_NOT_DECLARED")
        if run["results_path"] not in artifact_specs or artifact_specs[run["results_path"]].get("role") != "results":
            identity_status = _combine((identity_status, "INDETERMINATE"))
            reasons.append("RESULTS_ARTIFACT_NOT_DECLARED")
        if manifest_run_ids[run_id] > 1:
            identity_status = "FAIL"
            reasons.append("MANIFEST_RUN_ID_DUPLICATED")

        selected_calls, duplicate_calls, call_gap = _run_calls(call_records, run_id)
        parsed_call_count = len({item["call_index"] for item in selected_calls})
        calls_complete = (call_hash_status == "PASS" and call_parse_status == "PASS"
                          and not duplicate_calls and not call_gap)
        observed_calls = parsed_call_count if calls_complete else None
        budget_reasons = []
        budget_status = "PASS"
        if call_hash_status == "FAIL" or call_parse_status == "FAIL":
            budget_status = "FAIL"
            budget_reasons.extend(call_reasons or ["CALL_LOG_HASH_MISMATCH"])
        elif call_hash_status == "INDETERMINATE" or call_parse_status == "INDETERMINATE":
            budget_status = "INDETERMINATE"
            budget_reasons.extend(call_reasons or ["CALL_LOG_UNAVAILABLE"])
        if duplicate_calls:
            budget_status = "FAIL"
            budget_reasons.append("CALL_INDEX_DUPLICATED")
        if call_gap:
            budget_status = _combine((budget_status, "INDETERMINATE"))
            budget_reasons.append("CALL_INDEX_GAP")
        if row is None:
            budget_status = _combine((budget_status, "INDETERMINATE"))
            budget_reasons.append("BUDGET_ROW_UNAVAILABLE")
        else:
            reported = _as_nonnegative_int(_get(row, columns, "reported_fe"))
            target = _as_nonnegative_int(_get(row, columns, "target_fe"))
            if reported is None or target is None:
                budget_status = _combine((budget_status, "INDETERMINATE"))
                budget_reasons.append("FE_COUNT_MISSING_OR_INVALID")
            elif budget_status == "PASS" and not call_gap and not duplicate_calls:
                if observed_calls != reported:
                    budget_status = "FAIL"
                    budget_reasons.append("REPORTED_FE_MISMATCH")
                nfev_column = columns.get("solver_nfev_column")
                nfev_value = row.get(nfev_column) if nfev_column else None
                if nfev_value not in (None, ""):
                    nfev = _as_nonnegative_int(nfev_value)
                    if nfev is None:
                        budget_status = _combine((budget_status, "INDETERMINATE"))
                        budget_reasons.append("SOLVER_NFEV_INVALID")
                    elif observed_calls != nfev:
                        budget_status = "FAIL"
                        budget_reasons.append("SOLVER_NFEV_MISMATCH")
                elif columns["solver_nfev_required"]:
                    budget_status = _combine((budget_status, "INDETERMINATE"))
                    budget_reasons.append("SOLVER_NFEV_MISSING")
                if observed_calls > target or (run["budget_policy"] == "exact" and observed_calls != target):
                    budget_status = "FAIL"
                    budget_reasons.append("BUDGET_POLICY_VIOLATED")

        run_status = _get(row, columns, "run_status") if row is not None else None
        if run_status == "completed":
            runnability = "PASS"
        elif run_status == "failed":
            runnability = "FAIL"
        else:
            runnability = "INDETERMINATE"
        path_status = "INDETERMINATE" if requested["path"] else "NOT_TESTED"
        observer_status = "INDETERMINATE" if requested["observer"] else "NOT_TESTED"
        replay_status = "INDETERMINATE" if requested["replay"] else "NOT_TESTED"
        audit_record = None
        derived = None
        if row is not None:
            audit_record = _make_audit_record(manifest, run, row, columns,
                                              identity_status, budget_status,
                                              runnability, path_status,
                                              observer_status, replay_status,
                                              observed_calls)
            if audit_record is not None:
                derived = evaluate(audit_record)
                audit_records.append(audit_record)
        reports.append({
            "campaign_id": manifest["campaign_id"], "run_id": run_id,
            "result_row_id": run["result_row_id"],
            "statuses": {"identity": identity_status, "budget": budget_status,
                         "runnability": runnability, "path": path_status,
                         "observer": observer_status, "replay": replay_status,
                         "control": "NOT_TESTED", "incremental_value": "NOT_TESTED"},
            "row_status": row_status, "parsed_call_record_count": parsed_call_count,
            "observed_wrapper_calls": observed_calls,
            "reasons": sorted(set(reasons + budget_reasons)),
            "audit_record": audit_record, "derived": derived,
        })
    all_statuses = [status for item in reports for status in item["statuses"].values()]
    all_statuses.extend(item["status"] for item in campaign_checks)
    overall = _combine(all_statuses) if all_statuses else "INDETERMINATE"
    report = {"schema_version": MANIFEST_VERSION, "campaign_id": manifest["campaign_id"],
              "engine": manifest["engine"],
              "status": overall, "artifact_checks": list(artifact_checks.values()),
              "campaign_checks": campaign_checks, "runs": reports,
              "trust_boundary": "Manifest consistency is not authentication or proof of execution provenance."}
    return report, audit_records


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", required=True, type=Path)
    parser.add_argument("--report", required=True, type=Path)
    parser.add_argument("--audit-records", type=Path,
                        help="optional JSON array of v3-compatible local audit records")
    args = parser.parse_args(argv)
    try:
        report, records = verify_manifest(args.manifest)
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        if args.audit_records:
            args.audit_records.parent.mkdir(parents=True, exist_ok=True)
            args.audit_records.write_text(json.dumps(records, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    except (OSError, InputError, ValueError) as error:
        print(f"AUDIT_SCHEMA_ERROR: {error}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
