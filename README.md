# POCA: claim-dependency audit software

POCA is a Python command-line program for interpreting structured audit records from optimization experiments. It keeps each supplied local check visible, applies a user-declared acyclic dependency graph, and reports effective claim statuses, an admissible-claim frontier, and upstream blockers.

POCA does not run or control an optimizer, expose a complete execution trace, authenticate a manifest, or establish that an adapter or dependency graph is correct. Release v0.2.2 retains the v0.2.1 verifier implementation and corrects the supplied FSDC L/T/R incremental-value label to INDETERMINATE because the accompanying case materials do not preserve a prespecified decision rule. No algorithm, verification rule, or optimizer result is changed. The verifier checks declared artifact hashes, result-row identifiers, and wrapper-call accounting. Those checks establish consistency among supplied files and exposed counters only; they do not prove that the listed source produced the result or that no calls bypassed the wrapper. The SciPy integration is a single pinned smoke test, not an optimizer-performance experiment.

## Release status

This folder contains the POCA v0.2.2 patch release based on the v0.2.1 release and the v0.1.1 baseline. The v0.2.1 and v0.2.0 tags remain available as earlier releases, and the v0.1.1 tag remains available for the earlier bounded evaluation. The companion manuscript identifies this v0.2.2 release and its associated data record. No third-party source archive is redistributed here.

## Requirements

- Python 3 for the command-line evaluator and unit tests; both use the standard library.
- MATLAB for the selected preregistered validation runners.

## Quick start

From the repository root, evaluate the included branching-graph example:

    python src/audit_cli_v2.py examples/branching_case.json

The example contains a failed source-provenance check alongside local passes for budget and candidate path. POCA preserves those local observations, blocks dependent control and value claims, and reports the provenance failure as an upstream blocker. This example illustrates software behavior; it is not an experimental result.

Run both retained unit-test modules with:

    python -m unittest discover -s src -p "test_*.py" -v

The v0.2.2 release test suite contains 36 tests, including the original POCA evaluator tests and verifier-specific tests. Run the pinned SciPy integration into a new, empty output directory with:

    python src/run_scipy_smoke.py --output-dir validation/scipy-smoke-local

The smoke test compares logging-off and logging-on executions and checks wrapper calls against SciPy's exposed `nfev`. Its expected local path status is `INDETERMINATE`; it does not observe per-candidate acceptance.

Run selected MATLAB validations from the repository root with MATLAB installed:

    addpath('src'); addpath('validation');
    run_fault_injection_validation('validation');
    run_lshade_clean_control('validation');

## Repository layout

- src/ — command-line evaluator, bounded evidence verifier, smoke adapter, and tests.
- examples/ — runnable JSON example.
- spec/ — the POCA v3 node/edge specification and v1 verifier input contracts.
- validation/ — preregistration records, validation runners, and the local SciPy smoke output.
- RELEASE_MANIFEST.txt — per-file SHA-256 list for this v0.2.2 release tree.
- BASELINE_MANIFEST_v0.1.1.txt — preserved v0.1.1 manifest from the copied baseline.
- source/figures/ — the three editable SVG figure masters and PDF exports used by manuscript Figures 2-4; Figure 1 is native TikZ in the LaTeX source.
- source/figure_source_data/ — processed CSV records supporting Figures 3 and 4.
- THIRD_PARTY_ORIGINS.md — origins and checksums for external algorithm archives used as evidence objects.
- LICENSE.txt — MIT license for author-owned code and documentation in this package.

## Evidence boundaries

The inherited v0.1.1 study reports eight prespecified single-contract faults, 45 repeated clean-control records, and nine records from one author-corrected L-SHADE 1.0.1 implementation through one author-written adapter. The clean-control records repeat 15 task-seed combinations under three logging modes. The v0.2.2 release carries 36 passing unit tests and one pinned SciPy smoke integration (48 wrapper calls matched 48 reported evaluations in the tested run). These counts describe only the tested cases; they are not estimates of population sensitivity, specificity, false-alarm rates, or cross-platform transfer.

The L-SHADE result is compatibility evidence for one implementation and one adapter, not nine independent implementations. Third-party algorithm archives are not redistributed; consult THIRD_PARTY_ORIGINS.md and the original sources for provenance and licensing.

## License and citation

Author-owned code and documentation are distributed under the MIT License. Third-party materials retain their stated licenses.

This v0.2.2 patch release supersedes v0.2.1 by correcting the supplied FSDC L/T/R incremental-value label; it retains the same verifier functionality. The v0.2.1, v0.2.0, and v0.1.1 tags remain available as earlier releases and baselines. Author-generated data bundled with this release are licensed under CC BY 4.0 as specified in DATA_LICENSE.txt; software and documentation remain under MIT. Third-party source archives are not redistributed.
