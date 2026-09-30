#!/usr/bin/env python3
"""POCA v3 DAG evaluator for prerequisite-ordered claim admissibility."""

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
DEFAULT_GRAPH = {
    "nodes": {
        "L0": "execution_feasibility", "L1": "result_provenance",
        "L2": "evaluator_boundary_budget_identity",
        "L3": "evaluated_candidate_lineage", "L4": "control_comparability",
        "L5": "incremental_value", "VO": "observer_non_interference",
        "VR": "replay_validity",
    },
    "edges": [["L0", "L1"], ["L0", "L2"], ["VO", "L2"],
              ["L0", "L3"], ["VO", "L3"],
              ["L0", "L4"], ["L1", "L4"], ["L2", "L4"], ["L3", "L4"],
              ["L4", "L5"]],
}
FIELD_TO_NODE = {"runnability": "L0", "identity": "L1", "budget": "L2",
                 "path": "L3", "control": "L4", "incremental_value": "L5",
                 "observer": "VO", "replay": "VR"}
NODE_ORDER = ["L0", "L1", "L2", "L3", "L4", "L5"]


def _graph(record):
    graph = record.get("graph", DEFAULT_GRAPH)
    if not isinstance(graph, dict) or not isinstance(graph.get("nodes"), dict):
        raise ValueError("graph.nodes must be an object")
    edges = graph.get("edges", [])
    nodes = set(graph["nodes"])
    if any(not isinstance(edge, list) or len(edge) != 2 or
           edge[0] not in nodes or edge[1] not in nodes for edge in edges):
        raise ValueError("graph.edges must contain valid [predecessor, successor] pairs")
    indegree = {node: 0 for node in nodes}
    children = {node: [] for node in nodes}
    for parent, child in edges:
        indegree[child] += 1
        children[parent].append(child)
    queue = [node for node, degree in indegree.items() if degree == 0]
    visited = []
    while queue:
        node = queue.pop(0)
        visited.append(node)
        for child in children[node]:
            indegree[child] -= 1
            if indegree[child] == 0:
                queue.append(child)
    if len(visited) != len(nodes):
        raise ValueError("graph must be acyclic")
    return {"nodes": dict(graph["nodes"]), "edges": [list(edge) for edge in edges]}


def _ancestors(node, parents):
    found = set()
    stack = list(parents.get(node, ()))
    while stack:
        current = stack.pop()
        if current in found:
            continue
        found.add(current)
        stack.extend(parents.get(current, ()))
    return found


def _derive_effective(local, graph=None):
    """Evaluate every node by topological traversal without overwriting local evidence."""
    graph = graph or DEFAULT_GRAPH
    nodes, edges = graph["nodes"], graph["edges"]
    parents = {node: [] for node in nodes}
    children = {node: [] for node in nodes}
    for parent, child in edges:
        parents[child].append(parent)
        children[parent].append(child)
    indegree = {node: len(parents[node]) for node in nodes}
    queue = [node for node in nodes if indegree[node] == 0]
    effective = {}
    while queue:
        node = queue.pop(0)
        local_value = local.get(node)
        prerequisites = [effective[parent] for parent in parents[node]]
        effective[node] = (local_value if all(value == "PASS" for value in prerequisites)
                           else BLOCKED)
        for child in children[node]:
            indegree[child] -= 1
            if indegree[child] == 0:
                queue.append(child)
    return effective


def _minimal_blockers(target, local, graph):
    parents = {node: [] for node in graph["nodes"]}
    children = {node: [] for node in graph["nodes"]}
    for parent, child in graph["edges"]:
        parents[child].append(parent)
        children[parent].append(child)
    bad = {node for node in _ancestors(target, parents)
           if local.get(node) in LOCAL_STATUS - {"PASS"}}
    def descendants(node):
        found, stack = set(), list(children.get(node, ()))
        while stack:
            current = stack.pop()
            if current in found:
                continue
            found.add(current)
            stack.extend(children.get(current, ()))
        return found
    return sorted(node for node in bad if not (bad & descendants(node)))


def _frontier(effective, graph):
    # L0 is the feasibility root; VO and VR are auxiliary validity records.
    # All other graph nodes are claim nodes, including schema-compatible custom IDs.
    substantive = [node for node in graph["nodes"] if node not in {"L0", "VO", "VR"}]
    admissible = {node for node in substantive if effective.get(node) == "PASS"}
    children = {node: [] for node in graph["nodes"]}
    for parent, child in graph["edges"]:
        children[parent].append(child)
    return sorted(node for node in admissible if not any(child in admissible for child in children[node]))


def _blocking_monotone(local, graph, effective):
    """Downstream PASS observations cannot promote claims behind a failed ancestor."""
    parents = {node: [] for node in graph["nodes"]}
    children = {node: [] for node in graph["nodes"]}
    for parent, child in graph["edges"]:
        parents[child].append(parent)
        children[parent].append(child)
    for failed in (node for node in graph["nodes"] if local.get(node) != "PASS"):
        changed = dict(local)
        stack = list(children[failed])
        while stack:
            node = stack.pop()
            changed[node] = "PASS"
            stack.extend(children[node])
        revised = _derive_effective(changed, graph)
        for node in _ancestors(failed, parents):
            if effective.get(node) == BLOCKED and revised.get(node) == "PASS":
                return False
        descendants = set()
        stack = list(children[failed])
        while stack:
            node = stack.pop()
            if node in descendants:
                continue
            descendants.add(node)
            stack.extend(children[node])
        for node in descendants:
            if effective.get(node) == BLOCKED and revised.get(node) == "PASS":
                return False
    return True


def evaluate(record):
    missing = sorted(REQUIRED - record.keys())
    if missing:
        raise ValueError("missing fields: " + ", ".join(missing))
    graph = _graph(record)
    local = {node: record[field] for field, node in FIELD_TO_NODE.items()}
    if isinstance(record.get("local_status"), dict):
        local.update(record["local_status"])
    missing_local = sorted(node for node in graph["nodes"] if node not in local)
    if missing_local:
        raise ValueError("missing local statuses for graph nodes: " + ", ".join(missing_local))
    invalid = {node: value for node, value in local.items()
               if node in graph["nodes"] and value not in LOCAL_STATUS}
    if invalid:
        raise ValueError("invalid local statuses: " + json.dumps(invalid, sort_keys=True))
    for field in ("target_fe", "true_fe", "reported_fe"):
        if record[field] < 0:
            raise ValueError(f"{field} must be non-negative")
    effective = _derive_effective(local, graph)
    frontier = _frontier(effective, graph)
    blockers = {node: _minimal_blockers(node, local, graph)
                for node in graph["nodes"] if effective.get(node) == BLOCKED}
    downstream = dict(local)
    protocol_properties = {
        "evidence_conservation": all(node in local for node in graph["nodes"]),
        "idempotence": _derive_effective(dict(local), graph) == effective,
        "blocking_monotonicity": _blocking_monotone(local, graph, effective),
        "versioned_repair_record": {
            "required": True,
            "case_id_versioned": bool(record.get("case_id_version")),
        },
    }
    canonical = all(node in graph["nodes"]
                    for node in ("L0", "L1", "L2", "L3", "L4", "L5"))
    return {
        "case_id": record["case_id"], "graph": graph,
        "local_status": {node: local[node] for node in graph["nodes"] if node in local},
        "effective_claim_status": effective,
        "claim_frontier": frontier,
        # These summaries have canonical POCA meanings only. A custom graph
        # still returns node-level statuses/frontier/blockers, but does not
        # silently inherit L0-L5 semantics.
        "execution_claim_admissible": (all(effective.get(node) == "PASS"
                                            for node in ("L0", "L1", "L2", "L3"))
                                        if canonical else None),
        "control_claim_admissible": (all(effective.get(node) == "PASS"
                                          for node in ("L0", "L1", "L2", "L3", "L4"))
                                      if canonical else None),
        "incremental_value_claim_admissible": (all(effective.get(node) == "PASS"
                                                    for node in ("L0", "L1", "L2", "L3", "L4", "L5"))
                                                if canonical else None),
        "minimal_blockers": blockers,
        "blocked_by": [{"condition": node, "status": local[node]}
                       for node in graph["nodes"] if local[node] != "PASS"],
        "blocked_promotion_cases": [node for node in graph["nodes"]
                                           if local.get(node) == "PASS" and effective.get(node) == BLOCKED],
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
