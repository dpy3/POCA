# POCA — Prerequisite-Ordered Claim-Admissibility Protocol

POCA is a claim-admissibility protocol for assessing adaptive optimizers.
It separates **local diagnostic evidence** (what was observed at one layer)
from **effective scientific claims** (what may be stated after all
prerequisite layers are applied). Given an immutable local-status vector over
runnability, algorithm/evaluator identity, function-evaluation budget,
evaluated execution path, observer/replay validity, control adequacy, and
incremental value, POCA deterministically derives an effective claim status
per layer, the highest admissible layer, and the blocking predecessor.
The non-compensation rule preserves downstream local diagnostics while
blocking higher-level claims when an earlier prerequisite fails.

Companion manuscript: *A Prerequisite-Ordered Claim-Admissibility Protocol
for Adaptive Differential Evolution: Execution-Path Evidence in Four
Versioned Cases* (submitted to Applied Soft Computing, 2026).

This repository contains the executable protocol, its tests, the validation
entry points, and the frozen figure-source records used by the manuscript.
It does **not** contain optimizer implementations under audit: the later
FSDC implementation is hosted at https://github.com/dpy3/FSDC-.git, and
third-party archives are documented (origin + SHA-256, not redistributed) in
`THIRD_PARTY_ORIGINS.md`.

## Repository layout

- `extension/audit_cli_v2.py`, `extension/audit_schema_v2.json` — the
  executable v2 contract: local-to-effective claim transformation with
  blocking predecessor and protocol invariants (evidence conservation,
  idempotence, blocking monotonicity, repair isolation).
- `extension/audit_cli.py`, `extension/audit_schema_v1.json` — frozen v1
  historical interface, retained for regression.
- `extension/test_audit_cli.py`, `extension/test_audit_cli_v2.py` — unit
  tests (6 v2 + 2 v1 regression).
- `extension/run_clean_control_matrix.py`, `run_external_case_audit.py`,
  `run_external_runnability_smoke.m`, `run_lshade_positive_external_case.m`
  — Python/MATLAB runners for the clean matrix and external-case audits.
- `extension/results/` — frozen summary records (clean matrix, external
  case audit, positive external L-SHADE audit, runnability-smoke failure).
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

The reported 8/8 preregistered fault detections, 0/45 clean-record false
alarms, and 9/9 external L-SHADE replay audits are bounded to their stated
test units. They are not estimates of general error rates, field-wide
defect prevalence, or cross-platform transfer. The positive external record
covers one dependency-complete L-SHADE 1.0.1 implementation under a
disclosed objective adapter. POCA proposes no optimizer and makes no
superiority claim for any implementation in its development program.

## License and third-party material

Author-owned code and documentation are released under the MIT license
(see `LICENSE`). Third-party archives retain their original licences and
source attribution; see `THIRD_PARTY_ORIGINS.md`.
