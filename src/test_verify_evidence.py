import csv
import json
import tempfile
import unittest
from pathlib import Path

import verify_evidence as verifier


class VerifyEvidenceTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        (self.root / "results").mkdir()
        (self.root / "source.bin").write_bytes(b"\x00source-v1")
        (self.root / "runner.py").write_text("def run():\n    return 1\n", encoding="utf-8")
        (self.root / "config.json").write_text('{"seed": 4}\n', encoding="utf-8")
        self.row = {
            "campaign_id": "campaign-a", "run_id": "run-1",
            "result_row_id": "row-1", "source_id": "source-a",
            "source_sha256": verifier._hash_file(self.root / "source.bin", "binary-exact-v1"),
            "runner_id": "runner-a", "task_id": "sphere", "dimension": "2",
            "seed": "4", "logging_mode": "wrapped", "run_status": "completed",
            "target_fe": "2", "reported_fe": "2", "solver_nfev": "2",
        }
        self.columns = {
            "campaign_id_column": "campaign_id", "run_id_column": "run_id",
            "result_row_id_column": "result_row_id", "source_id_column": "source_id",
            "source_sha256_column": "source_sha256", "runner_id_column": "runner_id",
            "task_id_column": "task_id", "dimension_column": "dimension",
            "seed_column": "seed", "logging_mode_column": "logging_mode",
            "run_status_column": "run_status", "target_fe_column": "target_fe",
            "reported_fe_column": "reported_fe", "solver_nfev_column": "solver_nfev",
            "solver_nfev_required": True,
        }
        self.calls = [
            {"schema_version": "poca-call-1.0", "campaign_id": "campaign-a",
             "run_id": "run-1", "call_index": 1, "caller": "objective"},
            {"schema_version": "poca-call-1.0", "campaign_id": "campaign-a",
             "run_id": "run-1", "call_index": 2, "caller": "objective"},
        ]
        self.manifest = {
            "schema_version": "poca-verify-1.0", "campaign_id": "campaign-a",
            "artifacts": [],
            "results": {"files": [{"path": "results/results.csv"}],
                         "columns": self.columns},
            "call_log_path": "calls.jsonl",
            "engine": {"name": "test-engine", "version": "1.0",
                       "python": "3.x", "platform": "test"},
            "runs": [{"run_id": "run-1", "result_row_id": "row-1",
                      "results_path": "results/results.csv", "source_id": "source-a",
                      "source_path": "source.bin", "runner_id": "runner-a",
                      "budget_policy": "upper_bound",
                      "requested_checks": {"path": True, "replay": False,
                                            "observer": False}}],
        }
        self._write_results([self.row])
        self._write_calls(self.calls)
        self._refresh_artifacts()
        self.manifest_path = self.root / "manifest.json"
        self._write_manifest()

    def tearDown(self):
        self.temp.cleanup()

    def _write_results(self, rows):
        path = self.root / "results" / "results.csv"
        with path.open("w", encoding="utf-8", newline="") as stream:
            writer = csv.DictWriter(stream, fieldnames=list(self.row.keys()))
            writer.writeheader()
            writer.writerows(rows)

    def _write_calls(self, records):
        text = "".join(json.dumps(item, sort_keys=True) + "\n" for item in records)
        (self.root / "calls.jsonl").write_text(text, encoding="utf-8")

    def _refresh_artifacts(self):
        paths = [
            ("source.bin", "source", "binary-exact-v1"),
            ("runner.py", "runner", "text-lf-v1"),
            ("config.json", "configuration", "text-lf-v1"),
            ("results/results.csv", "results", "text-lf-v1"),
            ("calls.jsonl", "call_log", "text-lf-v1"),
        ]
        self.manifest["artifacts"] = [
            {"path": path, "role": role, "hash_mode": mode,
             "sha256": verifier._hash_file(self.root / path, mode)}
            for path, role, mode in paths
        ]

    def _write_manifest(self):
        self.manifest_path.write_text(json.dumps(self.manifest, indent=2) + "\n",
                                      encoding="utf-8")

    def _verify(self):
        self._write_manifest()
        return verifier.verify_manifest(self.manifest_path)

    def test_clean_manifest_row_and_call_log_pass(self):
        report, records = self._verify()
        run = report["runs"][0]
        self.assertEqual(run["statuses"]["identity"], "PASS")
        self.assertEqual(run["statuses"]["budget"], "PASS")
        self.assertEqual(run["statuses"]["runnability"], "PASS")
        self.assertEqual(run["statuses"]["path"], "INDETERMINATE")
        self.assertEqual(run["observed_wrapper_calls"], 2)
        self.assertEqual(len(records), 1)
        self.assertEqual(run["derived"]["local_status"]["L3"], "INDETERMINATE")
        self.assertEqual(run["derived"]["effective_claim_status"]["L3"], "BLOCKED_BY_UPSTREAM")

    def test_changed_source_without_manifest_update_fails_identity(self):
        (self.root / "source.bin").write_bytes(b"\x00source-v2")
        report, unused = self._verify()
        self.assertEqual(report["runs"][0]["statuses"]["identity"], "FAIL")
        source_check = next(item for item in report["artifact_checks"]
                            if item["path"] == "source.bin")
        self.assertEqual(source_check["reason_code"], "HASH_MISMATCH")

    def test_changed_configuration_without_manifest_update_fails_identity(self):
        (self.root / "config.json").write_text('{"seed": 5}\n', encoding="utf-8")
        report, unused = self._verify()
        self.assertEqual(report["runs"][0]["statuses"]["identity"], "FAIL")

    def test_synchronized_rewrite_passes_only_declared_consistency(self):
        (self.root / "source.bin").write_bytes(b"\x00source-v2")
        self.row["source_sha256"] = verifier._hash_file(self.root / "source.bin", "binary-exact-v1")
        self._write_results([self.row])
        self._refresh_artifacts()
        report, unused = self._verify()
        self.assertEqual(report["runs"][0]["statuses"]["identity"], "PASS")
        self.assertIn("not authentication", report["trust_boundary"])

    def test_text_line_endings_normalize_but_binary_is_exact(self):
        left = self.root / "lf.txt"
        right = self.root / "crlf.txt"
        left.write_bytes(b"alpha\nbeta\n")
        right.write_bytes(b"alpha\r\nbeta\r\n")
        self.assertEqual(verifier._hash_file(left, "text-lf-v1"),
                         verifier._hash_file(right, "text-lf-v1"))
        self.assertNotEqual(verifier._hash_file(left, "binary-exact-v1"),
                            verifier._hash_file(right, "binary-exact-v1"))

    def test_missing_manifest_field_is_indeterminate(self):
        self.manifest.pop("campaign_id")
        report, records = self._verify()
        self.assertEqual(report["status"], "INDETERMINATE")
        self.assertIn("manifest.campaign_id", report["missing_fields"])
        self.assertEqual(records, [])

    def test_missing_result_file_path_is_indeterminate(self):
        self.manifest["results"]["files"][0].pop("path")
        report, records = self._verify()
        self.assertEqual(report["status"], "INDETERMINATE")
        self.assertIn("results.files[0].path", report["missing_fields"])
        self.assertEqual(records, [])

    def test_missing_call_log_is_indeterminate(self):
        (self.root / "calls.jsonl").unlink()
        report, records = self._verify()
        self.assertEqual(report["runs"][0]["statuses"]["budget"], "INDETERMINATE")
        self.assertIsNone(report["runs"][0]["observed_wrapper_calls"])
        self.assertIsNone(report["runs"][0]["audit_record"])
        self.assertEqual(records, [])

    def test_hash_golden_vectors_match_implementation(self):
        vectors = json.loads((Path(__file__).parent.parent / "spec" /
                              "poca_verify_hash_vectors.json").read_text(encoding="utf-8"))
        for vector in vectors["vectors"]:
            raw = bytes.fromhex(vector["input_hex"])
            expected = bytes.fromhex(vector["normalized_hex"])
            if vector["hash_mode"] == "text-lf-v1":
                actual = raw.decode("utf-8").replace("\r\n", "\n").replace("\r", "\n").encode("utf-8")
            else:
                actual = raw
            self.assertEqual(actual, expected, vector["id"])
            import hashlib
            self.assertEqual(hashlib.sha256(actual).hexdigest(), vector["sha256"], vector["id"])

    def test_unsafe_artifact_path_is_rejected(self):
        self.manifest["artifacts"][0]["path"] = "../outside.bin"
        self.manifest["artifacts"][0]["sha256"] = "0" * 64
        with self.assertRaises(verifier.InputError):
            self._verify()

    def test_duplicate_run_id_across_result_files_fails(self):
        second = dict(self.row, result_row_id="row-2")
        second_path = self.root / "results" / "second.csv"
        with second_path.open("w", encoding="utf-8", newline="") as stream:
            writer = csv.DictWriter(stream, fieldnames=list(self.row.keys()))
            writer.writeheader()
            writer.writerow(second)
        self.manifest["results"]["files"].append({"path": "results/second.csv"})
        self.manifest["artifacts"].append({
            "path": "results/second.csv", "role": "results", "hash_mode": "text-lf-v1",
            "sha256": verifier._hash_file(second_path, "text-lf-v1")})
        report, unused = self._verify()
        self.assertEqual(report["runs"][0]["statuses"]["identity"], "FAIL")
        self.assertTrue(any(
            check["check"] == "campaign_run_id_uniqueness"
            and check["status"] == "FAIL"
            for check in report["campaign_checks"]))

    def test_unlisted_run_id_in_call_log_fails_campaign_coverage(self):
        extra = dict(self.calls[0], run_id="run-not-declared")
        self._write_calls(self.calls + [extra])
        self._refresh_artifacts()
        report, unused = self._verify()
        check = next(item for item in report["campaign_checks"]
                     if item["check"] == "declared_call_run_coverage")
        self.assertEqual(check["status"], "FAIL")
        self.assertEqual(check["run_ids"], ["run-not-declared"])
        self.assertEqual(report["status"], "FAIL")

    def test_unlisted_run_id_in_results_fails_campaign_coverage(self):
        extra = dict(self.row, run_id="run-not-declared",
                     result_row_id="row-not-declared")
        self._write_results([self.row, extra])
        self._refresh_artifacts()
        report, unused = self._verify()
        check = next(item for item in report["campaign_checks"]
                     if item["check"] == "declared_result_run_coverage")
        self.assertEqual(check["status"], "FAIL")
        self.assertEqual(check["run_ids"], ["run-not-declared"])
        self.assertEqual(report["status"], "FAIL")

    def test_missing_run_id_in_campaign_result_is_indeterminate(self):
        extra = dict(self.row, run_id="", result_row_id="row-without-run-id")
        self._write_results([self.row, extra])
        self._refresh_artifacts()
        report, unused = self._verify()
        check = next(item for item in report["campaign_checks"]
                     if item["check"] == "declared_result_run_coverage")
        self.assertEqual(check["status"], "INDETERMINATE")
        self.assertEqual(check["reason_codes"], ["RESULT_RUN_ID_MISSING"])

    def test_duplicate_result_row_id_fails(self):
        self._write_results([self.row, self.row])
        self._refresh_artifacts()
        report, unused = self._verify()
        self.assertEqual(report["runs"][0]["statuses"]["identity"], "FAIL")

    def test_call_index_gap_is_indeterminate(self):
        self._write_calls([self.calls[0], dict(self.calls[1], call_index=3)])
        self._refresh_artifacts()
        report, unused = self._verify()
        self.assertEqual(report["runs"][0]["statuses"]["budget"], "INDETERMINATE")

    def test_duplicate_call_index_fails(self):
        self._write_calls([self.calls[0], dict(self.calls[1], call_index=1)])
        self._refresh_artifacts()
        report, unused = self._verify()
        self.assertEqual(report["runs"][0]["statuses"]["budget"], "FAIL")

    def test_reported_fe_mismatch_fails(self):
        self.row["reported_fe"] = "1"
        self._write_results([self.row])
        self._refresh_artifacts()
        report, unused = self._verify()
        self.assertEqual(report["runs"][0]["statuses"]["budget"], "FAIL")

    def test_upper_bound_allows_early_stop(self):
        self.row["target_fe"] = "10"
        self._write_results([self.row])
        self._refresh_artifacts()
        report, unused = self._verify()
        self.assertEqual(report["runs"][0]["statuses"]["budget"], "PASS")

    def test_exact_budget_rejects_early_stop(self):
        self.row["target_fe"] = "10"
        self.manifest["runs"][0]["budget_policy"] = "exact"
        self._write_results([self.row])
        self._refresh_artifacts()
        report, unused = self._verify()
        self.assertEqual(report["runs"][0]["statuses"]["budget"], "FAIL")

    def test_solver_nfev_mismatch_fails(self):
        self.row["solver_nfev"] = "3"
        self._write_results([self.row])
        self._refresh_artifacts()
        report, unused = self._verify()
        self.assertEqual(report["runs"][0]["statuses"]["budget"], "FAIL")

    def test_unrequested_path_check_is_not_tested(self):
        self.manifest["runs"][0]["requested_checks"]["path"] = False
        report, unused = self._verify()
        self.assertEqual(report["runs"][0]["statuses"]["path"], "NOT_TESTED")

    def test_cli_writes_machine_readable_report_and_records(self):
        report_path = self.root / "out" / "report.json"
        record_path = self.root / "out" / "audit_records.json"
        code = verifier.main(["--manifest", str(self.manifest_path),
                              "--report", str(report_path),
                              "--audit-records", str(record_path)])
        self.assertEqual(code, 0)
        report = json.loads(report_path.read_text(encoding="utf-8"))
        records = json.loads(record_path.read_text(encoding="utf-8"))
        self.assertEqual(report["runs"][0]["statuses"]["identity"], "PASS")
        self.assertEqual(len(records), 1)


if __name__ == "__main__":
    unittest.main()
