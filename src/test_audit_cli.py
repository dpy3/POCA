import json
import tempfile
import unittest
from pathlib import Path

from audit_cli import evaluate


class AuditCliTests(unittest.TestCase):
    def test_clean_record_passes(self):
        record = {key: "PASS" for key in ("identity", "budget", "path", "observer", "replay", "runnability")}
        record.update({"case_id": "clean", "source_id": "x", "source_sha256": "a" * 64,
                       "runner_id": "r", "task_id": "sphere", "dimension": 5,
                       "seed": 1, "logging_mode": "off", "target_fe": 10,
                       "true_fe": 10, "reported_fe": 10, "decision": "PASS"})
        result = evaluate(record)
        self.assertTrue(result["performance_admissible"])

    def test_failed_layer_blocks_performance(self):
        record = {key: "PASS" for key in ("identity", "budget", "path", "observer", "replay", "runnability")}
        record["budget"] = "FAIL"
        record.update({"case_id": "bad", "source_id": "x", "source_sha256": "a" * 64,
                       "runner_id": "r", "task_id": "sphere", "dimension": 5,
                       "seed": 1, "logging_mode": "off", "target_fe": 10,
                       "true_fe": 11, "reported_fe": 10, "decision": "FAIL"})
        self.assertFalse(evaluate(record)["performance_admissible"])


if __name__ == "__main__":
    unittest.main()
