import unittest

from audit_cli_v2 import BLOCKED, evaluate


def record(**updates):
    item = {
        key: "PASS" for key in (
            "runnability", "identity", "budget", "path", "observer",
            "replay", "control", "incremental_value"
        )
    }
    item.update({
        "case_id": "case", "source_id": "source",
        "source_sha256": "a" * 64, "runner_id": "runner",
        "task_id": "sphere", "dimension": 5, "seed": 1,
        "logging_mode": "accepted_only", "target_fe": 100,
        "true_fe": 100, "reported_fe": 100,
    })
    item.update(updates)
    return item


class AuditCliV2Tests(unittest.TestCase):
    def test_complete_record_admits_incremental_value(self):
        result = evaluate(record())
        self.assertEqual(result["highest_admissible_layer"],
                         "L5_incremental_value")
        self.assertTrue(result["incremental_value_claim_admissible"])

    def test_budget_failure_blocks_downstream_claims(self):
        result = evaluate(record(budget="FAIL", true_fe=110))
        self.assertEqual(result["effective_claim_status"]["L2_budget"],
                         "FAIL")
        self.assertEqual(result["effective_claim_status"]["L3_path"],
                         BLOCKED)
        self.assertFalse(result["execution_claim_admissible"])

    def test_indeterminate_is_preserved(self):
        result = evaluate(record(identity="INDETERMINATE"))
        self.assertEqual(result["effective_claim_status"]["L1_identity"],
                         "INDETERMINATE")
        self.assertIn({"condition": "identity",
                       "status": "INDETERMINATE"}, result["blocked_by"])

    def test_not_tested_value_keeps_execution_claim(self):
        result = evaluate(record(control="NOT_TESTED",
                                 incremental_value="NOT_TESTED"))
        self.assertTrue(result["execution_claim_admissible"])
        self.assertFalse(result["control_claim_admissible"])
        self.assertEqual(result["effective_claim_status"]["L4_control"],
                         "NOT_TESTED")

    def test_observer_failure_invalidates_instrumented_layers(self):
        result = evaluate(record(observer="FAIL"))
        self.assertEqual(result["effective_claim_status"]["L2_budget"],
                         BLOCKED)
        self.assertFalse(result["execution_claim_admissible"])

    def test_upstream_failure_preserves_local_diagnostic_evidence(self):
        result = evaluate(record(identity="FAIL", budget="PASS",
                                 path="FAIL", control="PASS",
                                 incremental_value="FAIL"))
        self.assertEqual(result["local_status"]["budget"], "PASS")
        self.assertEqual(result["effective_claim_status"]["L2_budget"],
                         BLOCKED)

    def test_poca_protocol_properties_are_reported(self):
        result = evaluate(record(identity="FAIL", path="PASS",
                                 control="PASS", incremental_value="PASS"))
        self.assertEqual(result["protocol_properties"], {
            "evidence_conservation": True,
            "idempotence": True,
            "blocking_monotonicity": True,
            "repair_isolation": "enforced_by_new_versioned_case_id",
        })

    def test_blocking_is_monotone_when_downstream_local_status_is_added(self):
        result = evaluate(record(budget="FAIL", path="PASS",
                                 control="PASS", incremental_value="PASS"))
        self.assertEqual(result["effective_claim_status"]["L3_path"], BLOCKED)
        self.assertTrue(result["protocol_properties"]["blocking_monotonicity"])


if __name__ == "__main__":
    unittest.main()
