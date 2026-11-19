# POCA v0.2.0 local revision candidate status

Updated: 2026-11-19  
State: v0.2.0 release candidate prepared from the locally verified implementation; public release metadata and data-record links must remain synchronized with the final manuscript.

This tree is based on the v0.1.1 release branch. The v0.1.1 tag remains unchanged as the baseline.

## Completed and checked

- The verifier specification, input schemas, and six hash vectors are present and parse; all six SHA-256 values were recalculated from normalized bytes.
- src/verify_evidence.py implements declared-artifact hash checks, result-row identifier association, campaign-wide run-ID coverage checks, wrapper-call reconciliation, and conversion to the existing POCA audit-record format. Its report preserves local and effective statuses.
- Missing parseable evidence is distinguished from observed mismatch: a missing results-file path and a results row with no run_id produce INDETERMINATE; a changed artifact hash and undeclared or duplicate campaign run IDs produce FAIL. A synchronized artifact-plus-manifest rewrite still passes declared consistency, as intended; the report states that this is not authentication or proof of execution provenance.
- The full local unit suite passed: 36 tests, including all 13 inherited evaluator tests.
- The pinned SciPy 1.16.2 smoke test passed on Python 3.13.7: logging-off/on outputs and RNG states matched; wrapper count and nfev were both 48. Local statuses were identity/budget/runnability PASS, path INDETERMINATE, and effective L3 BLOCKED_BY_UPSTREAM. This is one software-integration case, not a performance result or full candidate trace.
- The candidate-specific release manifest covers 60 files using text-lf-v1 or binary-exact-v1 hashes. The code ZIP contains 61 files including the manifest; a fresh extraction matched every manifest entry and had no unlisted files.
- The fresh extracted candidate passed all 36 unit tests and the SciPy smoke test again with 48 wrapper calls and nfev=48.
- LaTeX/main.tex was updated to describe implemented behavior, the tested SciPy boundary, and pending code/data identifiers. It compiled as a 12-page A4 PDF; rendered pages were inspected, no overfull box or unresolved citation/reference was found, and the conclusion now stays together on page 9.
- Highlights.txt has five manuscript-aligned statements, each within 85 characters.
- DATA_AVAILABILITY_REVIEW.md inventories the candidate data and records unresolved author-rights and repository decisions. Nothing was uploaded or deposited.

## Current candidate artifacts

- Verifier specification: spec/verify_v1.md and the three verifier JSON contracts in spec/.
- Implementation and tests: src/verify_evidence.py, src/test_verify_evidence.py.
- SciPy smoke adapter and protocol: src/run_scipy_smoke.py and validation/SCIPY_SMOKE_PROTOCOL_20261119.md.
- Canonical local smoke output: validation/scipy_smoke_20261119_candidate/.
- Release manifest: RELEASE_CANDIDATE_MANIFEST.txt; baseline v0.1.1 manifest preserved as BASELINE_MANIFEST_v0.1.1.txt.
- Clean-extraction verification is retained outside the package in the parent QA folder.

## Remaining gates

1. The authors must review the final code, manuscript claims, AI-assistance disclosure, author order, affiliations, funding, conflict statement, and CRediT roles.
2. Complete DATA_AVAILABILITY_REVIEW.md: confirm rights for each file, check whether additional raw logs/configurations exist, select a reuse licence and repository, and deposit shareable data or give a concrete reason for each non-shared dataset. Do not upload externally before author permission.
3. Replace C1-C3 with exact public v0.2.0 code and data/archive identifiers after those releases exist. The public v0.1.1 reference identifies only the baseline.
4. After publication, keep the GitHub release tag, manifest, README, software citation, and manuscript C1-C3 synchronized. Data records should be linked using the persistent identifier selected by the authors.

## Claim boundary

The verifier checks consistency among declared files, row identifiers, and calls visible at the objective wrapper. It does not authenticate the manifest, show that a declared source generated a result, prevent unlogged calls, verify optimizer correctness, or reconstruct candidate acceptance. For the tested SciPy interface, candidate path remains INDETERMINATE.
