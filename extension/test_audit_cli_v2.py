import unittest

from audit_cli_v2 import BLOCKED, DEFAULT_GRAPH, _derive_effective, evaluate


def record(**updates):
    item = {key: "PASS" for key in (
        "runnability", "identity", "budget", "path", "observer",
        "replay", "control", "incremental_value")}
    item.update({"case_id": "case", "source_id": "source",
                 "source_sha256": "a" * 64, "runner_id": "runner",
                 "task_id": "sphere", "dimension": 5, "seed": 1,
                 "logging_mode": "accepted_only", "target_fe": 100,
                 "true_fe": 100, "reported_fe": 100})
    item.update(updates)
    return item


class AuditCliV3Tests(unittest.TestCase):
    def test_complete_record_admits_incremental_value(self):
        result = evaluate(record())
        self.assertEqual(result["claim_frontier"], ["L5"])
        self.assertTrue(result["incremental_value_claim_admissible"])

    def test_budget_failure_blocks_only_downstream_dependants(self):
        result = evaluate(record(budget="FAIL"))
        self.assertEqual(result["effective_claim_status"]["L2"], "FAIL")
        self.assertEqual(result["effective_claim_status"]["L3"], "PASS")
        self.assertEqual(result["effective_claim_status"]["L4"], BLOCKED)
        self.assertEqual(result["effective_claim_status"]["L1"], "PASS")
        self.assertFalse(result["execution_claim_admissible"])

    def test_identity_failure_does_not_block_independent_budget(self):
        result = evaluate(record(identity="FAIL"))
        self.assertEqual(result["effective_claim_status"]["L1"], "FAIL")
        self.assertEqual(result["effective_claim_status"]["L2"], "PASS")
        self.assertEqual(result["minimal_blockers"]["L4"], ["L1"])

    def test_observer_failure_blocks_instrumented_layers(self):
        result = evaluate(record(observer="FAIL"))
        self.assertEqual(result["effective_claim_status"]["L2"], BLOCKED)
        self.assertEqual(result["minimal_blockers"]["L3"], ["VO"])

    def test_local_evidence_is_preserved(self):
        result = evaluate(record(identity="FAIL", budget="PASS", path="FAIL"))
        self.assertEqual(result["local_status"]["L2"], "PASS")
        self.assertEqual(result["local_status"]["L3"], "FAIL")
        self.assertEqual(result["effective_claim_status"]["L2"], "PASS")
        self.assertTrue(result["protocol_properties"]["evidence_conservation"])

    def test_branching_graph_keeps_incomparable_frontier(self):
        graph = {"nodes": {"A": "a", "B": "b", "C": "c"},
                 "edges": [["A", "C"], ["B", "C"]]}
        local = {"A": "PASS", "B": "PASS", "C": "PASS"}
        effective = _derive_effective(local, graph)
        self.assertEqual(effective, local)

    def test_converging_graph_reports_multiple_minimal_blockers(self):
        graph = {"nodes": {"A": "a", "B": "b", "D": "d"},
                 "edges": [["A", "D"], ["B", "D"]]}
        item = record(graph=graph, local_status={"A": "FAIL", "B": "FAIL", "D": "PASS"})
        result = evaluate(item)
        self.assertEqual(result["effective_claim_status"]["D"], BLOCKED)
        self.assertEqual(result["minimal_blockers"]["D"], ["A", "B"])

    def test_custom_graph_frontier_uses_custom_claim_nodes(self):
        graph = {"nodes": {"A": "a", "B": "b", "D": "d"},
                 "edges": [["A", "D"], ["B", "D"]]}
        item = record(graph=graph,
                      local_status={"A": "PASS", "B": "PASS", "D": "PASS"})
        result = evaluate(item)
        self.assertEqual(result["claim_frontier"], ["D"])
        self.assertIsNone(result["execution_claim_admissible"])

    def test_custom_graph_requires_local_status_for_each_node(self):
        graph = {"nodes": {"A": "a", "D": "d"}, "edges": [["A", "D"]]}
        with self.assertRaisesRegex(ValueError, "missing local statuses"):
            evaluate(record(graph=graph, local_status={"A": "PASS"}))

    def test_redundant_blocker_is_removed(self):
        graph = {"nodes": {"A": "a", "B": "b", "D": "d"},
                 "edges": [["A", "B"], ["B", "D"], ["A", "D"]]}
        item = record(graph=graph, local_status={"A": "FAIL", "B": "FAIL", "D": "PASS"})
        self.assertEqual(evaluate(item)["minimal_blockers"]["D"], ["B"])

    def test_idempotence_and_versioned_repair_record(self):
        result = evaluate(record(case_id_version="v2"))
        self.assertTrue(result["protocol_properties"]["idempotence"])
        self.assertTrue(result["protocol_properties"]["versioned_repair_record"]["case_id_versioned"])


if __name__ == "__main__":
    unittest.main()
