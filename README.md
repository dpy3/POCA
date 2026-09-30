# POCA — Prerequisite-Ordered Claim-Admissibility Protocol

POCA is a claim-admissibility protocol for assessing adaptive optimizers.
It separates **local diagnostic evidence** (what was observed at one layer)
from **effective scientific claims** (what may be stated after all
prerequisite layers are applied). Given an immutable local-status vector over
runnability, algorithm/evaluator identity, function-evaluation budget,
evaluated execution path, observer/replay validity, control adequacy, and
incremental value, POCA v3 evaluates a configurable directed acyclic claim
graph. It derives effective statuses by topological traversal, preserves all
local evidence, reports every maximal admissible claim (including
incomparable branches), and identifies minimal upstream blockers. The
canonical nodes are execution feasibility (L0), result provenance (L1),
evaluator-boundary budget identity (L2), evaluated-candidate lineage (L3),
control comparability (L4), incremental value (L5), observer non-interference
(VO), and replay validity (VR).
The non-compensation rule preserves downstream local diagnostics while
blocking a dependent claim when one of that claim's transitive prerequisites fails.
Independent branches are evaluated separately.

Companion manuscript: *An Executable Claim-Dependency Audit Protocol for
Differential Evolution: Four Case Families and Five Evidence Objects*
(submitted to Applied Soft Computing, 2026).

This repository contains the executable protocol, its tests, the contract-level
regression entry points, and the frozen figure-source records used by the manuscript.
It does **not** contain optimizer implementations under audit: the later
FSDC implementation is hosted at https://github.com/dpy3/FSDC-.git, and
third-party archives are documented (origin + SHA-256, not redistributed) in
`THIRD_PARTY_ORIGINS.md`.

## Repository layout

- `spec/poca_v3.json` — the single normative node/edge specification.
- `extension/audit_cli_v2.py`, `extension/audit_schema_v2.json` — the
  executable POCA v3 contract. The CLI accepts the canonical DAG or a
  schema-compatible record-level custom DAG with supported field mappings and
  returns effective statuses, the claim frontier, minimal blockers, blocked
  promotion cases, and protocol invariants.
- `extension/audit_cli.py`, `extension/audit_schema_v1.json` — frozen v1
  historical compatibility interface, retained for regression. It is not the
  POCA v3 DAG evaluator and its `performance_admissible` field is not a POCA v3
  scientific conclusion.
- `extension/test_audit_cli.py`, `extension/test_audit_cli_v2.py` — unit
  tests (v1 regression plus synthetic linear, branching, converging,
  multiple-blocker, redundancy, idempotence, and evidence-conservation cases).
- `extension/run_clean_control_matrix.py`, `run_external_case_audit.py`,
  `run_external_runnability_smoke.m`, `run_lshade_positive_external_case.m`
  — Python/MATLAB runners for the clean matrix and external-case audits.
- `extension/results/` — frozen summary records (clean matrix, external
  case audit, dependency-complete L-SHADE compatibility check,
  runnability-smoke failure).
- `validation/` — preregistered fault-injection and clean-control MATLAB
  entry points with their preregistration notes and frozen results.
- `source/` — exclusive figure generators and frozen figure-source CSVs.

## Quick start

```bash
# unit tests (Python 3 standard library only)
cd extension
python -m unittest -v test_audit_cli.py test_audit_cli_v2.py

# evaluate one audit record
python audit_cli_v2.py my_record.json
```

MATLAB entry points (require MATLAB and the preregistered configurations):

```bash
matlab -batch "cd('validation'); run_fault_injection_validation"
matlab -batch "cd('validation'); run_lshade_clean_control"
```

Figures regenerate from the frozen CSV/JSON records only:

```bash
cd source
python generate_all_main_figures.py
```

## Evidence boundaries

The reported 8/8 preregistered fault detections, 0/45 clean records with an
observed execution-level alarm, and nine adapter-mediated external L-SHADE
compatibility checks are bounded to their stated
test units. They are not estimates of general error rates, field-wide
defect prevalence, or cross-platform transfer. The dependency-complete external
record covers one L-SHADE 1.0.1 implementation under a
disclosed objective adapter. POCA proposes no optimizer and makes no
superiority claim for any implementation in its development program.

Versioned repair records are represented by a version identifier when one is supplied
in a repair record. The CLI reports whether the field is present; it does not compare
records across a repository or enforce parent-object uniqueness. Those
cross-record checks remain part of the evidence-management procedure.
The legacy v1 clean-control outputs retain fields named `false_positive`,
`false_positives`, and `false_positive_rate` for backward compatibility. These
are observed clean-execution alarm fields, not estimates of classifier
specificity, accuracy, or a general false-positive rate. Processed summaries,
schemas, tests, preregistrations, and figure-source records are included here.
Raw execution logs and archived runner
configurations are retained by the authors and available on reasonable
request.

## License and third-party material

Author-owned code and documentation are released under the MIT license
(see `LICENSE`). Third-party archives retain their original licences and
source attribution; see `THIRD_PARTY_ORIGINS.md`.
