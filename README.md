# POCA: claim-dependency audit software

POCA is a Python command-line program for interpreting structured audit records from optimization experiments. It keeps each supplied local check visible, applies a user-declared acyclic dependency graph, and reports effective claim statuses, an admissible-claim frontier, and upstream blockers.

POCA does not run an optimizer, collect execution traces, enforce function-evaluation budgets, or establish that an adapter or dependency graph is correct. Its output depends on the supplied record and declared graph. The accompanying manuscript evaluates bounded differential-evolution cases and does not claim general detection accuracy, cross-domain transfer, causal attribution, or optimizer superiority.

## Release status

This source tree is the POCA v0.1.0 release prepared for the accompanying SoftwareX manuscript. It is based on public dpy3/POCA main commit 138aa27 (30 September 2026); the previously listed f3dbf12 base could not be verified in public history and is not claimed. The release includes a local evaluator and regression-test change plus a manuscript-aligned package layout, as detailed in RELEASE_CANDIDATE_MANIFEST.txt. The exact source snapshot is identified by Git tag v0.1.0. No DOI-backed reproducibility capsule has been deposited. The companion manuscript is a SoftwareX draft and has not been submitted.

## Requirements

- Python 3 for the command-line evaluator and unit tests; both use the standard library.
- MATLAB for the selected preregistered validation runners.

## Quick start

From the repository root, evaluate the included branching-graph example:

    python src/audit_cli_v2.py examples/branching_case.json

The example contains a failed source-provenance check alongside local passes for budget and candidate path. POCA preserves those local observations, blocks dependent control and value claims, and reports the provenance failure as an upstream blocker. This example illustrates software behavior; it is not an experimental result.

Run both retained unit-test modules with:

    python -m unittest discover -s src -p "test_audit_cli*.py" -v

Run selected MATLAB validations from the repository root with MATLAB installed:

    addpath('src'); addpath('validation');
    run_fault_injection_validation('validation');
    run_lshade_clean_control('validation');

## Repository layout

- src/ — command-line evaluator, schemas, tests, adapters, and processed case summaries.
- examples/ — runnable JSON example.
- spec/ — the documented POCA v3 node and edge specification.
- validation/ — preregistration records, validation runners, and retained output files.
- source/figures/ — the three editable SVG figure masters and PDF exports used by manuscript Figures 2-4; Figure 1 is native TikZ in the LaTeX source.
- source/figure_source_data/ — processed CSV records supporting Figures 3 and 4.
- THIRD_PARTY_ORIGINS.md — origins and checksums for external algorithm archives used as evidence objects.
- LICENSE.txt — MIT license for author-owned code and documentation in this package.

## Evidence boundaries

The retained manuscript reports eight prespecified single-contract faults, 45 repeated clean-control records, nine records from one author-corrected L-SHADE 1.0.1 implementation through one author-written adapter, and 13 unit tests. The clean-control records repeat 15 task-seed combinations under three logging modes. These counts describe the tested records only. They are not estimates of population sensitivity, specificity, false-alarm rates, or cross-platform transfer.

The L-SHADE result is compatibility evidence for one implementation and one adapter, not nine independent implementations. Third-party algorithm archives are not redistributed; consult THIRD_PARTY_ORIGINS.md and the original sources for provenance and licensing.

## License and citation

Author-owned code and documentation are distributed under the MIT License. Third-party materials retain their stated licenses.

For a publication, cite POCA v0.1.0 and identify the Git tag v0.1.0. No persistent archive DOI is available for this release; the manuscript states this limitation in its software metadata.
